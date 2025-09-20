import psycopg2
from decouple import config
import dj_database_url
import os

# Test Supabase connection for VitalCircle Django project

def test_supabase_connection():
    """Test direct connection to Supabase PostgreSQL"""
    try:
        # Get DATABASE_URL from .env file (same as Django uses)
        database_url = config('DATABASE_URL', default='')
        
        if not database_url:
            print("❌ DATABASE_URL not found in .env file")
            print("Please update your .env file with:")
            print("DATABASE_URL=postgresql://postgres:[PASSWORD]@db.ojqfozlrbzqjzsrsgpad.supabase.co:5432/postgres")
            return False
        
        # Parse the URL
        db_config = dj_database_url.parse(database_url)
        
        print(f"🔄 Connecting to: {db_config['HOST']}")
        print(f"📦 Database: {db_config['NAME']}")
        print(f"👤 User: {db_config['USER']}")
        
        # Connect using parsed config
        connection = psycopg2.connect(
            user=db_config['USER'],
            password=db_config['PASSWORD'],
            host=db_config['HOST'],
            port=db_config['PORT'],
            dbname=db_config['NAME']
        )
        
        print("✅ Connection successful!")
        
        # Test query
        cursor = connection.cursor()
        
        # Get current time
        cursor.execute("SELECT NOW();")
        current_time = cursor.fetchone()
        print(f"🕐 Current Time: {current_time[0]}")
        
        # Check if we can see Django tables (if migrations were run)
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'django_%'
            LIMIT 5;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print("📋 Django tables found:")
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("⚠️  No Django tables found. Run 'python manage.py migrate' first.")
        
        # Close connections
        cursor.close()
        connection.close()
        print("🔌 Connection closed.")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        print("\nTroubleshooting:")
        print("1. Check if DATABASE_URL is correct in .env")
        print("2. Verify your Supabase password")
        print("3. Make sure your Supabase project is active")
        return False

if __name__ == "__main__":
    print("🧪 Testing Supabase Connection for VitalCircle")
    print("=" * 50)
    test_supabase_connection()