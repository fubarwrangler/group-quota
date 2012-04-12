--
-- Table structure for table `atlas_group_quotas`
--

DROP TABLE IF EXISTS `atlas_group_quotas`;
CREATE TABLE `atlas_group_quotas` (
      `group_name` varchar(64) NOT NULL,
      `quota` int(12) NOT NULL DEFAULT 0,
      `priority` double DEFAULT 10.0,
      `accept_surplus` boolean DEFAULT False,
      `busy` int(12) NOT NULL DEFAULT 0,
      `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (`group_name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE USER 'atlas_update'@'%' IDENTIFIED BY 'xxx';
CREATE USER 'atlas_edit'@'%' IDENTIFIED BY 'xxx';

GRANT SELECT, UPDATE ON linux_farm.atlas_group_quotas TO 'atlas_update'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON linux_farm.atlas_group_quotas TO 'atlas_edit'@'%';

FLUSH PRIVILEGES;
