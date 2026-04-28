/*
Navicat MySQL Data Transfer

Source Server         : myconn
Source Server Version : 50712
Source Host           : localhost:3306
Source Database       : sys

Target Server Type    : MYSQL
Target Server Version : 50712
File Encoding         : 65001

Date: 2025-11-06 18:35:52
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for outfits
-- ----------------------------
DROP TABLE IF EXISTS `outfits`;
CREATE TABLE `outfits` (
  `id` char(36) NOT NULL COMMENT '穿搭记录UUID',
  `user_id` char(36) NOT NULL COMMENT '关联用户ID',
  `items` json NOT NULL COMMENT '包含的商品ID列表（如["prod1","prod2"]）',
  `occasion` varchar(100) DEFAULT NULL COMMENT '穿搭场景（通勤、约会等）',
  `style_score` decimal(3,2) DEFAULT NULL COMMENT '风格评分（0-5分，业务层保证范围）',
  `images` json DEFAULT NULL COMMENT '穿搭照片URL列表',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_outfits_user` (`user_id`),
  KEY `idx_outfits_occasion` (`occasion`),
  CONSTRAINT `fk_outfits_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户穿搭记录表';

-- ----------------------------
-- Records of outfits
-- ----------------------------
