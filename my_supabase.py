import supabase

SUPABASE_URL = "https://pcyajeuztowzrkceidvc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBjeWFqZXV6dG93enJrY2VpZHZjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDE4NTM3MzUsImV4cCI6MjAxNzQyOTczNX0.KNtIUpp9OVzda-HggJGV3ptw0cKNHzqWzQMSnoIxJhQ"

supabase = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

# supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
# auth = supabase.auth

try:
    # Attempt to make a simple query to check the connection
    response, error = supabase.from_('your-table').select('*').execute()
    
    # Check for errors in the response
    if error is not None:
        print(f"Connection failed with error: {error}")
    else:
        print("Connection successful!")
except Exception as e:
    print(f"Connection failed with exception: {e}")