from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from cat_book import CatBook
from datetime import datetime
import json
import os
import bcrypt
import re

app = Flask(__name__)
app.secret_key = 'supersecretkey123456'

# ===== 登录管理 =====
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录哦 🐱'
login_manager.login_message_category = 'info'

# ===== 用户数据文件 =====
USERS_FILE = 'users.json'

def load_users():
    """加载用户数据"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    """保存用户数据"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def is_valid_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# ===== 用户类 =====
class User(UserMixin):
    def __init__(self, email):
        self.id = email
        self.email = email

@login_manager.user_loader
def load_user(email):
    users = load_users()
    if email in users:
        return User(email)
    return None

# ===== 路由 =====

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        users = load_users()
        
        if email in users:
            stored_password = users[email]['password']
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                user = User(email)
                login_user(user)
                flash(f'🐱 欢迎回来，{users[email]["username"]}！', 'success')
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
        
        # 验证邮箱格式
        if not is_valid_email(email):
            flash('😿 邮箱格式不正确，请重新输入', 'danger')
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
        
        users = load_users()
        
        if email in users:
            flash('😿 该邮箱已被注册，请直接登录', 'warning')
            return render_template('register.html')
        
        # 加密密码
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users[email] = {
            'email': email,
            'username': username,
            'password': hashed.decode('utf-8'),
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_users(users)
        
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
    users = load_users()
    username = users.get(current_user.email, {}).get('username', '用户')
    return render_template('index.html', username=username, email=current_user.email)

# ===== API 接口 =====

@app.route('/api/records', methods=['GET'])
@login_required
def get_records():
    """获取所有记录"""
    return jsonify(book.records)

@app.route('/api/add', methods=['POST'])
@login_required
def add_record():
    """添加记录"""
    data = request.json
    date = data.get('date', datetime.now().strftime("%Y-%m-%d"))
    category = data.get('category', '其他')
    amount = float(data.get('amount', 0))
    note = data.get('note', '')
    type_ = data.get('type', '支出')
    
    record = book.add_record(date, category, amount, note, type_)
    return jsonify({'success': True, 'record': record})

@app.route('/api/delete/<int:record_id>', methods=['DELETE'])
@login_required
def delete_record(record_id):
    """删除记录"""
    book.delete_record(record_id)
    return jsonify({'success': True})

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """获取统计信息"""
    now = datetime.now()
    income, expense = book.get_monthly_summary(now.year, now.month)
    categories = book.get_category_summary(now.year, now.month)
    return jsonify({
        'income': income,
        'expense': expense,
        'balance': income - expense,
        'categories': categories
    })

@app.route('/api/weekly_stats', methods=['GET'])
@login_required
def get_weekly_stats():
    """获取本周统计"""
    from datetime import datetime, timedelta
    now = datetime.now()
    start = now - timedelta(days=now.weekday())
    end = start + timedelta(days=6)
    
    week_records = []
    for r in book.records:
        if r.get('date'):
            record_date = datetime.strptime(r['date'], "%Y-%m-%d")
            if start <= record_date <= end:
                week_records.append(r)
    
    total_income = sum(r['amount'] for r in week_records if r.get('type') == '收入')
    total_expense = sum(r['amount'] for r in week_records if r.get('type') == '支出')
    
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
def get_monthly_stats():
    """获取本月统计"""
    now = datetime.now()
    income, expense = book.get_monthly_summary(now.year, now.month)
    categories = book.get_category_summary(now.year, now.month)
    
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
    app.run(debug=True, host='0.0.0.0', port=5000)
