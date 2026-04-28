/*
Navicat MySQL Data Transfer

Source Server         : myconn
Source Server Version : 50712
Source Host           : localhost:3306
Source Database       : sys

Target Server Type    : MYSQL
Target Server Version : 50712
File Encoding         : 65001

Date: 2025-11-06 18:36:53
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` char(36) NOT NULL COMMENT '用户UUID',
  `email` varchar(100) NOT NULL,
  `profile` json NOT NULL COMMENT '用户基础画像（姓名、性别等）',
  `style_preferences` json DEFAULT NULL COMMENT '用户风格偏好',
  `body_measurements` json DEFAULT NULL COMMENT '用户身材数据',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `username` varchar(50) DEFAULT NULL,
  `password_hash` varchar(255) NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `reset_token` varchar(100) DEFAULT NULL,
  `reset_token_expiration` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `username` (`username`),
  KEY `idx_reset_token` (`reset_token`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';

-- ----------------------------
-- Records of users
-- ----------------------------
INSERT INTO `users` VALUES ('127a2eb8-6048-4f88-944d-c86b3a3b95ee', 'example@example.com', '{\"name\": \"\", \"gender\": \"\"}', '{}', '{}', '2025-11-04 09:27:26', '2025-11-04 09:27:26', 'lhuan', 'scrypt:32768:8:1$PhURXFfaEBC70Mmt$42e92c9dbaacd672e30412e91f101c0eecc12d8f8fee23da737c5dae4759ba2ce888c219046d6051e7cd8627c28ac17deb72044bd3ca29bdd005300478039bdb');
INSERT INTO `users` VALUES ('2f49be6c-308e-4ed1-90c2-f23ea41df003', '2556152515@qq.com', '{\"name\": \"\", \"gender\": \"\"}', '{}', '{}', '2025-11-03 10:03:23', '2025-11-03 10:03:23', 'x1', 'scrypt:32768:8:1$dYeekUKIPvzgTAGe$65c55b04f05395bebd443c96a1119fbc8b86e448dd15fe3a61ad8e067104e897491d5f1479e6003a8c5d234a2a4e398dca3154f65717a01f188335e4603add9d');
INSERT INTO `users` VALUES ('d1d6d75b-b8e6-4e92-93ac-54dc0c180d24', '3086592960@qq.com', '{\"name\": \"\", \"gender\": \"\"}', '{}', '{}', '2025-10-21 21:17:13', '2025-11-03 10:13:46', 'xsc', 'scrypt:32768:8:1$l0yFTm6TiWDvRjZM$2e483e3d0a63323105c7fd6ef4bbe218c0f6800e85c58da4f50892e628c5b9c11c09613f447cea2cd5eab7555c3dd59599bf5cd99bbf5615eeb6b4d1d6e5d28b');
INSERT INTO `users` VALUES ('e8253f41-ae76-11f0-930e-9c2dcdd43890', 'admin@example.com', '{\"name\": \"管理员\", \"gender\": \"male\"}', null, null, '2025-10-21 20:10:12', '2025-11-06 18:32:02', 'admin', 'scrypt:32768:8:1$3tvSn8lyTfYZBgra$c2db2c90fd00f91f8850b0a1910d8496c069576890185afae94f618ea151f1e72cc8ae902de8dd392f5bf77edaed60b2b2d632b2320f92022d11dc1219687a97');
INSERT INTO `users` VALUES ('e8254978-ae76-11f0-930e-9c2dcdd43890', 'vip@example.com', '{\"name\": \"VIP用户\", \"gender\": \"female\"}', null, null, '2025-10-21 20:10:12', '2025-10-21 20:10:12', 'vip_user', '加密的密码');
INSERT INTO `users` VALUES ('e8254a4a-ae76-11f0-930e-9c2dcdd43890', 'user@example.com', '{\"name\": \"普通用户\", \"gender\": \"male\"}', null, null, '2025-10-21 20:10:12', '2025-10-21 20:10:12', 'normal_user', '加密的密码');
INSERT INTO `users` VALUES ('f20eba5f-b299-11f0-a268-9c2dcdd43890', 'sample@example.com', '{\"name\": \"示例用户\", \"gender\": \"未知\"}', '{\"preferred_styles\": [\"休闲\", \"优雅\"]}', '{\"shape\": \"标准\", \"skin_tone\": \"黄色\"}', '2025-10-27 02:31:10', '2025-10-27 02:31:10', 'sample_user', '$2b$12$LQv3c1yqBWVHxkd0g8A7CuZ6vY6V3D3e7K3jV8mM6n8dJpLmN7oO2');
INSERT INTO `users` VALUES ('fc989a39-b2d5-49fd-bf12-495a02453328', 'huanou@example.com', '{\"name\": \"\", \"gender\": \"\"}', '{}', '{}', '2025-10-22 11:07:57', '2025-10-22 11:07:57', 'huanou', 'scrypt:32768:8:1$1YP0D56vNyNw5Dnx$c68270b17197a2ffd4702db0dd4eaa96aec14c7a054b590c6ba24b2205fc6963726655ffc39e723d2d849447e34fc018dd4847e8fa6063b89cb2fd1ba3789b9c');
