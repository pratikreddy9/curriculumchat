import pymongo
from urllib.parse import quote_plus

# Credentials
username = "admin"
password = "Ayotta@123"
host = "notify.pesuacademy.com"
port = "27017"
auth_db = "admin"

# MongoDB Connection URI
uri = f"mongodb://{quote_plus(username)}:{quote_plus(password)}@{host}:{port}/{auth_db}"

try:
    client = pymongo.MongoClient(uri)
    client.server_info()  # Check connection
    print("✅ Connected successfully to MongoDB!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
