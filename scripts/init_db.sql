-- VEDANTA PostgreSQL initialization script
-- Creates extensions required by VEDANTA

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Create search configuration for institutional content
CREATE TEXT SEARCH CONFIGURATION IF NOT EXISTS vedanta_english (COPY = english);
