/*
Navicat MySQL Data Transfer

Source Server         : myconn
Source Server Version : 50712
Source Host           : localhost:3306
Source Database       : sys

Target Server Type    : MYSQL
Target Server Version : 50712
File Encoding         : 65001

Date: 2025-11-06 18:36:15
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for role_permissions
-- ----------------------------
DROP TABLE IF EXISTS `role_permissions`;
CREATE TABLE `role_permissions` (
  `role_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`role_id`,`permission_id`),
  KEY `permission_id` (`permission_id`),
  CONSTRAINT `role_permissions_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`),
  CONSTRAINT `role_permissions_ibfk_2` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of role_permissions
-- ----------------------------
INSERT INTO `role_permissions` VALUES ('1', '1');
INSERT INTO `role_permissions` VALUES ('2', '1');
INSERT INTO `role_permissions` VALUES ('3', '1');
INSERT INTO `role_permissions` VALUES ('1', '2');
INSERT INTO `role_permissions` VALUES ('2', '2');
INSERT INTO `role_permissions` VALUES ('1', '3');
INSERT INTO `role_permissions` VALUES ('2', '3');
INSERT INTO `role_permissions` VALUES ('1', '4');
INSERT INTO `role_permissions` VALUES ('1', '5');
