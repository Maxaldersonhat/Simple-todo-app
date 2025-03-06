from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask import flash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)
    urgency = db.Column(db.Integer, nullable=False, default=2)
    completion_date = db.Column(db.DateTime, nullable=True)

    @property
    def urgency_text(self):
        if self.urgency == 1:
            return "Low"
        elif self.urgency == 2:
            return "Medium"
        elif self.urgency == 3:
            return "High"
        else:
            return "Unknown"

@app.route('/')
def index():
    tasks = Todo.query.filter_by(completed=False).order_by(Todo.date_created).all()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add():
    task_content = request.form['content'].strip()   
    urgency = int(request.form.get('urgency', 2))
    completion_date = request.form.get('completion_date', None)
    try:
        if not task_content: 
            flash ('Task cannot be empty, please fill the task field')
        if completion_date: 
            completion_date = datetime.strptime(completion_date, '%Y-%m-%d')
        
        new_task = Todo(content=task_content, urgency=urgency, completion_date=completion_date)
        db.session.add(new_task)
        db.session.commit()
        return redirect('/')
    
    except ValueError as e: 
        return str(e)
    
    except Exception as e:  
     return ('There was an issue adding your task, Make sure to fill all the fields')

@app.route('/delete/<int:id>', methods=['GET','POST'])
def delete_task(id):
    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        flash ('There was a problem deleting that task')
    
@app.route('/update/<int:id>', methods=['GET','POST'])
def update_task(id):
    task = Todo.query.get_or_404(id)
    
    if request.method == 'POST':
        task.content = request.form['content']
        
        try:
            db.session.commit()
            return redirect('/')
        except:
            flash ('There was an issue updating your task')
    else:
        return render_template('update.html', task=task)
    
@app.route('/complete/<int:id>', methods=['GET','POST'])
def complete_task(id):
    task = Todo.query.get_or_404(id)
    task.completed = True
    try:
        db.session.commit()
        return redirect(url_for('completed_tasks'))
    except:
        flash ('There was an issue completing your task')
        return redirect(url_for('index'))


@app.route('/search', methods=['GET'])
def search():
    search_query = request.args.get('query', '').strip()
    urgency_filter = request.args.get('urgency', '').strip()
    date_filter = request.args.get('date_filter', '').strip()

    tasks = [] 

    if search_query or urgency_filter or date_filter:

        tasks = Todo.query

        # Apply text search
        if search_query:
            tasks = tasks.filter(Todo.content.contains(search_query))

        # Apply urgency filter (matching words, not numbers)
        if urgency_filter:
            tasks = tasks.filter(Todo.urgency.ilike(urgency_filter))  # Case-insensitive search

        # Apply date filter
        today = datetime.today().date()
        if date_filter == 'today':
            tasks = tasks.filter(db.func.date(Todo.completion_date) == today)
        elif date_filter == 'tomorrow':
            tasks = tasks.filter(db.func.date(Todo.completion_date) == today + timedelta(days=1))
        elif date_filter == 'this_week':
            next_week = today + timedelta(days=7)
            tasks = tasks.filter(
                db.func.date(Todo.completion_date) >= today,
                db.func.date(Todo.completion_date) <= next_week
            )

        tasks = tasks.all()  # Fetch filtered tasks

    return render_template('search.html', tasks=tasks, search_query=search_query, urgency_filter=urgency_filter, date_filter=date_filter)
   
@app.route('/completed')
def completed_tasks():
    tasks = Todo.query.filter_by(completed=True).order_by(Todo.date_created).all()
    return render_template('completed.html', tasks=tasks)



if __name__ == '__main__':
    with app.app_context():
       db.create_all()
    app.run(debug=True, use_reloader=True)