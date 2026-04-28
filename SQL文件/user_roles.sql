/*
Navicat MySQL Data Transfer

Source Server         : myconn
Source Server Version : 50712
Source Host           : localhost:3306
Source Database       : sys

Target Server Type    : MYSQL
Target Server Version : 50712
File Encoding         : 65001

Date: 2025-11-06 18:36:45
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for user_roles
-- ----------------------------
DROP TABLE IF EXISTS `user_roles`;
CREATE TABLE `user_roles` (
  `user_id` char(36) NOT NULL,
  `role_id` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`,`role_id`),
  KEY `role_id` (`role_id`),
  CONSTRAINT `user_roles_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `user_roles_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Records of user_roles
-- ----------------------------
INSERT INTO `user_roles` VALUES ('127a2eb8-6048-4f88-944d-c86b3a3b95ee', '3', '2025-11-04 09:27:26');
INSERT INTO `user_roles` VALUES ('2f49be6c-308e-4ed1-90c2-f23ea41df003', '3', '2025-11-03 10:03:23');
INSERT INTO `user_roles` VALUES ('d1d6d75b-b8e6-4e92-93ac-54dc0c180d24', '3', '2025-10-21 21:17:13');
INSERT INTO `user_roles` VALUES ('e8253f41-ae76-11f0-930e-9c2dcdd43890', '1', '2025-10-21 20:10:12');
INSERT INTO `user_roles` VALUES ('e8254978-ae76-11f0-930e-9c2dcdd43890', '2', '2025-10-21 20:10:12');
INSERT INTO `user_roles` VALUES ('e8254a4a-ae76-11f0-930e-9c2dcdd43890', '3', '2025-10-21 20:10:12');
INSERT INTO `user_roles` VALUES ('fc989a39-b2d5-49fd-bf12-495a02453328', '3', '2025-10-22 11:07:57');
