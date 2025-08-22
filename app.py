from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from forms import StudentForm, LoginForm, RegistrationForm
from models import db, User, Student

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home / Index
@app.route('/')
@login_required
def index():
    students = Student.query.all()
    return render_template('index.html', students=students)

# Add student
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('index'))

    form = StudentForm()
    if form.validate_on_submit():
        student = Student(
            name=form.name.data,
            age=form.age.data,
            student_class=form.student_class.data,
            roll_number=form.roll_number.data,
            email=form.email.data
        )
        db.session.add(student)
        db.session.commit()
        flash("Student added successfully!", "success")
        return redirect(url_for('index'))
    return render_template('add_student.html', form=form)

# Edit student
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('index'))

    student = Student.query.get_or_404(id)
    form = StudentForm(obj=student)
    if form.validate_on_submit():
        form.populate_obj(student)
        db.session.commit()
        flash("Student updated successfully!", "success")
        return redirect(url_for('index'))
    return render_template('edit_student.html', form=form, student=student)

# Delete student
@app.route('/delete/<int:id>')
@login_required
def delete_student(id):
    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('index'))

    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash("Student deleted successfully!", "danger")
    return redirect(url_for('index'))

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for('index'))
        flash("Invalid username or password!", "danger")
    return render_template('login.html', form=form)

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash("Username already exists!", "danger")
            return redirect(url_for('register'))
        hashed = generate_password_hash(form.password.data, method='sha256')
        user = User(username=form.username.data, password=hashed, role=form.role.data)
        db.session.add(user)
        db.session.commit()
        flash("User registered successfully!", "success")
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Dashboard (Admin analytics)
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('index'))

    students = Student.query.all()
    classes = list(set([s.student_class for s in students]))
    counts = [len([s for s in students if s.student_class==c]) for c in classes]
    return render_template('dashboard.html', students=students, classes=classes, counts=counts)

# Run App
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Default admin
        if not User.query.filter_by(username='admin').first():
            hashed = generate_password_hash('admin123', method='sha256')
            admin_user = User(username='admin', password=hashed, role='admin')
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True)
