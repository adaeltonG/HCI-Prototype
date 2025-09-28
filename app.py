from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
import sqlite3
import bcrypt
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

def init_db():
    conn = sqlite3.connect('prototype.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            search_keyword TEXT NOT NULL,
            search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alumni_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            graduation_year INTEGER,
            degree TEXT,
            current_position TEXT,
            company TEXT,
            location TEXT,
            email TEXT,
            linkedin_url TEXT
        )
    ''')
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('Adaelton',))
    if cursor.fetchone()[0] == 0:
        password = 'user123'
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, email)
            VALUES (?, ?, ?, ?)
        ''', ('Adaelton', password_hash, 'Adaelton Silva', 'adaelton@example.com'))
    
    cursor.execute('SELECT COUNT(*) FROM alumni_data')
    if cursor.fetchone()[0] == 0:
        dummy_alumni = [
            ('Sarah Johnson', 2020, 'Computer Science', 'Software Engineer', 'Google', 'London, UK', 'sarah.johnson@example.com', 'https://linkedin.com/in/sarahjohnson'),
            ('Michael Chen', 2019, 'Business Administration', 'Marketing Manager', 'Microsoft', 'Manchester, UK', 'michael.chen@example.com', 'https://linkedin.com/in/michaelchen'),
            ('Emma Wilson', 2021, 'Graphic Design', 'UI/UX Designer', 'Apple', 'Birmingham, UK', 'emma.wilson@example.com', 'https://linkedin.com/in/emmawilson'),
            ('David Brown', 2018, 'Engineering', 'Project Manager', 'Tesla', 'Liverpool, UK', 'david.brown@example.com', 'https://linkedin.com/in/davidbrown'),
            ('Lisa Garcia', 2022, 'Psychology', 'HR Specialist', 'Amazon', 'Leeds, UK', 'lisa.garcia@example.com', 'https://linkedin.com/in/lisagarcia')
        ]
        
        cursor.executemany('''
            INSERT INTO alumni_data (name, graduation_year, degree, current_position, company, location, email, linkedin_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', dummy_alumni)
    
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        
        conn = sqlite3.connect('prototype.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, password_hash, full_name, username FROM users WHERE LOWER(username) = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1]):
            session['user_id'] = user[0]
            session['username'] = user[3]
            session['full_name'] = user[2]
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/api/user')
@login_required
def get_user():
    return jsonify({
        'username': session.get('username'),
        'full_name': session.get('full_name')
    })

@app.route('/api/search', methods=['POST'])
@login_required
def search_alumni():
    try:
        data = request.get_json()
        search_term = data.get('search_term', '').strip()
        
        if not search_term:
            return jsonify({'results': [], 'message': 'Please enter a search term'})
        
        conn = sqlite3.connect('prototype.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO search_logs (user_id, search_keyword)
            VALUES (?, ?)
        ''', (session['user_id'], search_term))
        conn.commit()
        
        cursor.execute('''
            SELECT name, graduation_year, degree, current_position, company, location, email, linkedin_url
            FROM alumni_data
            WHERE name LIKE ? OR degree LIKE ? OR current_position LIKE ? OR company LIKE ? OR location LIKE ? OR graduation_year LIKE ?
        ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'name': row[0],
                'graduation_year': row[1],
                'degree': row[2],
                'current_position': row[3],
                'company': row[4],
                'location': row[5],
                'email': row[6],
                'linkedin_url': row[7]
            })
        
        conn.close()
        
        return jsonify({
            'results': results,
            'count': len(results),
            'search_term': search_term
        })
        
    except Exception as e:
        return jsonify({'error': 'Search failed', 'message': str(e)}), 500

@app.route('/api/search-logs')
@login_required
def get_search_logs():
    conn = sqlite3.connect('prototype.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT search_keyword, search_timestamp
        FROM search_logs
        WHERE user_id = ?
        ORDER BY search_timestamp DESC
        LIMIT 10
    ''', (session['user_id'],))
    
    logs = []
    for row in cursor.fetchall():
        logs.append({
            'keyword': row[0],
            'timestamp': row[1]
        })
    
    conn.close()
    return jsonify({'search_logs': logs})

if __name__ == '__main__':
    init_db()
   
