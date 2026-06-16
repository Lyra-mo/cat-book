import json
from datetime import datetime
import os

class CatBook:
    def __init__(self, data_file='data.json'):
        self.data_file = data_file
        self.records = []
        self.load_data()
    
    def load_data(self):
        """加载数据，如果文件不存在则创建空数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 兼容旧格式：如果是列表则直接使用
                if isinstance(data, list):
                    self.records = data
                else:
                    self.records = data.get('records', [])
        except (FileNotFoundError, json.JSONDecodeError):
            self.records = []
            self.save_data()
    
    def save_data(self):
        """保存数据到文件"""
        # 数据格式：{"records": [...], "last_updated": "2026-06-16 17:00:00"}
        data = {
            'records': self.records,
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_record(self, date, category, amount, note, type_='支出'):
        """添加一条记账记录"""
        # 自动生成ID（基于现有记录数量+1）
        record_id = max([r.get('id', 0) for r in self.records], default=0) + 1
        
        record = {
            'id': record_id,
            'date': date,
            'category': category,
            'amount': float(amount),
            'note': note,
            'type': type_,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.records.append(record)
        self.save_data()
        return record
    
    def delete_record(self, record_id):
        """删除指定ID的记录"""
        self.records = [r for r in self.records if r.get('id') != record_id]
        self.save_data()
        return True
    
    def get_record(self, record_id):
        """获取单条记录"""
        for r in self.records:
            if r.get('id') == record_id:
                return r
        return None
    
    def update_record(self, record_id, **kwargs):
        """更新记录"""
        record = self.get_record(record_id)
        if record:
            for key, value in kwargs.items():
                if key in ['date', 'category', 'amount', 'note', 'type']:
                    if key == 'amount':
                        value = float(value)
                    record[key] = value
            self.save_data()
            return True
        return False
    
    def get_monthly_summary(self, year, month):
        """获取月度汇总：收入、支出"""
        total_income = 0.0
        total_expense = 0.0
        month_str = f"{year}-{month:02d}"
        
        for r in self.records:
            if r['date'].startswith(month_str):
                if r.get('type', '支出') == '收入':
                    total_income += r['amount']
                else:
                    total_expense += r['amount']
        
        return total_income, total_expense
    
    def get_category_summary(self, year, month):
        """获取月度分类汇总"""
        month_str = f"{year}-{month:02d}"
        category_totals = {}
        
        for r in self.records:
            if r['date'].startswith(month_str) and r.get('type', '支出') == '支出':
                cat = r['category']
                category_totals[cat] = category_totals.get(cat, 0.0) + r['amount']
        
        return category_totals
    
    def get_all_categories(self):
        """获取所有已使用的类别"""
        categories = set()
        for r in self.records:
            categories.add(r['category'])
        return sorted(list(categories))
    
    def search_records(self, keyword='', category='', start_date='', end_date=''):
        """搜索记录"""
        results = self.records.copy()
        
        if keyword:
            results = [r for r in results if keyword.lower() in r['note'].lower()]
        if category:
            results = [r for r in results if r['category'] == category]
        if start_date:
            results = [r for r in results if r['date'] >= start_date]
        if end_date:
            results = [r for r in results if r['date'] <= end_date]
        
        return results
    def get_monthly_trend(self, year, months=6):
        """获取最近N个月的收支趋势"""
        trend_data = []
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        for i in range(months - 1, -1, -1):
            # 计算月份
            m = current_month - i
            y = current_year
            if m <= 0:
                m += 12
                y -= 1
            
            month_str = f"{y}-{m:02d}"
            income, expense = self.get_monthly_summary(y, m)
            
            trend_data.append({
                'month': month_str,
                'income': income,
                'expense': expense,
                'balance': income - expense
            })
        
        return trend_data
    
    def get_category_data(self, year, month):
        """获取分类数据（用于饼图）"""
        return self.get_category_summary(year, month)
    
    def get_all_months(self):
        """获取所有有数据的月份"""
        months = set()
        for r in self.records:
            if r.get('date'):
                months.add(r['date'][:7])  # 取 YYYY-MM
        return sorted(list(months))