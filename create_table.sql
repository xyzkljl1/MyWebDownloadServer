-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               8.0.17 - MySQL Community Server - GPL
-- Server OS:                    Win64
-- HeidiSQL Version:             10.2.0.5599
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;


-- Dumping database structure for youtubedl
CREATE DATABASE IF NOT EXISTS `youtubedl` /*!40100 DEFAULT CHARACTER SET utf8 COLLATE utf8_bin */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `youtubedl`;

-- Dumping structure for table youtubedl.queue
CREATE TABLE IF NOT EXISTS `queue` (
  `Id` int(11) NOT NULL AUTO_INCREMENT,
  `URL` varchar(500) COLLATE utf8_bin NOT NULL DEFAULT '',
  `Cookie` varchar(2000) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL DEFAULT '',
  `UpdateTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `FailCount` int(10) unsigned NOT NULL DEFAULT '0',
  `FailMessage` varchar(10000) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL DEFAULT '',
  `UserAgent` varchar(1000) COLLATE utf8_bin NOT NULL DEFAULT '',
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB AUTO_INCREMENT=725 DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

-- Data exporting was unselected.

/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
