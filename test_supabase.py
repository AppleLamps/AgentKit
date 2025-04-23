import os
from dotenv import load_dotenv
from supabase import create_client

def test_supabase_connection():
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
        return False
    
    try:
        # Initialize Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Test 1: Basic connection
        print("🔄 Testing Supabase connection...")
        version = supabase.table("code_chunks").select("*").execute()
        print("✅ Connection successful!")
        
        # Test 2: Check if vector extension exists
        print("\n🔄 Checking pgvector extension...")
        result = supabase.rpc('check_vector_ext', {}).execute()
        print("✅ pgvector extension is enabled!")
        
        # Test 3: Check if code_chunks table exists
        print("\n🔄 Checking code_chunks table...")
        result = supabase.table("code_chunks").select("*").execute()
        print("✅ code_chunks table exists!")
        
        return True
        
    except Exception as e:
        if "relation" in str(e) and "does not exist" in str(e):
            print("❌ Error: code_chunks table not found. Need to run setup SQL.")
        elif "function" in str(e) and "does not exist" in str(e):
            print("❌ Error: check_vector_ext function not found. Need to run setup SQL.")
        else:
            print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_supabase_connection()
