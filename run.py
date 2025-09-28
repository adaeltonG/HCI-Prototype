#!/usr/bin/env python3
"""
Solent Alumni Hub - Authentication System
Run this script to start the Flask application with authentication.
"""

import os
import sys
from app import app, init_db

if __name__ == '__main__':
    print("🚀 Starting Solent Alumni Hub with Authentication...")
    print("📊 Initializing database...")
    init_db()
    print("✅ Database initialized successfully!")
    print("🔐 Authentication system ready!")
    print("🌐 Server starting at http://localhost:5000")
    print("👤 Demo credentials: Username: Adaelton, Password: user123")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
