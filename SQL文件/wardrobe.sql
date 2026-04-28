/*
Navicat MySQL Data Transfer

Source Server         : myconn
Source Server Version : 50712
Source Host           : localhost:3306
Source Database       : sys

Target Server Type    : MYSQL
Target Server Version : 50712
File Encoding         : 65001

Date: 2025-11-06 18:37:38
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for wardrobe
-- ----------------------------
DROP TABLE IF EXISTS `wardrobe`;
CREATE TABLE `wardrobe` (
  `id` char(36) NOT NULL COMMENT '衣柜项UUID',
  `user_id` char(36) NOT NULL COMMENT '关联用户ID',
  `product_id` char(36) NOT NULL COMMENT '关联商品ID',
  `images` json DEFAULT NULL COMMENT '用户穿着照片URL列表',
  `purchase_date` date DEFAULT NULL COMMENT '购买日期',
  `item_condition` varchar(50) DEFAULT NULL COMMENT '衣物状态（全新、九成新等）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_wardrobe_user_product` (`user_id`,`product_id`),
  KEY `idx_wardrobe_user` (`user_id`),
  KEY `idx_wardrobe_product` (`product_id`),
  KEY `idx_wardrobe_purchase_date` (`purchase_date`),
  CONSTRAINT `fk_wardrobe_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_wardrobe_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户虚拟衣柜表';

-- ----------------------------
-- Records of wardrobe
-- ----------------------------
