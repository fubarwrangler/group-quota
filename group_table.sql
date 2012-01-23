--
-- Table structure for table `atlas_group_quotas`
--

DROP TABLE IF EXISTS `atlas_group_quotas`;
CREATE TABLE `atlas_group_quotas` (
      `group_name` varchar(64) NOT NULL,
      `quota` int(12) NOT NULL DEFAULT 0,
      `priority` double DEFAULT 10.0,
      `auto_regroup` boolean DEFAULT False,
      `busy` int(12),
      `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`group_name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

