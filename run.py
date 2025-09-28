import os
import sys
from app import app, init_db

if __name__ == '__main__':
    print("🚀 Starting Solent Alumni Hub")
    print("📊 Initializing database...")
    init_db()
    print("✅ Database initialized successfully!")
    print("🌐 Server starting at http://localhost:5000")
    print("👤 Demo credentials: Username: Adaelton, Password: user123")    
    app.run(port=5000)
