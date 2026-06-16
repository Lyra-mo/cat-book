import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from cat_book import CatBook
from datetime import datetime
from PIL import Image, ImageTk
import os

# ===== 喵喵风格配色 =====
COLORS = {
    'bg': '#FFF8F0',           # 奶油白背景
    'card': '#FFFFFF',          # 卡片白（半透明效果）
    'primary': '#FF9A76',       # 橘猫色
    'primary_light': '#FFD4B8', # 浅橘色
    'secondary': '#F5D9C7',     # 奶茶色
    'text': '#5D4037',          # 棕色文字
    'text_light': '#8D6E63',    # 浅棕色
    'pink': '#FFB5B5',          # 粉红
    'yellow': '#FFE5A3',        # 奶油黄
    'green': '#B5EAD7',         # 薄荷绿
    'shadow': '#E8DDD5',        # 阴影色
}

class XiaoMaoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🐱 小鱼干记账本")
        self.root.geometry("780x680")
        self.root.resizable(True, True)
        self.root.configure(bg=COLORS['bg'])
        
        # ===== 🖼️ 添加程序图标 =====
        try:
            self.root.iconbitmap('cat_icon.ico')
        except:
            pass
        
        # ===== 🖼️ 设置背景图 =====
        self.bg_photo = None
        self.setup_background()
        
        # 初始化数据管理
        self.book = CatBook()
        self.current_record_id = None
        
        # 设置界面
        self.setup_ui()
        self.refresh_records()
    
    def setup_background(self):
        """设置背景图（带自动适应窗口）"""
        try:
            # 获取窗口大小
            width = self.root.winfo_width() or 780
            height = self.root.winfo_height() or 680
            
            # 加载并调整图片大小
            bg_image = Image.open('bg_pattern.png')
            bg_image = bg_image.resize((width, height), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(bg_image)
            
            # 创建背景标签
            self.bg_label = tk.Label(self.root, image=self.bg_photo)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            
            # 把背景标签放到最底层
            self.bg_label.lower()
            
        except Exception as e:
            print(f"💡 背景图加载失败（不影响使用）: {e}")
            self.root.configure(bg=COLORS['bg'])
    
    def on_resize(self, event):
        """窗口大小变化时重新调整背景图"""
        try:
            if hasattr(self, 'bg_label') and self.bg_label:
                # 重新加载并调整图片大小
                bg_image = Image.open('bg_pattern.png')
                bg_image = bg_image.resize((event.width, event.height), Image.Resampling.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(bg_image)
                self.bg_label.config(image=self.bg_photo)
        except:
            pass
    
    def setup_ui(self):
        """设置界面（使用白色卡片浮在背景上）"""
        
        # ===== 顶部标题 =====
        header_frame = tk.Frame(self.root, bg=COLORS['bg'], height=90)
        header_frame.pack(fill='x', pady=(10, 5))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, 
            text="🐱 小鱼干记账本", 
            font=("微软雅黑", 22, "bold"), 
            fg=COLORS['primary'],
            bg=COLORS['bg']
        )
        title_label.pack(pady=(5, 0))
        
        sub_label = tk.Label(
            header_frame,
            text="🌸 今天也要好好记账哦 🌸",
            font=("微软雅黑", 10),
            fg=COLORS['text_light'],
            bg=COLORS['bg']
        )
        sub_label.pack()
        
        # ===== 输入卡片 =====
        input_card = tk.Frame(
            self.root, 
            bg=COLORS['card'],
            relief='flat',
            highlightthickness=1,
            highlightcolor=COLORS['shadow']
        )
        input_card.pack(padx=20, pady=8, fill='x')
        
        card_title = tk.Label(
            input_card,
            text="✏️ 记一笔",
            font=("微软雅黑", 12, "bold"),
            fg=COLORS['text'],
            bg=COLORS['card']
        )
        card_title.pack(anchor='w', padx=15, pady=(10, 5))
        
        # 输入行1
        row1 = tk.Frame(input_card, bg=COLORS['card'])
        row1.pack(fill='x', padx=15, pady=3)
        
        tk.Label(row1, text="📅", font=("微软雅黑", 12), bg=COLORS['card']).pack(side='left', padx=(0, 3))
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = tk.Entry(
            row1, textvariable=self.date_var, width=12,
            font=("微软雅黑", 10), relief='flat',
            bg=COLORS['bg'], fg=COLORS['text']
        )
        date_entry.pack(side='left', padx=(0, 15))
        
        tk.Label(row1, text="📂", font=("微软雅黑", 12), bg=COLORS['card']).pack(side='left', padx=(0, 3))
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(
            row1, textvariable=self.category_var,
            values=["🍜 餐饮", "🚌 交通", "🛍️ 购物", "💰 工资", "🎮 娱乐", "🏠 居家", "其他"],
            width=10, font=("微软雅黑", 10)
        )
        self.category_combo.pack(side='left', padx=(0, 15))
        
        tk.Label(row1, text="💸", font=("微软雅黑", 12), bg=COLORS['card']).pack(side='left', padx=(0, 3))
        self.amount_var = tk.StringVar()
        amount_entry = tk.Entry(
            row1, textvariable=self.amount_var, width=10,
            font=("微软雅黑", 10), relief='flat',
            bg=COLORS['bg'], fg=COLORS['text']
        )
        amount_entry.pack(side='left')
        
        # 输入行2
        row2 = tk.Frame(input_card, bg=COLORS['card'])
        row2.pack(fill='x', padx=15, pady=5)
        
        tk.Label(row2, text="📝", font=("微软雅黑", 12), bg=COLORS['card']).pack(side='left', padx=(0, 3))
        self.note_var = tk.StringVar()
        note_entry = tk.Entry(
            row2, textvariable=self.note_var, width=20,
            font=("微软雅黑", 10), relief='flat',
            bg=COLORS['bg'], fg=COLORS['text']
        )
        note_entry.pack(side='left', padx=(0, 15))
        
        tk.Label(row2, text="类型:", font=("微软雅黑", 10), bg=COLORS['card'], fg=COLORS['text_light']).pack(side='left', padx=(0, 5))
        self.type_var = tk.StringVar(value="支出")
        type_frame = tk.Frame(row2, bg=COLORS['card'])
        type_frame.pack(side='left', padx=(0, 10))
        
        expense_btn = tk.Label(
            type_frame, text="💸 支出",
            font=("微软雅黑", 9),
            bg=COLORS['primary_light'] if self.type_var.get() == "支出" else COLORS['bg'],
            fg=COLORS['text'], relief='flat', padx=8, pady=2
        )
        expense_btn.pack(side='left', padx=2)
        expense_btn.bind('<Button-1>', lambda e: self.set_type("支出", expense_btn, income_btn))
        
        income_btn = tk.Label(
            type_frame, text="💎 收入",
            font=("微软雅黑", 9),
            bg=COLORS['green'] if self.type_var.get() == "收入" else COLORS['bg'],
            fg=COLORS['text'], relief='flat', padx=8, pady=2
        )
        income_btn.pack(side='left', padx=2)
        income_btn.bind('<Button-1>', lambda e: self.set_type("收入", expense_btn, income_btn))
        
        btn_frame = tk.Frame(row2, bg=COLORS['card'])
        btn_frame.pack(side='right')
        
        self.add_btn = tk.Button(
            btn_frame, text="🎀 记好了！",
            font=("微软雅黑", 10, "bold"),
            bg=COLORS['primary'], fg='white',
            relief='flat', padx=15, pady=4,
            command=self.add_record, cursor='hand2'
        )
        self.add_btn.pack(side='left', padx=2)
        
        self.update_btn = tk.Button(
            btn_frame, text="✏️ 修改",
            font=("微软雅黑", 10, "bold"),
            bg=COLORS['yellow'], fg=COLORS['text'],
            relief='flat', padx=15, pady=4,
            command=self.update_record, cursor='hand2',
            state='disabled'
        )
        self.update_btn.pack(side='left', padx=2)
        
        self.cancel_btn = tk.Button(
            btn_frame, text="❌ 取消",
            font=("微软雅黑", 9),
            bg=COLORS['shadow'], fg=COLORS['text'],
            relief='flat', padx=12, pady=4,
            command=self.cancel_edit, cursor='hand2',
            state='disabled'
        )
        self.cancel_btn.pack(side='left', padx=2)
        
        # ===== 搜索栏 =====
        search_frame = tk.Frame(self.root, bg=COLORS['bg'])
        search_frame.pack(padx=20, pady=5, fill='x')
        
        tk.Label(search_frame, text="🔍", font=("微软雅黑", 12), bg=COLORS['bg']).pack(side='left', padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame, textvariable=self.search_var, width=20,
            font=("微软雅黑", 10), relief='flat',
            bg='white', fg=COLORS['text']
        )
        search_entry.pack(side='left', padx=(0, 10))
        
        tk.Button(
            search_frame, text="🔎 搜索",
            font=("微软雅黑", 9), bg=COLORS['secondary'], fg=COLORS['text'],
            relief='flat', padx=12, pady=3,
            command=self.search_records, cursor='hand2'
        ).pack(side='left', padx=2)
        
        tk.Button(
            search_frame, text="📋 全部",
            font=("微软雅黑", 9), bg='white', fg=COLORS['text'],
            relief='flat', padx=12, pady=3,
            command=self.refresh_records, cursor='hand2'
        ).pack(side='left', padx=2)
        
        # ===== 记录列表卡片 =====
        list_card = tk.Frame(
            self.root, bg=COLORS['card'],
            relief='flat', highlightthickness=1,
            highlightcolor=COLORS['shadow']
        )
        list_card.pack(padx=20, pady=8, fill='both', expand=True)
        
        list_title = tk.Label(
            list_card, text="📒 记账本",
            font=("微软雅黑", 12, "bold"),
            fg=COLORS['text'], bg=COLORS['card']
        )
        list_title.pack(anchor='w', padx=15, pady=(10, 5))
        
        tree_frame = tk.Frame(list_card, bg=COLORS['card'])
        tree_frame.pack(padx=15, pady=(0, 10), fill='both', expand=True)
        
        columns = ('日期', '类别', '金额', '备注')
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show='headings', height=12
        )
        
        col_config = {'日期': 100, '类别': 100, '金额': 90, '备注': 250}
        for col, width in col_config.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor='center')
        
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.tree.bind('<Double-Button-1>', self.on_tree_double_click)
        self.tree.bind('<Delete>', self.on_delete_key)
        
        # ===== 底部统计栏 =====
        bottom_frame = tk.Frame(self.root, bg=COLORS['bg'])
        bottom_frame.pack(padx=20, pady=(5, 15), fill='x')
        
        self.stats_label = tk.Label(
            bottom_frame,
            text="💰 本月收入: ¥0  支出: ¥0  结余: ¥0",
            font=("微软雅黑", 11),
            fg=COLORS['text'], bg=COLORS['bg']
        )
        self.stats_label.pack(side='left')
        
        btn_right = tk.Frame(bottom_frame, bg=COLORS['bg'])
        btn_right.pack(side='right')
        
        tk.Button(
            btn_right, text="📊 统计",
            font=("微软雅黑", 9), bg=COLORS['yellow'], fg=COLORS['text'],
            relief='flat', padx=10, pady=3,
            command=self.show_monthly_chart, cursor='hand2'
        ).pack(side='left', padx=2)
        
        tk.Button(
            btn_right, text="📈 趋势",
            font=("微软雅黑", 9), bg=COLORS['green'], fg=COLORS['text'],
            relief='flat', padx=10, pady=3,
            command=self.show_trend_chart, cursor='hand2'
        ).pack(side='left', padx=2)
        
        tk.Button(
            btn_right, text="📂 分类",
            font=("微软雅黑", 9), bg=COLORS['secondary'], fg=COLORS['text'],
            relief='flat', padx=10, pady=3,
            command=self.show_category_stats, cursor='hand2'
        ).pack(side='left', padx=2)
        
        tk.Button(
            btn_right, text="🗑️ 删除",
            font=("微软雅黑", 9), bg=COLORS['pink'], fg=COLORS['text'],
            relief='flat', padx=10, pady=3,
            command=self.delete_selected, cursor='hand2'
        ).pack(side='left', padx=2)
        
        # 绑定窗口大小变化事件
        self.root.bind('<Configure>', self.on_resize)
    
    def set_type(self, type_val, expense_btn, income_btn):
        """切换收支类型"""
        self.type_var.set(type_val)
        if type_val == "支出":
            expense_btn.config(bg=COLORS['primary_light'])
            income_btn.config(bg=COLORS['bg'])
        else:
            expense_btn.config(bg=COLORS['bg'])
            income_btn.config(bg=COLORS['green'])
    
    # ===== 以下是功能方法 =====
    
    def add_record(self):
        try:
            date = self.date_var.get()
            category = self.category_var.get()
            amount = float(self.amount_var.get())
            note = self.note_var.get().strip()
            type_ = self.type_var.get()
            
            if not category:
                messagebox.showwarning("🐱 喵~", "请选择类别哦")
                return
            if amount <= 0:
                messagebox.showwarning("🐱 喵~", "金额要大于0哦")
                return
            
            self.book.add_record(date, category, amount, note, type_)
            messagebox.showinfo("🎀 成功！", f"✨ 记录已保存~\n{category} {type_}: ¥{amount:.2f}")
            self.refresh_records()
            self.clear_inputs()
        except ValueError:
            messagebox.showerror("😿 哎呀", "请输入正确的金额数字~")
    
    def update_record(self):
        if not self.current_record_id:
            return
        
        try:
            date = self.date_var.get()
            category = self.category_var.get()
            amount = float(self.amount_var.get())
            note = self.note_var.get().strip()
            type_ = self.type_var.get()
            
            if not category:
                messagebox.showwarning("🐱 喵~", "请选择类别哦")
                return
            
            self.book.update_record(self.current_record_id, 
                                   date=date, category=category, 
                                   amount=amount, note=note, type=type_)
            messagebox.showinfo("🎀 成功！", "✅ 记录已更新~")
            self.refresh_records()
            self.clear_inputs()
            self.cancel_edit()
        except ValueError:
            messagebox.showerror("😿 哎呀", "请输入正确的金额数字~")
    
    def delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("🐱 喵~", "先选中要删除的记录哦")
            return
        
        if not messagebox.askyesno("😿 确认", "确定要删掉这条记录吗？"):
            return
        
        for item in selection:
            values = self.tree.item(item, 'values')
            date = values[0]
            category = values[1]
            amount = float(values[2].replace('¥', ''))
            for r in self.book.records:
                if r['date'] == date and r['category'] == category and abs(r['amount'] - amount) < 0.01:
                    self.book.delete_record(r['id'])
                    break
        
        self.refresh_records()
        messagebox.showinfo("🎀 成功！", f"✨ 已删除 {len(selection)} 条记录")
    
    def on_delete_key(self, event):
        self.delete_selected()
    
    def on_tree_double_click(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        date = values[0]
        category = values[1]
        amount = float(values[2].replace('¥', ''))
        note = values[3]
        
        for r in self.book.records:
            if r['date'] == date and r['category'] == category and abs(r['amount'] - amount) < 0.01:
                self.current_record_id = r['id']
                self.date_var.set(r['date'])
                self.category_var.set(r['category'])
                self.amount_var.set(str(r['amount']))
                self.note_var.set(r['note'])
                self.type_var.set(r.get('type', '支出'))
                
                self.add_btn.config(state='disabled')
                self.update_btn.config(state='normal')
                self.cancel_btn.config(state='normal')
                break
    
    def cancel_edit(self):
        self.current_record_id = None
        self.clear_inputs()
        self.add_btn.config(state='normal')
        self.update_btn.config(state='disabled')
        self.cancel_btn.config(state='disabled')
    
    def clear_inputs(self):
        self.amount_var.set("")
        self.note_var.set("")
        self.category_var.set("")
        self.type_var.set("支出")
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
    
    def search_records(self):
        keyword = self.search_var.get().strip()
        if not keyword:
            self.refresh_records()
            return
        
        results = self.book.search_records(keyword=keyword)
        self.display_records(results)
    
    def display_records(self, records):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for r in records:
            amount_str = f"¥{r['amount']:.2f}"
            self.tree.insert('', 'end', values=(
                r['date'], r['category'], amount_str, r['note']
            ))
    
    def refresh_records(self):
        self.display_records(self.book.records)
        self.update_stats()
        self.search_var.set("")
    
    def update_stats(self):
        now = datetime.now()
        income, expense = self.book.get_monthly_summary(now.year, now.month)
        balance = income - expense
        self.stats_label.config(
            text=f"💰 本月收入: ¥{income:.0f}  支出: ¥{expense:.0f}  结余: ¥{balance:.0f}"
        )
    
    def show_category_stats(self):
        now = datetime.now()
        categories = self.book.get_category_summary(now.year, now.month)
        
        if not categories:
            messagebox.showinfo("🐱 喵~", "本月还没有支出记录哦")
            return
        
        stat_window = tk.Toplevel(self.root)
        stat_window.title("📊 分类统计")
        stat_window.geometry("350x300")
        stat_window.configure(bg=COLORS['bg'])
        
        tk.Label(stat_window, text=f"🐱 {now.year}年{now.month}月 支出分类", 
                font=("微软雅黑", 12, "bold"), bg=COLORS['bg'], fg=COLORS['text']).pack(pady=10)
        
        text_area = scrolledtext.ScrolledText(stat_window, width=40, height=15)
        text_area.pack(padx=10, pady=5, fill='both', expand=True)
        
        total = sum(categories.values())
        output = "类别\t\t金额\t占比\n"
        output += "-" * 30 + "\n"
        for cat, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            percent = (amount / total * 100) if total > 0 else 0
            output += f"{cat}\t\t¥{amount:.2f}\t{percent:.1f}%\n"
        output += "-" * 30 + "\n"
        output += f"总计\t\t¥{total:.2f}\t100.0%"
        
        text_area.insert('1.0', output)
        text_area.config(state='disabled')
        
        tk.Button(stat_window, text="✨ 关闭", 
                 font=("微软雅黑", 9), bg=COLORS['primary'], fg='white',
                 relief='flat', padx=20, pady=5,
                 command=stat_window.destroy, cursor='hand2').pack(pady=10)
    
    # ===== 图表功能 =====
    
    def show_monthly_chart(self):
        try:
            import matplotlib.pyplot as plt
            from matplotlib import rcParams
            
            rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
            rcParams['axes.unicode_minus'] = False
            
            now = datetime.now()
            categories = self.book.get_category_data(now.year, now.month)
            
            if not categories:
                messagebox.showinfo("🐱 喵~", "本月还没有支出记录哦")
                return
            
            labels = list(categories.keys())
            values = list(categories.values())
            
            fig, ax = plt.subplots(figsize=(8, 6))
            fig.patch.set_facecolor('#FFF8F0')
            ax.set_facecolor('#FFF8F0')
            
            colors = ['#FF9A76', '#FFD4B8', '#FFE5A3', '#B5EAD7', '#FFB5B5', 
                     '#A8D8EA', '#AA96DA', '#FCBAD3', '#D4F0C0', '#FFC8DD']
            
            wedges, texts, autotexts = ax.pie(
                values, labels=labels, autopct='%1.1f%%',
                colors=colors[:len(labels)], startangle=90,
                textprops={'fontsize': 12}
            )
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            ax.set_title(f'🐱 {now.year}年{now.month}月 支出小统计', 
                        fontsize=16, fontweight='bold', pad=20, color='#5D4037')
            
            total = sum(values)
            ax.text(0, -1.2, f'💰 总支出: ¥{total:.2f}', 
                   fontsize=14, ha='center', color='#FF9A76')
            
            plt.tight_layout()
            plt.show()
            
        except ImportError:
            messagebox.showerror("😿 哎呀", "先安装 matplotlib 哦:\npip install matplotlib")
        except Exception as e:
            messagebox.showerror("😿 哎呀", f"图表生成失败:\n{str(e)}")
    
    def show_trend_chart(self):
        try:
            import matplotlib.pyplot as plt
            from matplotlib import rcParams
            
            rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
            rcParams['axes.unicode_minus'] = False
            
            trend_data = self.book.get_monthly_trend(datetime.now().year, months=6)
            
            if not trend_data or all(d['expense'] == 0 and d['income'] == 0 for d in trend_data):
                messagebox.showinfo("🐱 喵~", "最近6个月还没有数据哦")
                return
            
            months = [d['month'] for d in trend_data]
            expenses = [d['expense'] for d in trend_data]
            incomes = [d['income'] for d in trend_data]
            balances = [d['balance'] for d in trend_data]
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
            fig.patch.set_facecolor('#FFF8F0')
            
            x = range(len(months))
            width = 0.35
            
            bars1 = ax1.bar([i - width/2 for i in x], expenses, width, 
                           label='支出', color='#FF9A76', alpha=0.8)
            bars2 = ax1.bar([i + width/2 for i in x], incomes, width, 
                           label='收入', color='#B5EAD7', alpha=0.8)
            
            ax1.set_xlabel('月份', fontsize=12)
            ax1.set_ylabel('金额 (¥)', fontsize=12)
            ax1.set_title('📈 收支趋势', fontsize=14, fontweight='bold')
            ax1.set_xticks(x)
            ax1.set_xticklabels(months, rotation=45)
            ax1.legend()
            ax1.grid(axis='y', alpha=0.3)
            ax1.set_facecolor('#FFF8F0')
            
            for bar in bars1:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                            f'¥{height:.0f}', ha='center', va='bottom', fontsize=8)
            for bar in bars2:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                            f'¥{height:.0f}', ha='center', va='bottom', fontsize=8)
            
            colors = ['#B5EAD7' if b >= 0 else '#FF9A76' for b in balances]
            bars3 = ax2.bar(months, balances, color=colors, alpha=0.7)
            
            ax2.set_xlabel('月份', fontsize=12)
            ax2.set_ylabel('结余 (¥)', fontsize=12)
            ax2.set_title('📊 结余趋势', fontsize=14, fontweight='bold')
            ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
            ax2.grid(axis='y', alpha=0.3)
            ax2.set_facecolor('#FFF8F0')
            
            for bar in bars3:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'¥{height:.0f}', ha='center', 
                        va='bottom' if height >= 0 else 'top', fontsize=9)
            
            plt.tight_layout()
            plt.show()
            
        except ImportError:
            messagebox.showerror("😿 哎呀", "先安装 matplotlib 哦:\npip install matplotlib")
        except Exception as e:
            messagebox.showerror("😿 哎呀", f"图表生成失败:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = XiaoMaoGUI(root)
    root.mainloop()