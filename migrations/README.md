# Database Migrations

This directory contains SQL migration scripts for the Supabase database used by AgentKit.

## How to Apply Migrations

Since the Supabase API key used by the application might not have permissions to create tables, these migrations should be applied manually through the Supabase SQL Editor.

1. Log in to your Supabase dashboard
2. Navigate to the SQL Editor
3. Copy the contents of each SQL file in this directory
4. Paste into the SQL Editor and execute

## Migration Files

- `create_repo_metadata_table.sql` - Creates a table to store repository metadata for efficient change detection

## Table Schema

### repo_metadata

Stores metadata about indexed repositories to enable efficient change detection.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGSERIAL | Primary key |
| repo_url | TEXT | URL of the GitHub repository (unique) |
| repo_name | TEXT | Name of the repository |
| file_count | INTEGER | Number of files in the repository |
| file_hashes | JSONB | JSON object mapping file paths to their MD5 hashes |
| last_indexed | TIMESTAMP | When the repository was last indexed |
| created_at | TIMESTAMP | When the record was created |

The table also includes:
- A unique index on `repo_url` for faster lookups
- An `upsert_repo_metadata` function to simplify updating repository data
