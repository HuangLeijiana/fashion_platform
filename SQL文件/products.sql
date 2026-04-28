/*
Navicat MySQL Data Transfer

Source Server         : myconn
Source Server Version : 50712
Source Host           : localhost:3306
Source Database       : sys

Target Server Type    : MYSQL
Target Server Version : 50712
File Encoding         : 65001

Date: 2025-11-06 18:36:07
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for products
-- ----------------------------
DROP TABLE IF EXISTS `products`;
CREATE TABLE `products` (
  `id` char(36) NOT NULL COMMENT '商品UUID',
  `name` varchar(255) NOT NULL COMMENT '商品名称',
  `description` text COMMENT '商品描述',
  `price` decimal(10,2) DEFAULT NULL COMMENT '商品价格',
  `category` varchar(100) DEFAULT NULL COMMENT '商品分类',
  `brand` varchar(100) DEFAULT NULL COMMENT '商品品牌',
  `images` json DEFAULT NULL COMMENT '商品图片URL列表',
  `attributes` json DEFAULT NULL COMMENT '商品属性（尺码、颜色等）',
  `embedding` text COMMENT '商品向量嵌入（逗号分隔字符串）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  FULLTEXT KEY `name` (`name`,`description`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品信息表';

-- ----------------------------
-- Records of products
-- ----------------------------
INSERT INTO `products` VALUES ('1', '男士休闲衬衫', '舒适棉质男士衬衫', '199.00', '上衣', '优衣库', '[\"/static/images/shirt1.jpg\"]', '{\"size\": \"L\", \"color\": \"白色\"}', null);
INSERT INTO `products` VALUES ('123', '测试商品', '这是一个测试商品', '99.99', '测试类别', '测试品牌', '[]', '{}', null);
INSERT INTO `products` VALUES ('2', '女士牛仔裤', '修身款女士牛仔裤', '299.00', '裤子', '李维斯', '[\"/static/images/jeans1.jpg\"]', '{\"size\": \"M\", \"color\": \"蓝色\"}', null);
INSERT INTO `products` VALUES ('3', '运动鞋', '轻便透气运动鞋', '399.00', '鞋类', '耐克', '[\"/static/images/shoes1.jpg\"]', '{\"size\": \"42\", \"color\": \"黑色\"}', null);
INSERT INTO `products` VALUES ('4', '冬季羽绒服', '保暖加厚羽绒服', '599.00', '外套', '波司登', '[\"/static/images/coat1.jpg\"]', '{\"size\": \"XL\", \"color\": \"黑色\"}', null);
INSERT INTO `products` VALUES ('5', '休闲背包', '多功能双肩背包', '159.00', '配饰', '小米', '[\"/static/images/bag1.jpg\"]', '{\"color\": \"灰色\", \"capacity\": \"20L\"}', null);
INSERT INTO `products` VALUES ('6ffe33f7-ae68-11f0-930e-9c2dcdd43890', '白色衬衫', '时尚Shirt，优质面料，舒适透气', '189.00', 'Shirt', '时尚品牌', '[\"/static/images/products/shirt_white_1.jpg\"]', '{\"size\": [\"XS\", \"S\", \"M\", \"L\", \"XL\"], \"color\": \"白色\", \"style\": \"casual\", \"season\": \"all\", \"material\": \"纯棉\"}', null);
INSERT INTO `products` VALUES ('6ffe5cea-ae68-11f0-930e-9c2dcdd43890', '蓝色牛仔裤', '时尚Jeans，优质面料，舒适透气', '259.00', 'Jeans', '时尚品牌', '[\"/static/images/products/jeans_blue_1.jpg\"]', '{\"size\": [\"25\", \"26\", \"27\", \"28\", \"29\"], \"color\": \"蓝色\", \"style\": \"casual\", \"season\": \"all\", \"material\": \"牛仔布\"}', null);
INSERT INTO `products` VALUES ('6ffe5dfb-ae68-11f0-930e-9c2dcdd43890', '运动鞋', '时尚Shoes，优质面料，舒适透气', '199.00', 'Shoes', '时尚品牌', '[\"/static/images/products/shoes_black_1.jpg\"]', '{\"size\": [\"38\", \"39\", \"40\", \"41\", \"42\", \"43\"], \"color\": \"黑色\", \"style\": \"sports\", \"season\": \"all\", \"material\": \"网布+橡胶\"}', null);
INSERT INTO `products` VALUES ('6ffe5e5b-ae68-11f0-930e-9c2dcdd43890', '碎花裙', '时尚Dress，优质面料，舒适透气', '299.00', 'Dress', '时尚品牌', '[\"/static/images/products/dress_silk_1.jpg\"]', '{\"size\": [\"S\", \"M\", \"L\"], \"color\": \"花色\", \"style\": \"elegant\", \"season\": \"summer\", \"material\": \"真丝\"}', null);
INSERT INTO `products` VALUES ('6ffe5ebb-ae68-11f0-930e-9c2dcdd43890', '斜挎包', '时尚Bag，优质面料，舒适透气', '159.00', 'Bag', '时尚品牌', '[\"/static/images/products/bag_leather_1.jpg\"]', '{\"color\": \"棕色\", \"style\": \"business\", \"material\": \"牛皮\", \"dimensions\": \"30x20x10cm\"}', null);
INSERT INTO `products` VALUES ('6ffe5f09-ae68-11f0-930e-9c2dcdd43890', '大衣', '时尚Coat，优质面料，舒适透气', '459.00', 'Coat', '时尚品牌', '[\"/static/images/products/coat_wool_1.jpg\"]', '{\"size\": [\"S\", \"M\", \"L\", \"XL\"], \"color\": \"驼色\", \"style\": \"classic\", \"season\": \"winter\", \"material\": \"羊毛混纺\"}', null);
INSERT INTO `products` VALUES ('6ffe5f60-ae68-11f0-930e-9c2dcdd43890', '休闲板鞋', '时尚Shoes，优质面料，舒适透气', '199.00', 'Shoes', '时尚品牌', '[\"/static/images/products/shoes_canvas_1.jpg\"]', '{\"size\": [\"36\", \"37\", \"38\", \"39\", \"40\", \"41\"], \"color\": \"白色\", \"style\": \"casual\", \"season\": \"all\", \"material\": \"帆布\"}', null);
INSERT INTO `products` VALUES ('6ffe606a-ae68-11f0-930e-9c2dcdd43890', '珍珠项链', '时尚Necklace，优质面料，舒适透气', '199.00', 'Necklace', '时尚品牌', '[\"/static/images/products/necklace_pearl_1.jpg\"]', '{\"color\": \"白色\", \"style\": \"elegant\", \"length\": \"45cm\", \"material\": \"珍珠+银\"}', null);
INSERT INTO `products` VALUES ('6ffe60c7-ae68-11f0-930e-9c2dcdd43890', '连帽卫衣', '时尚Hoodie，优质面料，舒适透气', '199.00', 'Hoodie', '时尚品牌', '[\"/static/images/products/hoodie_sports_1.jpg\"]', '{\"size\": [\"S\", \"M\", \"L\", \"XL\"], \"color\": \"灰色\", \"style\": \"sports\", \"season\": \"autumn\", \"material\": \"纯棉\"}', null);
INSERT INTO `products` VALUES ('6ffe6126-ae68-11f0-930e-9c2dcdd43890', '皮鞋', '时尚Shoes，优质面料，舒适透气', '199.00', 'Shoes', '时尚品牌', '[\"/static/images/products/shoes_leather_1.jpg\"]', '{\"size\": [\"39\", \"40\", \"41\", \"42\", \"43\"], \"color\": \"黑色\", \"style\": \"business\", \"season\": \"all\", \"material\": \"牛皮\"}', null);
INSERT INTO `products` VALUES ('6ffe6176-ae68-11f0-930e-9c2dcdd43890', '衬衫', '时尚Sweater，优质面料，舒适透气', '279.00', 'Sweater', '时尚品牌', '[\"/static/images/products/sweater_lace_1.jpg\"]', '{\"size\": [\"S\", \"M\", \"L\"], \"color\": \"米白色\", \"style\": \"feminine\", \"season\": \"winter\", \"material\": \"羊毛混纺\"}', null);
INSERT INTO `products` VALUES ('6ffe61cf-ae68-11f0-930e-9c2dcdd43890', '运动短裤', '时尚Shorts，优质面料，舒适透气', '149.00', 'Shorts', '时尚品牌', '[\"/static/images/products/shorts_sports_1.jpg\"]', '{\"size\": [\"S\", \"M\", \"L\", \"XL\"], \"color\": \"黑色\", \"style\": \"sports\", \"season\": \"summer\", \"material\": \"聚酯纤维\"}', null);
INSERT INTO `products` VALUES ('6ffe6218-ae68-11f0-930e-9c2dcdd43890', '牛皮钱包', '时尚Wallet，优质面料，舒适透气', '199.00', 'Wallet', '时尚品牌', '[\"/static/images/products/wallet_leather_1.jpg\"]', '{\"color\": \"黑色\", \"style\": \"business\", \"material\": \"牛皮\", \"dimensions\": \"10x8cm\"}', null);
INSERT INTO `products` VALUES ('6ffe626c-ae68-11f0-930e-9c2dcdd43890', '裙子', '时尚Dress，优质面料，舒适透气', '299.00', 'Dress', '时尚品牌', '[\"/static/images/products/dress_floral_1.jpg\"]', '{\"size\": [\"S\", \"M\", \"L\"], \"color\": \"花色\", \"style\": \"romantic\", \"season\": \"spring\", \"material\": \"雪纺\"}', null);
INSERT INTO `products` VALUES ('6ffe62dc-ae68-11f0-930e-9c2dcdd43890', '运动背包', '时尚Backpack，优质面料，舒适透气', '199.00', 'Backpack', '时尚品牌', '[\"/static/images/products/backpack_sports_1.jpg\"]', '{\"color\": \"蓝色\", \"style\": \"sports\", \"capacity\": \"30L\", \"material\": \"尼龙\"}', null);
INSERT INTO `products` VALUES ('6ffe635a-ae68-11f0-930e-9c2dcdd43890', '围巾', '时尚Scarf，优质面料，舒适透气', '199.00', 'Scarf', '时尚品牌', '[\"/static/images/products/scarf_wool_1.jpg\"]', '{\"color\": \"格纹\", \"style\": \"classic\", \"length\": \"180cm\", \"material\": \"羊毛\"}', null);
INSERT INTO `products` VALUES ('6ffe63db-ae68-11f0-930e-9c2dcdd43890', '时尚男款外套', '时尚Blazer，优质面料，舒适透气', '399.00', 'Blazer', '时尚品牌', '[\"/static/images/products/blazer_wool_1.jpg\"]', '{\"size\": [\"S\", \"M\", \"L\", \"XL\"], \"color\": \"藏青色\", \"style\": \"business\", \"season\": \"all\", \"material\": \"羊毛混纺\"}', null);
INSERT INTO `products` VALUES ('6ffe642f-ae68-11f0-930e-9c2dcdd43890', '手提包', '时尚Bag，优质面料，舒适透气', '159.00', 'Bag', '时尚品牌', '[\"/static/images/products/bag_tote_1.jpg\"]', '{\"color\": \"米色\", \"style\": \"casual\", \"capacity\": \"20L\", \"material\": \"帆布\"}', null);
INSERT INTO `products` VALUES ('6ffe6472-ae68-11f0-930e-9c2dcdd43890', '休闲板鞋', '时尚Shoes，优质面料，舒适透气', '199.00', 'Shoes', '时尚品牌', '[\"/static/images/products/shoes_skate_1.jpg\"]', '{\"size\": [\"37\", \"38\", \"39\", \"40\", \"41\", \"42\"], \"color\": \"黑白格\", \"style\": \"casual\", \"season\": \"all\", \"material\": \"帆布+橡胶\"}', null);
INSERT INTO `products` VALUES ('6ffe64bd-ae68-11f0-930e-9c2dcdd43890', '珍珠耳钉', '时尚Earrings，优质面料，舒适透气', '199.00', 'Earrings', '时尚品牌', '[\"/static/images/products/earrings_pearl_1.jpg\"]', '{\"type\": \"耳钉\", \"color\": \"白色\", \"style\": \"elegant\", \"material\": \"珍珠+银\"}', null);
INSERT INTO `products` VALUES ('6ffe64ff-ae68-11f0-930e-9c2dcdd43890', '针织开衫女款', '时尚Cardigan，优质面料，舒适透气', '229.00', 'Cardigan', '时尚品牌', '[\"/static/images/products/cardigan_knit_1.jpg\"]', '{\"size\": [\"S\", \"M\", \"L\"], \"color\": \"杏色\", \"style\": \"casual\", \"season\": \"spring\", \"material\": \"棉混纺\"}', null);
INSERT INTO `products` VALUES ('6ffe6544-ae68-11f0-930e-9c2dcdd43890', '女款运动裤', '时尚Leggings，优质面料，舒适透气', '129.00', 'Leggings', '时尚品牌', '[\"/static/images/products/leggings_sports_1.jpg\"]', '{\"size\": [\"XS\", \"S\", \"M\", \"L\"], \"color\": \"黑色\", \"style\": \"sports\", \"season\": \"all\", \"material\": \"氨纶\"}', null);
INSERT INTO `products` VALUES ('6ffe659c-ae68-11f0-930e-9c2dcdd43890', '包包', '时尚Bag，优质面料，舒适透气', '159.00', 'Bag', '时尚品牌', '[\"/static/images/products/bag_brief_1.jpg\"]', '{\"color\": \"黑色\", \"style\": \"business\", \"material\": \"牛皮\", \"dimensions\": \"40x30x10cm\"}', null);
INSERT INTO `products` VALUES ('6ffe65de-ae68-11f0-930e-9c2dcdd43890', '短裙', '时尚Skirt，优质面料，舒适透气', '199.00', 'Skirt', '时尚品牌', '[\"/static/images/products/skirt_wool_1.jpg\"]', '{\"size\": [\"S\", \"M\", \"L\"], \"color\": \"灰色\", \"style\": \"elegant\", \"season\": \"winter\", \"material\": \"羊毛呢\"}', null);
INSERT INTO `products` VALUES ('6ffe6631-ae68-11f0-930e-9c2dcdd43890', '休闲板鞋', '时尚Shoes，优质面料，舒适透气', '199.00', 'Shoes', '时尚品牌', '[\"/static/images/products/shoes_canvas_red_1.jpg\"]', '{\"size\": [\"35\", \"36\", \"37\", \"38\", \"39\", \"40\"], \"color\": \"红色\", \"style\": \"casual\", \"season\": \"all\", \"material\": \"帆布\"}', null);
INSERT INTO `products` VALUES ('6ffe667f-ae68-11f0-930e-9c2dcdd43890', '墨镜', '时尚Glasses，优质面料，舒适透气', '159.00', 'Glasses', '时尚品牌', '[\"/static/images/products/glasses_sun_1.jpg\"]', '{\"color\": \"黑色\", \"style\": \"fashion\", \"material\": \"金属+树脂\", \"uv_protection\": \"UV400\"}', null);
INSERT INTO `products` VALUES ('6ffe66c2-ae68-11f0-930e-9c2dcdd43890', '羽绒服', '时尚Jacket，优质面料，舒适透气', '349.00', 'Jacket', '时尚品牌', '[\"/static/images/products/jacket_down_1.jpg\"]', '{\"size\": [\"S\", \"M\", \"L\", \"XL\"], \"color\": \"黑色\", \"style\": \"outdoor\", \"season\": \"winter\", \"material\": \"羽绒+尼龙\"}', null);
INSERT INTO `products` VALUES ('6ffe670d-ae68-11f0-930e-9c2dcdd43890', '腰带', '时尚Belt，优质面料，舒适透气', '89.00', 'Belt', '时尚品牌', '[\"/static/images/products/belt_leather_1.jpg\"]', '{\"color\": \"棕色\", \"style\": \"business\", \"length\": \"105-115cm\", \"material\": \"牛皮\"}', null);
INSERT INTO `products` VALUES ('6ffe674f-ae68-11f0-930e-9c2dcdd43890', '运动鞋', '时尚Shoes，优质面料，舒适透气', '199.00', 'Shoes', '时尚品牌', '[\"/static/images/products/shoes_running_1.jpg\"]', '{\"size\": [\"39\", \"40\", \"41\", \"42\", \"43\", \"44\"], \"color\": \"蓝色\", \"style\": \"running\", \"season\": \"all\", \"material\": \"网布+EVA\"}', null);
INSERT INTO `products` VALUES ('6ffe6798-ae68-11f0-930e-9c2dcdd43890', '女款斜挎包', '时尚Bag，优质面料，舒适透气', '159.00', 'Bag', '时尚品牌', '[\"/static/images/products/bag_chain_1.jpg\"]', '{\"color\": \"金色\", \"style\": \"evening\", \"material\": \"牛皮+金属\", \"dimensions\": \"20x15x5cm\"}', null);
INSERT INTO `products` VALUES ('82b24d77-b94d-11f0-853a-9c2dcdd43890', 'eT 男生款外套', '时尚潮流男生外套，适合日常穿搭', '299.00', '外套', 'eT', '[\"image1.jpg\", \"image2.jpg\"]', '{\"尺码\": [\"S\", \"M\", \"L\", \"XL\"], \"材质\": \"聚酯纤维\", \"颜色\": \"黑色\"}', null);
INSERT INTO `products` VALUES ('82b2aff3-b94d-11f0-853a-9c2dcdd43890', '男生酷帅穿搭一整套', '完整男生时尚穿搭套装，包含多件单品', '599.00', '套装', '个乐grotrto', '[\"set1.jpg\", \"set2.jpg\"]', '{\"风格\": \"街头潮流\", \"包含单品\": [\"外套\", \"裤子\", \"T恤\"], \"适合场合\": \"日常出行\"}', null);
INSERT INTO `products` VALUES ('82b2b6c9-b94d-11f0-853a-9c2dcdd43890', '李宁加绒男式外套', '冬季保暖加绒外套，运动休闲风格', '459.00', '外套', '李宁', '[\"lining1.jpg\", \"lining2.jpg\"]', '{\"尺码\": [\"M\", \"L\", \"XL\", \"XXL\"], \"颜色\": \"深蓝\", \"填充物\": \"羽绒\", \"保暖等级\": \"加厚\"}', null);
INSERT INTO `products` VALUES ('82b2b77c-b94d-11f0-853a-9c2dcdd43890', '弯刀微列裤', '潮流修身裤子，微弹面料舒适耐穿', '189.00', '裤子', '未知', '[\"pants1.jpg\", \"pants2.jpg\"]', '{\"尺码\": [\"28\", \"30\", \"32\", \"34\"], \"弹力\": \"微弹\", \"裤型\": \"修身\", \"颜色\": \"深灰\"}', null);
INSERT INTO `products` VALUES ('82b2b7ec-b94d-11f0-853a-9c2dcdd43890', '源氏木语飞行夹克', '经典飞行夹克款式，复古风格', '389.00', '外套', '源氏木语', '[\"jacket1.jpg\", \"jacket2.jpg\"]', '{\"尺码\": [\"S\", \"M\", \"L\"], \"材质\": \"尼龙\", \"颜色\": \"军绿\", \"风格\": \"复古\"}', null);
INSERT INTO `products` VALUES ('82b2b84c-b94d-11f0-853a-9c2dcdd43890', 'BCE男士卫衣', '基础款男士卫衣，百搭舒适', '159.00', '上衣', 'BCE', '[\"sweater1.jpg\", \"sweater2.jpg\"]', '{\"厚度\": \"常规\", \"尺码\": [\"S\", \"M\", \"L\", \"XL\"], \"连帽\": \"是\", \"颜色\": \"灰色\"}', null);
INSERT INTO `products` VALUES ('82b2b8da-b94d-11f0-853a-9c2dcdd43890', 'MHS休闲裤', '商务休闲款式裤子，多场合适用', '239.00', '裤子', 'MHS', '[\"casual1.jpg\", \"casual2.jpg\"]', '{\"尺码\": [\"30\", \"32\", \"34\", \"36\"], \"材质\": \"棉\", \"裤型\": \"直筒\", \"颜色\": \"卡其色\"}', null);
INSERT INTO `products` VALUES ('82b2b935-b94d-11f0-853a-9c2dcdd43890', 'JE男士牛仔裤', '经典牛仔款式，耐穿耐磨', '279.00', '裤子', 'JE', '[\"jeans1.jpg\", \"jeans2.jpg\"]', '{\"尺码\": [\"30\", \"32\", \"34\", \"36\"], \"裤型\": \"修身直筒\", \"颜色\": \"深蓝\", \"水洗效果\": \"常规\"}', null);
INSERT INTO `products` VALUES ('82b2b98b-b94d-11f0-853a-9c2dcdd43890', '个乐grotrto运动套装', '运动风格整套穿搭，舒适透气', '429.00', '套装', '个乐grotrto', '[\"sport1.jpg\", \"sport2.jpg\"]', '{\"材质\": \"速干面料\", \"包含单品\": [\"运动上衣\", \"运动裤\"], \"适合运动\": [\"跑步\", \"健身\"]}', null);
INSERT INTO `products` VALUES ('82b2b9e9-b94d-11f0-853a-9c2dcdd43890', 'eT休闲衬衫', '商务休闲衬衫，多色可选', '199.00', '上衣', 'eT', '[\"shirt1.jpg\", \"shirt2.jpg\"]', '{\"尺码\": [\"S\", \"M\", \"L\", \"XL\"], \"款式\": \"常规\", \"颜色\": [\"白色\", \"蓝色\", \"浅灰\"]}', null);
INSERT INTO `products` VALUES ('82b2ba5c-b94d-11f0-853a-9c2dcdd43890', '李宁运动长裤', '运动休闲长裤，弹性面料', '189.00', '裤子', '李宁', '[\"sportpants1.jpg\", \"sportpants2.jpg\"]', '{\"尺码\": [\"M\", \"L\", \"XL\"], \"弹力\": \"高弹\", \"颜色\": \"黑色\", \"适合运动\": \"跑步健身\"}', null);
INSERT INTO `products` VALUES ('82b2babc-b94d-11f0-853a-9c2dcdd43890', '源氏木语工装裤', '潮流工装风格裤子，多口袋设计', '269.00', '裤子', '源氏木语', '[\"cargo1.jpg\", \"cargo2.jpg\"]', '{\"尺码\": [\"30\", \"32\", \"34\"], \"颜色\": \"军绿\", \"风格\": \"工装\", \"口袋数量\": \"5\"}', null);
INSERT INTO `products` VALUES ('82b2bb0d-b94d-11f0-853a-9c2dcdd43890', 'BCE短袖T恤', '夏季基础款短袖，纯棉舒适', '89.00', '上衣', 'BCE', '[\"tshirt1.jpg\", \"tshirt2.jpg\"]', '{\"尺码\": [\"S\", \"M\", \"L\", \"XL\"], \"材质\": \"纯棉\", \"颜色\": [\"白色\", \"黑色\", \"灰色\"]}', null);
INSERT INTO `products` VALUES ('82b2c158-b94d-11f0-853a-9c2dcdd43890', 'MHS商务外套', '正式商务场合外套，质感优良', '499.00', '外套', 'MHS', '[\"blazer1.jpg\", \"blazer2.jpg\"]', '{\"尺码\": [\"S\", \"M\", \"L\", \"XL\"], \"材质\": \"羊毛混纺\", \"颜色\": \"深蓝\", \"风格\": \"商务\"}', null);
INSERT INTO `products` VALUES ('82b2c1f0-b94d-11f0-853a-9c2dcdd43890', 'JE连帽夹克', '秋季轻薄夹克，连帽设计', '329.00', '外套', 'JE', '[\"hoodie1.jpg\", \"hoodie2.jpg\"]', '{\"厚度\": \"轻薄\", \"尺码\": [\"M\", \"L\", \"XL\"], \"连帽\": \"是\", \"颜色\": \"藏青\"}', null);
