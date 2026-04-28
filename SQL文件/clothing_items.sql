/*
Navicat MySQL Data Transfer

Source Server         : myconn
Source Server Version : 50712
Source Host           : localhost:3306
Source Database       : sys

Target Server Type    : MYSQL
Target Server Version : 50712
File Encoding         : 65001

Date: 2025-11-06 18:35:34
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for clothing_items
-- ----------------------------
DROP TABLE IF EXISTS `clothing_items`;
CREATE TABLE `clothing_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `category` varchar(100) NOT NULL,
  `subcategory` varchar(100) DEFAULT NULL,
  `color` varchar(100) DEFAULT NULL,
  `brand` varchar(100) DEFAULT NULL,
  `season` varchar(50) DEFAULT NULL,
  `occasion` varchar(100) DEFAULT NULL,
  `image_path` text,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of clothing_items
-- ----------------------------
INSERT INTO `clothing_items` VALUES ('4', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '格子衫', 'top', null, '蓝', '森林之家', 'autumn', null, 'uploads/20251019_181107_20251017145704_137_116.jpg', '2025-10-19 18:11:07');
INSERT INTO `clothing_items` VALUES ('5', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '直筒裤', 'bottom', null, '奶白色', '森林之家', 'autumn', null, 'uploads/20251020_091437_20251017145654_126_116.jpg', '2025-10-20 09:14:37');
INSERT INTO `clothing_items` VALUES ('7', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '微喇裤', 'bottom', null, '泥色', '巴黎世家', 'autumn', null, 'uploads/20251020_154529_20251017145702_135_116.jpg', '2025-10-20 15:45:29');
INSERT INTO `clothing_items` VALUES ('8', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '阔腿裤', 'bottom', null, '黑色', '巴黎世家', 'autumn', null, 'uploads/20251020_164235_20251019_175038_20251017145648_123_116.jpg', '2025-10-20 16:42:35');
INSERT INTO `clothing_items` VALUES ('9', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '束脚裤', 'bottom', null, '黑色', '巴黎世家', 'winter', null, 'uploads/20251020_164431_20251017145659_131_116.jpg', '2025-10-20 16:44:31');
INSERT INTO `clothing_items` VALUES ('10', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '连帽衣', 'top', null, '黑白色', '巴黎世家', 'autumn', null, 'uploads/20251020_165216_20251020164900_147_116.jpg', '2025-10-20 16:52:16');
INSERT INTO `clothing_items` VALUES ('11', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '短款棒球服', 'top', null, '深蓝色', '巴黎世家', 'autumn', null, 'uploads/20251020_165300_20251020164901_148_116.jpg', '2025-10-20 16:53:00');
INSERT INTO `clothing_items` VALUES ('13', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '格子衫', 'top', null, '蓝泥相间', 'LV', 'summer', null, 'uploads/20251020_165536_20251020165010_152_116.jpg', '2025-10-20 16:55:36');
INSERT INTO `clothing_items` VALUES ('14', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '板鞋', 'shoes', null, '黑白', 'Nike', 'winter', null, 'uploads/20251020_165923_u344561653850735200fm253app138fJPEG.jpg', '2025-10-20 16:59:23');
INSERT INTO `clothing_items` VALUES ('15', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '衬衫', 'top', null, '浅蓝', '辛普森', 'summer', null, 'uploads/20251021_164907_63dfefef6df1d50e81e33a2fad7d250c.png', '2025-10-21 16:49:07');
INSERT INTO `clothing_items` VALUES ('16', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '板鞋', 'shoes', null, '黑红', 'Nike', 'winter', null, 'uploads/20251021_165005_003cce9bede2b1a9665ddd05ffed79bf.png', '2025-10-21 16:50:05');
INSERT INTO `clothing_items` VALUES ('17', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '卡西欧手表', 'accessory', null, '银色', 'CASIO', 'spring', null, 'uploads/20251021_165200_71733281e37ef3d93f7a5ea630822699.png', '2025-10-21 16:52:00');
INSERT INTO `clothing_items` VALUES ('18', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '手表', 'accessory', null, '银色', 'CASIO', 'autumn', null, 'uploads/20251021_165239_fdae95aadba5dce8197d58ef88974a89.png', '2025-10-21 16:52:39');
INSERT INTO `clothing_items` VALUES ('19', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '手提包', 'accessory', null, '棕色', 'LV', 'spring', null, 'uploads/20251021_165319_98427e652cc277545c593259a3f99e0b.png', '2025-10-21 16:53:19');
INSERT INTO `clothing_items` VALUES ('20', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '微喇牛仔裤', 'bottom', null, '黑色', '巴黎世家', 'autumn', null, 'uploads/20251021_165349_c3652d19f53e683a36bb1470230513e4.png', '2025-10-21 16:53:49');
INSERT INTO `clothing_items` VALUES ('21', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '牛仔裤', 'bottom', null, '泥色', '巴黎世家', 'autumn', null, 'uploads/20251021_165443_acdc63299ad35df8756c941ed032d54e.png', '2025-10-21 16:54:43');
INSERT INTO `clothing_items` VALUES ('22', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '休闲板鞋', 'shoes', null, '白色', 'PUMA', 'summer', null, 'uploads/20251021_165625_f7ecebc7bc4cbee5f08c04333c5d172b.png', '2025-10-21 16:56:25');
INSERT INTO `clothing_items` VALUES ('24', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', 'AJ板鞋', 'shoes', null, '黑色', 'AJ', 'summer', null, 'uploads/20251021_165829_684fa14d083e1245cf58564d20efee5d.png', '2025-10-21 16:58:29');
INSERT INTO `clothing_items` VALUES ('25', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '休闲板鞋', 'shoes', null, '蓝白色', '阿迪达斯', 'autumn', null, 'uploads/20251021_165940_f0d900956fd20f9eda2c7372dcd78ca1.png', '2025-10-21 16:59:40');
INSERT INTO `clothing_items` VALUES ('26', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '帽子', 'accessory', null, '黑色', 'MLB', 'autumn', null, 'uploads/20251021_181345_a09f5b1b6fd0a76dfccd2d7cdb8354e5.png', '2025-10-21 18:13:45');
INSERT INTO `clothing_items` VALUES ('27', 'e8253f41-ae76-11f0-930e-9c2dcdd43890', '高跟鞋', 'shoes', null, '银白色', 'LV', 'summer', null, 'uploads/20251021_182518_faa34930cc703cd0c665b607be90a416.png', '2025-10-21 18:25:18');
INSERT INTO `clothing_items` VALUES ('28', 'd1d6d75b-b8e6-4e92-93ac-54dc0c180d24', '板鞋', 'shoes', null, '红白', 'Nike', 'winter', null, 'uploads/20251028_091934_20251020_165923_u344561653850735200fm253app138fJPEG.jpg', '2025-10-28 09:19:34');
INSERT INTO `clothing_items` VALUES ('29', 'fc989a39-b2d5-49fd-bf12-495a02453328', '碎花裙', 'top', null, '粉色', 'LV', 'summer', null, 'uploads/20251031_154337_20251027_022254_sweet_style.jpg', '2025-10-31 15:43:37');
INSERT INTO `clothing_items` VALUES ('30', 'fc989a39-b2d5-49fd-bf12-495a02453328', '美式高街休闲百搭裤', 'bottom', null, '泥色', '森林之家', 'autumn', null, 'uploads/20251031_154534_20251021_165443_acdc63299ad35df8756c941ed032d54e.png', '2025-10-31 15:45:34');
INSERT INTO `clothing_items` VALUES ('31', 'fc989a39-b2d5-49fd-bf12-495a02453328', '包包', 'accessory', null, '奶白色', 'LV', 'spring', null, 'uploads/20251031_154604_20251021_165729_26fa7fc08d55a05ea0252aeadbea7bbb.png', '2025-10-31 15:46:04');
INSERT INTO `clothing_items` VALUES ('32', 'fc989a39-b2d5-49fd-bf12-495a02453328', '高跟鞋', 'shoes', null, '银白色', 'LV', 'summer', null, 'uploads/20251031_154631_faa34930cc703cd0c665b607be90a416.png', '2025-10-31 15:46:31');
