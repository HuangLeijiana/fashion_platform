#!/usr/bin/env python3
"""云裳衣裳 — CLIP 图像检索评估脚本

对 static/images/products 下的商品图做两套检索评估：
1. 库内自检（sanity）：每张商品图作为查询，在完整商品库中检索，检查自身是否命中 top-k。
   验证 CLIP 特征与向量库管线的一致性。
2. 扰动鲁棒检索：模拟"用户实拍图 ≠ 库图"的真实差距，对每张图施加
   JPEG 压缩 / 缩放 / 高斯模糊 / 亮度偏移 / 水平翻转 5 类扰动后作为查询，
   在原始商品库中检索，检查自身是否命中 top-k（recall@k）。

运行方式：
    python eval_clip_retrieval.py
输出：
    eval/retrieval_results.json
"""

import json
import os

import numpy as np
import torch
from PIL import Image, ImageEnhance, ImageFilter

import clip

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCTS_DIR = os.path.join(BASE_DIR, "static", "images", "products")
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "retrieval_results.json")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
TOP_K = 5


def load_images() -> list[tuple[str, Image.Image]]:
    exts = (".jpg", ".jpeg", ".png", ".webp")
    paths = sorted(
        p for p in os.listdir(PRODUCTS_DIR) if p.lower().endswith(exts)
    )
    images = []
    for name in paths:
        img = Image.open(os.path.join(PRODUCTS_DIR, name)).convert("RGB")
        images.append((name, img))
    return images


def perturb(img: Image.Image, kind: str) -> Image.Image:
    """生成模拟用户实拍的扰动图。"""
    if kind == "jpeg30":  # 低质量 JPEG 压缩
        buf = __import__("io").BytesIO()
        img.save(buf, format="JPEG", quality=30)
        buf.seek(0)
        return Image.open(buf).convert("RGB")
    if kind == "jpeg20":  # 低质量 JPEG 压缩
        buf = __import__("io").BytesIO()
        img.save(buf, format="JPEG", quality=20)
        buf.seek(0)
        return Image.open(buf).convert("RGB")
    if kind == "jpeg10":  # 极低质量 JPEG 压缩
        buf = __import__("io").BytesIO()
        img.save(buf, format="JPEG", quality=10)
        buf.seek(0)
        return Image.open(buf).convert("RGB")
    if kind == "resize50":  # 分辨率减半再放大
        w, h = img.size
        return img.resize((w // 2, h // 2)).resize((w, h))
    if kind == "resize25":  # 分辨率 1/4 再放大
        w, h = img.size
        return img.resize((w // 4, h // 4)).resize((w, h))
    if kind == "blur2":  # 高斯模糊
        return img.filter(ImageFilter.GaussianBlur(radius=2))
    if kind == "blur5":  # 重度高斯模糊
        return img.filter(ImageFilter.GaussianBlur(radius=5))
    if kind == "bright70":  # 亮度 0.7
        return ImageEnhance.Brightness(img).enhance(0.7)
    if kind == "bright130":  # 亮度 1.3
        return ImageEnhance.Brightness(img).enhance(1.3)
    if kind == "flip":  # 水平翻转
        return img.transpose(Image.FLIP_LEFT_RIGHT)
    if kind == "crop70":  # 中心裁剪 70%（模拟拍摄角度/构图差异）
        w, h = img.size
        cw, ch = int(w * 0.7), int(h * 0.7)
        return img.crop(((w - cw) // 2, (h - ch) // 2,
                         (w - cw) // 2 + cw, (h - ch) // 2 + ch)).resize((w, h))
    if kind == "rot15":  # 旋转 15°（黑色填充）
        return img.rotate(15)
    if kind == "sat150":  # 饱和度 1.5（颜色偏移）
        return ImageEnhance.Color(img).enhance(1.5)
    if kind == "combo":  # 组合扰动：压缩+模糊+变暗
        img = perturb(img, "jpeg20")
        img = img.filter(ImageFilter.GaussianBlur(radius=2.5))
        return ImageEnhance.Brightness(img).enhance(0.8)
    raise ValueError(kind)


@torch.no_grad()
def embed(model: torch.nn.Module, preprocess, images: list[Image.Image]) -> np.ndarray:
    feats = []
    for img in images:
        x = preprocess(img).unsqueeze(0).to(DEVICE)
        f = model.encode_image(x)
        f = f / f.norm(dim=-1, keepdim=True)
        feats.append(f.cpu().numpy())
    return np.vstack(feats)


@torch.no_grad()
def embed_batch(model: torch.nn.Module, preprocess, images: list[Image.Image],
                batch: int = 32) -> np.ndarray:
    feats = []
    for i in range(0, len(images), batch):
        chunk = images[i:i + batch]
        x = torch.stack([preprocess(im) for im in chunk]).to(DEVICE)
        f = model.encode_image(x)
        f = f / f.norm(dim=-1, keepdim=True)
        feats.append(f.cpu().numpy())
    return np.vstack(feats)


def recall_at(sims: np.ndarray, top_k: int) -> float:
    """sims[i, :] 为查询 i 与库中所有项的相似度，查询 i 的正确答案是第 i 项。"""
    n = sims.shape[0]
    order = np.argsort(-sims, axis=1)[:, :top_k]
    hit = sum(i in order[i] for i in range(n))
    return hit / n


def main() -> None:
    print(f"device: {DEVICE}")
    print(f"loading CLIP ViT-B/32 ...")
    model, preprocess = clip.load("ViT-B/32", device=DEVICE)
    model.eval()

    items = load_images()
    names = [n for n, _ in items]
    print(f"product images: {len(items)}")

    gallery_feats = embed_batch(model, preprocess, [im for _, im in items])
    print(f"feature dim: {gallery_feats.shape[1]}")

    results = {
        "n_products": len(items),
        "feature_dim": int(gallery_feats.shape[1]),
        "model": "CLIP ViT-B/32",
        "top_k": TOP_K,
        "self_check": {},
        "perturbations": {},
    }

    # 1) 库内自检
    sims = gallery_feats @ gallery_feats.T
    for k in (1, TOP_K):
        results["self_check"][f"recall@{k}"] = round(recall_at(sims, k), 4)
    # 自检 top-1 相似度均值（对角线）
    results["self_check"]["mean_self_sim"] = round(float(np.diag(sims).mean()), 4)

    # 2) 扰动鲁棒检索
    for kind in ["jpeg30", "resize50", "blur2", "bright70", "bright130", "flip",
                 "jpeg10", "resize25", "blur5", "crop70", "rot15", "sat150", "combo"]:
        q_imgs = [perturb(im, kind) for _, im in items]
        q_feats = embed_batch(model, preprocess, q_imgs)
        q_sims = q_feats @ gallery_feats.T
        r = {f"recall@{k}": round(recall_at(q_sims, k), 4) for k in (1, TOP_K)}
        r["mean_top1_sim"] = round(
            float(q_sims.max(axis=1).mean()), 4
        )
        results["perturbations"][kind] = r
        print(f"{kind}: {r}")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nsaved -> {OUT_PATH}")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
