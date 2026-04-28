/*
Navicat MySQL Data Transfer

Source Server         : myconn
Source Server Version : 50712
Source Host           : localhost:3306
Source Database       : sys

Target Server Type    : MYSQL
Target Server Version : 50712
File Encoding         : 65001

Date: 2025-11-06 18:36:38
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for user_profiles
-- ----------------------------
DROP TABLE IF EXISTS `user_profiles`;
CREATE TABLE `user_profiles` (
  `user_id` char(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户ID，关联users表',
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名',
  `body_shape` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '体型',
  `skin_tone` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '肤色',
  `style_pref` text COLLATE utf8mb4_unicode_ci COMMENT '风格偏好',
  `height` float DEFAULT NULL COMMENT '身高(cm)',
  `weight` float DEFAULT NULL COMMENT '体重(kg)',
  `age` int(11) DEFAULT NULL COMMENT '年龄',
  `gender` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '性别',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `username` (`username`),
  KEY `idx_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户档案表';

-- ----------------------------
-- Records of user_profiles
-- ----------------------------
INSERT INTO `user_profiles` VALUES ('d1d6d75b-b8e6-4e92-93ac-54dc0c180d24', 'xsc', '矩形', '白色', '甜美', null, null, null, null, '2025-10-27 02:22:55', '2025-10-27 02:22:55');
INSERT INTO `user_profiles` VALUES ('f20eba5f-b299-11f0-a268-9c2dcdd43890', 'sample_user', '梨形', '白色', '运动', null, null, null, null, '2025-10-27 02:34:45', '2025-10-27 02:34:45');
INSERT INTO `user_profiles` VALUES ('fc989a39-b2d5-49fd-bf12-495a02453328', 'huanou', '梨形', '白色', '[]', null, null, null, null, '2025-10-31 11:42:47', '2025-10-31 11:42:47');
