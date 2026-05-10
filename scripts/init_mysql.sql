-- Initialize MySQL schema for gaokao-pilot.
-- Run with: mysql -u root -p < scripts/init_mysql.sql

CREATE DATABASE IF NOT EXISTS gaokao_pilot
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE gaokao_pilot;

CREATE TABLE IF NOT EXISTS school (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  school_code VARCHAR(32) NOT NULL COMMENT 'Official school code',
  name VARCHAR(128) NOT NULL COMMENT 'School name',
  province VARCHAR(32) NOT NULL COMMENT 'School province',
  city VARCHAR(64) NULL COMMENT 'School city',
  school_type VARCHAR(64) NULL COMMENT 'School type, such as comprehensive or science',
  education_level VARCHAR(32) NULL COMMENT 'Education level, such as undergraduate',
  is_985 TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Whether the school is in Project 985',
  is_211 TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Whether the school is in Project 211',
  is_double_first_class TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Whether the school is Double First-Class',
  official_website VARCHAR(255) NULL COMMENT 'Official website URL',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation time',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time',
  PRIMARY KEY (id),
  UNIQUE KEY uk_school_code (school_code),
  KEY idx_school_province_type (province, school_type),
  KEY idx_school_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='School master table';

CREATE TABLE IF NOT EXISTS user (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  username VARCHAR(50) NOT NULL COMMENT 'Unique login username',
  email VARCHAR(255) NOT NULL COMMENT 'Unique email address',
  password_hash VARCHAR(255) NOT NULL COMMENT 'Bcrypt password hash',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation time',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time',
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_username (username),
  UNIQUE KEY uk_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Application users';

CREATE TABLE IF NOT EXISTS user_activity (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  user_id BIGINT UNSIGNED NOT NULL COMMENT 'Owner user ID',
  activity_type VARCHAR(32) NOT NULL COMMENT 'recommendation / school_view / qa / report',
  target_id VARCHAR(64) NULL COMMENT 'Optional target identifier',
  summary VARCHAR(255) NOT NULL COMMENT 'Readable activity summary',
  payload_json JSON NULL COMMENT 'Optional activity payload',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation time',
  PRIMARY KEY (id),
  KEY idx_user_activity_user_created (user_id, created_at),
  KEY idx_user_activity_type_created (activity_type, created_at),
  CONSTRAINT fk_user_activity_user
    FOREIGN KEY (user_id) REFERENCES user (id)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Lightweight user activity stream';

CREATE TABLE IF NOT EXISTS favorite_school (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  user_id BIGINT UNSIGNED NOT NULL COMMENT 'Owner user ID',
  school_id BIGINT UNSIGNED NOT NULL COMMENT 'School ID or snapshot source ID',
  school_name_snapshot VARCHAR(128) NOT NULL COMMENT 'Snapshot school name',
  province_snapshot VARCHAR(32) NULL COMMENT 'Snapshot province',
  city_snapshot VARCHAR(64) NULL COMMENT 'Snapshot city',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation time',
  PRIMARY KEY (id),
  UNIQUE KEY uk_favorite_school_user_school (user_id, school_id),
  KEY idx_favorite_school_user_created (user_id, created_at),
  CONSTRAINT fk_favorite_school_user
    FOREIGN KEY (user_id) REFERENCES user (id)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='User favorite school snapshots';

CREATE TABLE IF NOT EXISTS plan (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  user_id BIGINT UNSIGNED NOT NULL COMMENT 'Owner user ID',
  name VARCHAR(100) NOT NULL COMMENT 'Plan name',
  province VARCHAR(32) NOT NULL COMMENT 'Candidate province',
  subject_type VARCHAR(32) NOT NULL COMMENT 'Subject type',
  score INT UNSIGNED NOT NULL COMMENT 'Candidate score',
  rank INT UNSIGNED NOT NULL COMMENT 'Candidate rank',
  status VARCHAR(32) NOT NULL DEFAULT 'draft' COMMENT 'Plan status',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation time',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time',
  PRIMARY KEY (id),
  KEY idx_plan_user_updated (user_id, updated_at),
  CONSTRAINT fk_plan_user
    FOREIGN KEY (user_id) REFERENCES user (id)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='User volunteer plans';

CREATE TABLE IF NOT EXISTS major (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  major_code VARCHAR(32) NOT NULL COMMENT 'Official major code',
  name VARCHAR(128) NOT NULL COMMENT 'Major name',
  category VARCHAR(64) NULL COMMENT 'Major category',
  degree_type VARCHAR(64) NULL COMMENT 'Degree type, such as bachelor of engineering',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation time',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time',
  PRIMARY KEY (id),
  UNIQUE KEY uk_major_code (major_code),
  KEY idx_major_category (category),
  KEY idx_major_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Major master table';

CREATE TABLE IF NOT EXISTS plan_item (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  plan_id BIGINT UNSIGNED NOT NULL COMMENT 'Plan ID',
  school_id BIGINT UNSIGNED NULL COMMENT 'School ID',
  major_id BIGINT UNSIGNED NULL COMMENT 'Major ID',
  group_type VARCHAR(16) NOT NULL COMMENT 'rush / stable / safe',
  sort_order INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Sort order inside one group',
  source_type VARCHAR(32) NOT NULL DEFAULT 'recommendation' COMMENT 'manual / recommendation',
  recommend_reason TEXT NULL COMMENT 'Recommendation reason',
  risk_level VARCHAR(32) NULL COMMENT 'Risk level',
  school_name_snapshot VARCHAR(128) NOT NULL COMMENT 'Snapshot school name for durable display',
  major_name_snapshot VARCHAR(128) NULL COMMENT 'Snapshot major name for durable display',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation time',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time',
  PRIMARY KEY (id),
  KEY idx_plan_item_plan_group_order (plan_id, group_type, sort_order),
  KEY idx_plan_item_school (school_id),
  KEY idx_plan_item_major (major_id),
  CONSTRAINT fk_plan_item_plan
    FOREIGN KEY (plan_id) REFERENCES plan (id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_plan_item_school
    FOREIGN KEY (school_id) REFERENCES school (id)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT fk_plan_item_major
    FOREIGN KEY (major_id) REFERENCES major (id)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Plan items under one volunteer plan';

CREATE TABLE IF NOT EXISTS school_major (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  school_id BIGINT UNSIGNED NOT NULL COMMENT 'School ID',
  major_id BIGINT UNSIGNED NOT NULL COMMENT 'Major ID',
  school_major_code VARCHAR(32) NULL COMMENT 'Major code used by the school or admission plan',
  degree_type VARCHAR(64) NULL COMMENT 'Degree type for this school-major relation',
  duration_years DECIMAL(3,1) NULL COMMENT 'Default study duration in years',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation time',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time',
  PRIMARY KEY (id),
  UNIQUE KEY uk_school_major (school_id, major_id),
  KEY idx_school_major_major_id (major_id),
  CONSTRAINT fk_school_major_school
    FOREIGN KEY (school_id) REFERENCES school (id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_school_major_major
    FOREIGN KEY (major_id) REFERENCES major (id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='School-major relation table';

CREATE TABLE IF NOT EXISTS score_line (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  school_id BIGINT UNSIGNED NOT NULL COMMENT 'School ID',
  major_id BIGINT UNSIGNED NULL COMMENT 'Major ID, nullable for school-level score lines',
  year SMALLINT UNSIGNED NOT NULL COMMENT 'Admission year',
  province VARCHAR(32) NOT NULL COMMENT 'Candidate province',
  subject_type VARCHAR(32) NOT NULL COMMENT 'Subject type, such as physics or history',
  batch VARCHAR(64) NOT NULL COMMENT 'Admission batch',
  min_score SMALLINT UNSIGNED NOT NULL COMMENT 'Minimum admission score',
  min_rank INT UNSIGNED NULL COMMENT 'Minimum admission rank',
  avg_score DECIMAL(6,2) NULL COMMENT 'Average admission score',
  max_score SMALLINT UNSIGNED NULL COMMENT 'Highest admission score',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation time',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time',
  PRIMARY KEY (id),
  KEY idx_score_line_province_year_subject_min_score (province, year, subject_type, min_score),
  KEY idx_score_line_province_year_subject_min_rank (province, year, subject_type, min_rank),
  KEY idx_score_line_province_year_subject (province, year, subject_type),
  KEY idx_score_line_school_year (school_id, year),
  KEY idx_score_line_major_year (major_id, year),
  CONSTRAINT fk_score_line_school
    FOREIGN KEY (school_id) REFERENCES school (id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_score_line_major
    FOREIGN KEY (major_id) REFERENCES major (id)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Historical admission score line table';

CREATE TABLE IF NOT EXISTS admission_plan (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  school_id BIGINT UNSIGNED NOT NULL COMMENT 'School ID',
  major_id BIGINT UNSIGNED NOT NULL COMMENT 'Major ID',
  year SMALLINT UNSIGNED NOT NULL COMMENT 'Admission year',
  province VARCHAR(32) NOT NULL COMMENT 'Candidate province',
  subject_type VARCHAR(32) NOT NULL COMMENT 'Subject type, such as physics or history',
  batch VARCHAR(64) NOT NULL COMMENT 'Admission batch',
  enrollment_count INT UNSIGNED NOT NULL COMMENT 'Planned enrollment count',
  tuition DECIMAL(10,2) NULL COMMENT 'Annual tuition fee',
  duration_years DECIMAL(3,1) NULL COMMENT 'Study duration in years',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation time',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time',
  PRIMARY KEY (id),
  KEY idx_admission_plan_school_year (school_id, year),
  KEY idx_admission_plan_major_year (major_id, year),
  KEY idx_admission_plan_province_year_subject (province, year, subject_type),
  CONSTRAINT fk_admission_plan_school
    FOREIGN KEY (school_id) REFERENCES school (id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_admission_plan_major
    FOREIGN KEY (major_id) REFERENCES major (id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Admission plan table';
