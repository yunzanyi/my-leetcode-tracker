from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import plotly.express as px
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stuleetcode2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///leetcode.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    tags = db.Column(db.String(200))
    description = db.Column(db.Text)
    code = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    time_spent = db.Column(db.Integer, nullable=False)


with app.app_context():
    db.create_all()


@app.route('/')
def index():
    problems = Problem.query.order_by(Problem.date.desc()).all()
    if not problems:
        return render_template('index.html', problems=[], total=0, easy=0, medium=0, hard=0)

    df = pd.DataFrame([{
        '题号': p.num, '标题': p.title, '难度': p.difficulty,
        '标签': p.tags or '', '完成日期': p.date, '耗时': p.time_spent
    } for p in problems])

    total = len(df)
    easy = len(df[df['难度'] == 'Easy'])
    medium = len(df[df['难度'] == 'Medium'])
    hard = len(df[df['难度'] == 'Hard'])

    return render_template('index.html', problems=problems, total=total, easy=easy, medium=medium, hard=hard)


@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        new_problem = Problem(
            num=request.form['num'],
            title=request.form['title'],
            difficulty=request.form['difficulty'],
            tags=request.form['tags'],
            description=request.form.get('description', ''),
            code=request.form.get('code', ''),
            date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
            time_spent=int(request.form['time_spent'])
        )
        db.session.add(new_problem)
        db.session.commit()
        flash('✅ 添加成功！', 'success')
        return redirect(url_for('index'))

    today = datetime.today().strftime('%Y-%m-%d')
    return render_template('add.html', today=today, problem=None, edit=False)


@app.route('/edit/<int:pid>', methods=['GET', 'POST'])
def edit(pid):
    problem = Problem.query.get_or_404(pid)
    
    if request.method == 'POST':
        # 直接修改对象属性
        problem.title = request.form['title']
        problem.difficulty = request.form['difficulty']
        problem.tags = request.form['tags']
        problem.description = request.form.get('description', '')
        problem.code = request.form.get('code', '')
        problem.time_spent = int(request.form['time_spent'])
        # 注意：date 通常不修改，如果需要修改可以加上
        
        db.session.commit()   # 确保提交
        flash('✅ 修改成功！', 'success')
        return redirect(url_for('index'))
    
    # GET 请求：显示编辑表单（预填充数据）
    return render_template('add.html', 
                         today=problem.date.strftime('%Y-%m-%d'), 
                         problem=problem, 
                         edit=True)
@app.route('/delete/<int:pid>')
def delete(pid):
    problem = Problem.query.get_or_404(pid)
    db.session.delete(problem)
    db.session.commit()
    flash('🗑️ 删除成功！', 'success')
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    problems = Problem.query.all()
    if not problems:
        return render_template('dashboard.html', pie_json=None, bar_json=None)

    df = pd.DataFrame([{'难度': p.difficulty, '完成日期': p.date} for p in problems])
    pie_fig = px.pie(df, names='难度', title='难度分布')
    bar_fig = px.bar(df.groupby('完成日期').size().reset_index(name='数量'), x='完成日期', y='数量',
                     title='每日刷题趋势')

    return render_template('dashboard.html',
                           pie_json=pie_fig.to_json(),
                           bar_json=bar_fig.to_json())


if __name__ == '__main__':
    app.run(debug=True)
