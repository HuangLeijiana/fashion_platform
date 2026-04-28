/*
Navicat MySQL Data Transfer

Source Server         : myconn
Source Server Version : 50712
Source Host           : localhost:3306
Source Database       : sys

Target Server Type    : MYSQL
Target Server Version : 50712
File Encoding         : 65001

Date: 2025-11-06 18:35:59
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for permissions
-- ----------------------------
DROP TABLE IF EXISTS `permissions`;
CREATE TABLE `permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of permissions
-- ----------------------------
INSERT INTO `permissions` VALUES ('1', 'view_wardrobe', '查看我的衣柜');
INSERT INTO `permissions` VALUES ('2', 'edit_wardrobe', '编辑我的衣柜');
INSERT INTO `permissions` VALUES ('3', 'delete_wardrobe', '删除衣柜内容');
INSERT INTO `permissions` VALUES ('4', 'manage_products', '管理平台商品');
INSERT INTO `permissions` VALUES ('5', 'view_admin', '访问管理后台');
