from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import json
import os
import bcrypt
import re
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'supersecretkey123456'

# ===== 数据库连接 =====
def get_db_connection():
    """获取数据库连接"""
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    else:
        # 本地开发用
        return psycopg2.connect(
            host='localhost',
            database='catbook',
            user='catbook_user',
            password=''
        )

def init_db():
    """初始化数据库表"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 用户表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    # 记录表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id SERIAL PRIMARY KEY,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            note TEXT,
            type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            user_email TEXT NOT NULL,
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ 数据库表创建成功！")

# ===== 用户操作 =====
def get_user(email):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def save_user(email, username, hashed_password, created_at):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO users (email, username, password, created_at) VALUES (%s, %s, %s, %s)',
        (email, username, hashed_password, created_at)
    )
    conn.commit()
    cur.close()
    conn.close()

# ===== 记录操作 =====
def get_records(email):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM records WHERE user_email = %s ORDER BY id DESC', (email,))
    records = cur.fetchall()
    cur.close()
    conn.close()
    return records

def add_record(email, date, category, amount, note, type_, created_at):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO records (date, category, amount, note, type, created_at, user_email) VALUES (%s, %s, %s, %s, %s, %s, %s)',
        (date, category, amount, note, type_, created_at, email)
    )
    conn.commit()
    cur.close()
    conn.close()

def delete_record(record_id, email):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM records WHERE id = %s AND user_email = %s', (record_id, email))
    conn.commit()
    cur.close()
    conn.close()

# ===== 验证 =====
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# ===== 登录管理 =====
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录哦 🐱'
login_manager.login_message_category = 'info'

class User(UserMixin):
    def __init__(self, email):
        self.id = email
        self.email = email

@login_manager.user_loader
def load_user(email):
    user = get_user(email)
    if user:
        return User(email)
    return None

# ===== 路由 =====

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = get_user(email)
        
        if user:
            stored_password = user['password']
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                login_user(User(email))
                flash(f'🐱 欢迎回来，{user["username"]}！', 'success')
                return redirect(url_for('index'))
            else:
                flash('😿 密码错误，再试一次吧', 'danger')
        else:
            flash('😿 该邮箱未注册，请先注册', 'warning')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not is_valid_email(email):
            flash('😿 邮箱格式不正确', 'danger')
            return render_template('register.html')
        
        if not username or len(username) < 2:
            flash('😿 昵称至少2个字符', 'danger')
            return render_template('register.html')
        
        if not password or len(password) < 4:
            flash('😿 密码至少4个字符', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('😿 两次密码不一致', 'danger')
            return render_template('register.html')
        
        if get_user(email):
            flash('😿 该邮箱已被注册', 'warning')
            return render_template('register.html')
        
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_user(email, username, hashed.decode('utf-8'), created_at)
        
        flash('🎀 注册成功！请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('🐱 已退出，下次见~', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    user = get_user(current_user.email)
    username = user['username'] if user else '用户'
    return render_template('index.html', username=username, email=current_user.email)

# ===== API =====

@app.route('/api/records', methods=['GET'])
@login_required
def api_get_records():
    records = get_records(current_user.email)
    return jsonify([dict(r) for r in records])

@app.route('/api/add', methods=['POST'])
@login_required
def api_add_record():
    data = request.json
    date = data.get('date', datetime.now().strftime("%Y-%m-%d"))
    category = data.get('category', '其他')
    amount = float(data.get('amount', 0))
    note = data.get('note', '')
    type_ = data.get('type', '支出')
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    add_record(current_user.email, date, category, amount, note, type_, created_at)
    return jsonify({'success': True})

@app.route('/api/delete/<int:record_id>', methods=['DELETE'])
@login_required
def api_delete_record(record_id):
    delete_record(record_id, current_user.email)
    return jsonify({'success': True})

@app.route('/api/stats', methods=['GET'])
@login_required
def api_get_stats():
    records = get_records(current_user.email)
    now = datetime.now()
    month_str = f"{now.year}-{now.month:02d}"
    
    income = 0.0
    expense = 0.0
    categories = {}
    
    for r in records:
        if r['date'].startswith(month_str):
            if r['type'] == '收入':
                income += r['amount']
            else:
                expense += r['amount']
                cat = r['category']
                categories[cat] = categories.get(cat, 0.0) + r['amount']
    
    return jsonify({
        'income': income,
        'expense': expense,
        'balance': income - expense,
        'categories': categories
    })

@app.route('/api/weekly_stats', methods=['GET'])
@login_required
def api_get_weekly_stats():
    from datetime import datetime, timedelta
    records = get_records(current_user.email)
    now = datetime.now()
    start = now - timedelta(days=now.weekday())
    end = start + timedelta(days=6)
    
    week_records = []
    for r in records:
        if r.get('date'):
            record_date = datetime.strptime(r['date'], "%Y-%m-%d")
            if start <= record_date <= end:
                week_records.append(r)
    
    total_income = sum(r['amount'] for r in week_records if r['type'] == '收入')
    total_expense = sum(r['amount'] for r in week_records if r['type'] == '支出')
    
    return jsonify({
        'start': start.strftime("%Y-%m-%d"),
        'end': end.strftime("%Y-%m-%d"),
        'income': total_income,
        'expense': total_expense,
        'balance': total_income - total_expense,
        'records': week_records
    })

@app.route('/api/monthly_stats', methods=['GET'])
@login_required
def api_get_monthly_stats():
    records = get_records(current_user.email)
    now = datetime.now()
    month_str = f"{now.year}-{now.month:02d}"
    
    income = 0.0
    expense = 0.0
    categories = {}
    
    for r in records:
        if r['date'].startswith(month_str):
            if r['type'] == '收入':
                income += r['amount']
            else:
                expense += r['amount']
                cat = r['category']
                categories[cat] = categories.get(cat, 0.0) + r['amount']
    
    return jsonify({
        'year': now.year,
        'month': now.month,
        'income': income,
        'expense': expense,
        'balance': income - expense,
        'categories': categories
    })

# ===== 启动 =====

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
