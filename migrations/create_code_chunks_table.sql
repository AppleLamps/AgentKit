-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the function to create the code_chunks table
CREATE OR REPLACE FUNCTION create_code_chunks_table()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    -- Create the table if it doesn't exist
    CREATE TABLE IF NOT EXISTS code_chunks (
        id BIGSERIAL PRIMARY KEY,
        content TEXT NOT NULL,
        embedding vector(768),  -- Using 768 dimensions for text-embedding-004 model
        metadata JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Create an index for similarity search using HNSW which supports higher dimensions
    CREATE INDEX IF NOT EXISTS code_chunks_embedding_idx ON code_chunks 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
END;
$$;
