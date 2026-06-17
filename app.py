from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import json
import os
import bcrypt
import re
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
import requests

app = Flask(__name__)
app.secret_key = 'supersecretkey123456'

# ===== Brevo 邮件配置（已配置好） =====
BREVO_API_KEY = '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'

def send_email(to_email, subject, body):
    """通过 Brevo API 发送邮件"""
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }
    data = {
        "sender": {"name": "小鱼干记账本", "email": "1220518@outlook.com"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": body.replace('\n', '<br>')
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.status_code == 201
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False

# ===== 数据库连接 =====
def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    else:
        return psycopg2.connect(
            host='localhost',
            database='catbook',
            user='catbook_user',
            password=''
        )

def init_db():
    """初始化数据库表，自动添加缺失字段"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 创建用户表（基础表）
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    # ===== 检查并添加 reset_token 字段 =====
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
    columns = [row[0] for row in cur.fetchall()]
    
    if 'reset_token' not in columns:
        cur.execute('ALTER TABLE users ADD COLUMN reset_token TEXT')
        print("✅ 已添加 reset_token 字段")
    
    if 'reset_token_expiry' not in columns:
        cur.execute('ALTER TABLE users ADD COLUMN reset_token_expiry TEXT')
        print("✅ 已添加 reset_token_expiry 字段")
    
    if 'security_question' not in columns:
        cur.execute('ALTER TABLE users ADD COLUMN security_question TEXT')
        print("✅ 已添加 security_question 字段")
    
    if 'security_answer' not in columns:
        cur.execute('ALTER TABLE users ADD COLUMN security_answer TEXT')
        print("✅ 已添加 security_answer 字段")
    
    # 创建记录表
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
    print("✅ 数据库初始化完成！")

# ===== 用户操作 =====
def get_user(email):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def save_user(email, username, hashed_password, created_at, security_question=None, security_answer=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO users (email, username, password, created_at, security_question, security_answer) VALUES (%s, %s, %s, %s, %s, %s)',
        (email, username, hashed_password, created_at, security_question, security_answer)
    )
    conn.commit()
    cur.close()
    conn.close()

def update_user_token(email, token, expiry):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE users SET reset_token = %s, reset_token_expiry = %s WHERE email = %s',
                (token, expiry, email))
    conn.commit()
    cur.close()
    conn.close()

def update_user_password(email, new_hashed_password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE users SET password = %s, reset_token = NULL, reset_token_expiry = NULL WHERE email = %s',
                (new_hashed_password, email))
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

# ===== 静态文件路由 =====
@app.route('/bg_pattern.png')
def serve_bg():
    return send_file('bg_pattern.png', mimetype='image/png')

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
        security_question = request.form.get('security_question')
        security_answer = request.form.get('security_answer')
        
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
        save_user(email, username, hashed.decode('utf-8'), created_at, security_question, security_answer)
        
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

# ===== 忘记密码 =====
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = get_user(email)
        if not user:
            flash('😿 该邮箱未注册', 'danger')
            return render_template('forgot_password.html')
        
        token = str(uuid.uuid4())
        expiry = str(datetime.now().timestamp() + 900)  # 15分钟
        
        update_user_token(email, token, expiry)
        
        body = f'''你好 {user['username']}，

你请求了重置密码。请点击以下链接（15分钟内有效）：

https://cat-book-62zc.onrender.com/reset_password?token={token}

如果这不是你本人的操作，请忽略此邮件。

🐱 小鱼干记账本
'''
        
        success = send_email(email, '🐱 重置你的小鱼干记账本密码', body)
        if success:
            flash('📧 重置邮件已发送，请查收（15分钟有效）', 'success')
        else:
            flash('😿 邮件发送失败，请稍后重试', 'danger')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get('token')
    if not token:
        flash('😿 无效的链接', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM users WHERE reset_token = %s', (token,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if not user:
        flash('😿 无效的链接', 'danger')
        return redirect(url_for('login'))
    
    now = datetime.now().timestamp()
    if float(user['reset_token_expiry']) < now:
        flash('😿 链接已过期，请重新申请', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if not password or len(password) < 4:
            flash('😿 密码至少4个字符', 'danger')
            return render_template('reset_password.html', token=token)
        if password != confirm:
            flash('😿 两次密码不一致', 'danger')
            return render_template('reset_password.html', token=token)
        
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        update_user_password(user['email'], hashed.decode('utf-8'))
        
        flash('🎀 密码重置成功！请用新密码登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

# ===== API 接口 =====

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

# ===== 导出 Excel =====
@app.route('/api/export_excel', methods=['GET'])
@login_required
def export_excel():
    import io
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill
    
    records = get_records(current_user.email)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "记账本"
    
    headers = ['日期', '类别', '金额', '备注', '类型']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="FF8A80", end_color="FF8A80", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    
    for row_idx, r in enumerate(records, 2):
        ws.cell(row=row_idx, column=1, value=r['date'])
        ws.cell(row=row_idx, column=2, value=r['category'])
        ws.cell(row=row_idx, column=3, value=r['amount'])
        ws.cell(row=row_idx, column=4, value=r['note'] or '')
        ws.cell(row=row_idx, column=5, value=r['type'])
    
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 10
    ws.column_dimensions['D'].width = 20
    ws.column_dimensions['E'].width = 8
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'小鱼干记账_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

# ===== 启动 =====

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
    @app.route('/test_email')
def test_email():
    success = send_email('fipped99@qq.com', '🐱 测试邮件', '这是一封测试邮件，如果你收到了，说明邮件功能正常！')
    if success:
        return '✅ 邮件发送成功！请检查邮箱（包括垃圾箱）'
    else:
        return '❌ 邮件发送失败，请查看 Render 日志'
