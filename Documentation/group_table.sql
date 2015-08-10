--
-- Table structure for table `groups`
--

DROP TABLE IF EXISTS `groups`;
CREATE TABLE `groups` (
      `id` int AUTO_INCREMENT not null,
      `group_name` varchar(128) NOT NULL,
      `quota` int(12) NOT NULL DEFAULT 0,
      `priority` double NOT NULL DEFAULT 10.0,
      `weight` double NOT NULL DEFAULT 1.0,
      `accept_surplus` boolean DEFAULT False,
      `busy` int(12) NOT NULL DEFAULT 0,
      `surplus_threshold` int(10) unsigned NOT NULL DEFAULT 0,
      `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
      `last_surplus_update` timestamp NULL DEFAULT NULL,
      PRIMARY KEY (`id`),
      UNIQUE KEY `gr_grp_name` (`group_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `queue_log`;
CREATE TABLE `queue_log` (
  `id` int DEFAULT NULL,
  `amount_in_queue` int(10) unsigned NOT NULL DEFAULT '0',
  `query_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT FK_qlog_gq_id FOREIGN KEY
    (`id`) REFERENCES `groups` (`id`)
    ON DELETE CASCADE,
  KEY `ts_idx` (`query_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE USER 'atlas_update'@'%' IDENTIFIED BY 'xxx';
CREATE USER 'atlas_edit'@'%' IDENTIFIED BY 'xxx';

GRANT SELECT, UPDATE ON atlas_groups.groups TO 'atlas_update'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON atlas_groups.groups TO 'atlas_edit'@'%';

FLUSH PRIVILEGES;
