# test_supabase.py
from supabase import create_client, Client

url = "https://zygdfixfuvujnccyhgab.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp5Z2RmaXhmdXZ1am5jY3loZ2FiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDc4MTA2NiwiZXhwIjoyMDc2MzU3MDY2fQ.cFxHQ2yRb3pYD3s0S_FSRKWxvCVVd8e6R-mWrnnkukY"

supabase: Client = create_client(url, key)

data = supabase.table("ev_models").select("*").execute()
print(data.data)
