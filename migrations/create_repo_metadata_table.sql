-- Create a table to store repository metadata
CREATE TABLE IF NOT EXISTS repo_metadata (
    id BIGSERIAL PRIMARY KEY,
    repo_url TEXT NOT NULL UNIQUE,
    repo_name TEXT NOT NULL,
    file_count INTEGER NOT NULL,
    file_hashes JSONB NOT NULL,
    last_indexed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create an index on repo_url for faster lookups
CREATE INDEX IF NOT EXISTS repo_metadata_url_idx ON repo_metadata (repo_url);

-- Create a function to upsert repository metadata
CREATE OR REPLACE FUNCTION upsert_repo_metadata(
    p_repo_url TEXT,
    p_repo_name TEXT,
    p_file_count INTEGER,
    p_file_hashes JSONB
) RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO repo_metadata (repo_url, repo_name, file_count, file_hashes, last_indexed)
    VALUES (p_repo_url, p_repo_name, p_file_count, p_file_hashes, CURRENT_TIMESTAMP)
    ON CONFLICT (repo_url) 
    DO UPDATE SET 
        repo_name = p_repo_name,
        file_count = p_file_count,
        file_hashes = p_file_hashes,
        last_indexed = CURRENT_TIMESTAMP;
END;
$$;
