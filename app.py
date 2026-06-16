from flask import Flask, render_template, request, jsonify
from cat_book import CatBook
from datetime import datetime
import json

app = Flask(__name__)
book = CatBook()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/records', methods=['GET'])
def get_records():
    """获取所有记录"""
    return jsonify(book.records)

@app.route('/api/add', methods=['POST'])
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
def delete_record(record_id):
    """删除记录"""
    book.delete_record(record_id)
    return jsonify({'success': True})

@app.route('/api/stats', methods=['GET'])
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)