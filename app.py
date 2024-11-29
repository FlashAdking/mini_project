from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from flask import flash
from werkzeug.utils import secure_filename
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # Replace with a secure random key
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:mysql123@localhost/mini_project'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

session['user_id'] = user.id
session['username'] = user.username

db = SQLAlchemy(app)

# Models
class Student(db.Model):
    prn = db.Column(db.String(20), primary_key=True)
    roll_no = db.Column(db.String(10), unique=True, nullable=False)  # Unique roll number
    name = db.Column(db.String(50), nullable=False)

class Attendance(db.Model):
    prn = db.Column(db.String(20), db.ForeignKey('student.prn'), primary_key=True)
    date = db.Column(db.String(50), primary_key=True)  # Format: "YYYY-MM-DD"
    time = db.Column(db.String(10), nullable=False)  # e.g., "1:00 PM"
    student = db.relationship('Student', backref='attendances')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Hashed password for security
    mobile = db.Column(db.String(15), nullable=True)

    def set_password(self, password):
        """Generate a hashed password and store it."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Check if the entered password matches the hashed password."""
        return check_password_hash(self.password, password) 

class Student_class(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Add an auto-incrementing primary key
    name = db.Column(db.String(255), nullable=False)
    prn = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    mobile = db.Column(db.String(15), nullable=True)
    year = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    div = db.Column(db.String(1), nullable=False)
    role = db.Column(db.String(50), nullable=True)  # Make role nullable if not mandatory

# Create the database tables
with app.app_context():
    db.create_all()




@app.route('/set_session')
def set_session():
    session['user_id'] = user.id  # Store data in the session
    return redirect(url_for('get_session'))  # Redirect to another route to see session data

@app.route('/get_session')
def get_session():
    user_id = session.get('user_id')  # Retrieve data from the session
    if user_id:
        return f'User ID: {user_id}'  # Display the user ID stored in session
    return 'No user ID in session'



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:           
            flash('Please log in to view this page.', 'warning')        
            return redirect(url_for('login'))  # Redirect to login page if not logged in
        return f(*args, **kwargs)
    return decorated_function


# Routes
@app.route('/')
def home():
    return render_template('index.html')  # Public home page

@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if user exists in the database
        user = User.query.filter_by(username=username).first()  # Or use email if applicable
        
        if user and user.check_password(password):  # Assuming check_password method exists
            flash("Login successful!", "success")  # Flash success message

            return redirect(url_for('index'))  # Redirect to the dashboard (or another page)
        else:
            flash("Incorrect username or password", "danger")  
            return redirect(url_for('login'))  
    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        mobile = request.form['mobile']
        terms_accepted = request.form.get('terms')

        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        
        if existing_user:
            flash("Username or Email already exists", "danger")
            return redirect(url_for('register'))

        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        # Create a new user
        new_user = User(username=username, email=email, password=hashed_password, mobile=mobile)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('login'))  # Redirect to the login page after successful registration

    return render_template('register.html')



# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Function to validate file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_images', methods=['POST'])
def upload_images():
    # Check if both files are in the request
    if 'photos' not in request.files or 'files' not in request.files:
        return jsonify({'error': 'Both photos and files are required'}), 400

    image1 = request.files['photos']
    image2 = request.files['files']

    # Validate file types
    if not allowed_file(image1.filename) or not allowed_file(image2.filename):
        return jsonify({'error': 'Files must be in .png, .jpg, or .webp format'}), 400

    # Secure filenames
    image1_filename = secure_filename(image1.filename)
    image2_filename = secure_filename(image2.filename)

    # Create the upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Save the images
    image1_path = os.path.join(app.config['UPLOAD_FOLDER'], image1_filename)
    image2_path = os.path.join(app.config['UPLOAD_FOLDER'], image2_filename)

    try:
        image1.save(image1_path)
        image2.save(image2_path)
    except Exception as e:
        return jsonify({'error': f'Error saving files: {str(e)}'}), 500

    # URLs for the uploaded images
    image1_url = url_for('static', filename='uploads/' + image1_filename)
    image2_url = url_for('static', filename='uploads/' + image2_filename)

    # Response with the URLs
    return jsonify({
        'image1_url': image1_url,
        'image2_url': image2_url
    })


# Route for marking attendance (face detection and recognition)
@app.route('/mark_attendance', methods=['GET'])
def mark_attendance():
    # Sample logic for detecting faces from uploaded images and marking attendance
    attendance = []
    
    # Load the uploaded images (for this example, we're assuming we have image paths)
    image1_path = os.path.join(app.config['UPLOAD_FOLDER'], 'image1.jpg')
    image2_path = os.path.join(app.config['UPLOAD_FOLDER'], 'image2.jpg')

    # Load the images using OpenCV
    img1 = cv2.imread(image1_path)
    img2 = cv2.imread(image2_path)
    
    # Example: detect faces and match against known encodings
    # (Implement your actual face detection and recognition here)
    # For simplicity, this is a mock response
    attendance.append({
        'roll_number': 'A55',
        'name': 'Arav Prabhare',
        'time': '10:00 AM'
    })
    attendance.append({
        'roll_number': 'A65',
        'name': 'Gautam adnave',
        'time': '10:05 AM'
    })

    return jsonify({'attendance': attendance})

# Route for submitting the attendance
@app.route('/submit_attendance', methods=['POST'])
def submit_attendance():
    # Parse JSON data from the request
    data = request.json
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400

    attendance_list = data.get('attendance_list')
    if not attendance_list or not isinstance(attendance_list, list):
        return jsonify({'status': 'error', 'message': 'Invalid attendance list provided'}), 400

    # Process each attendance record
    errors = []
    for record in attendance_list:
        prn = record.get('prn')
        date = record.get('date')  # Format: "YYYY-MM-DD"
        time = record.get('time')  # Format: "HH:MM AM/PM"

        # Validate required fields
        if not prn or not date or not time:
            errors.append(f"Missing data for PRN: {prn}")
            continue

        # Check if the student exists
        student = Student.query.filter_by(prn=prn).first()
        if not student:
            errors.append(f"Student with PRN {prn} not found")
            continue

        # Check if attendance is already marked for the given date
        existing_attendance = Attendance.query.filter_by(prn=prn, date=date).first()
        if existing_attendance:
            errors.append(f"Attendance already marked for PRN {prn} on {date}")
            continue

        # Mark attendance
        new_attendance = Attendance(prn=prn, date=date, time=time)
        db.session.add(new_attendance)

    # Commit changes to the database
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Error saving attendance: {str(e)}'}), 500

    # Return success or partial success response
    if errors:
        return jsonify({'status': 'partial_success', 'message': 'Some records were not processed', 'errors': errors}), 207

    return jsonify({'status': 'success', 'message': 'Attendance submitted successfully'})


@app.route('/search_students', methods=['GET'])
def search_students():
    prn = request.args.get('prn')
    name = request.args.get('name')
    department = request.args.get('department')
    year = request.args.get('year')
    division = request.args.get('division')
    
    # Build a query based on the filters
    query = Student.query
    
    if prn:
        query = query.filter(Student.prn.like(f'%{prn}%'))
    if name:
        query = query.filter(Student.name.like(f'%{name}%'))
    if department:
        query = query.filter(Student.department == department)
    if year:
        query = query.filter(Student.year == year)
    if division:
        query = query.filter(Student.division == division)

    # Get filtered results
    students = query.all()

    # Prepare response data
    student_data = [{
        'name': student.name,
        'prn': student.prn,
        'email': student.email,
        'mobile': student.mobile,
        'year': student.year,
        'role': student.role
    } for student in students]

    return jsonify({'data': student_data})


@app.route('/students_list', methods=['GET'])
@login_required
def students_list():
    # Retrieve all students, or filtered ones based on query params
    students = Student.query.all()
    return render_template('students.html', students=students)


@app.route('/attendance')
@login_required
def attendance():
    return render_template('attendance.html')

@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

@app.route('/forgot_password')
@login_required
def forgot_password():
    return render_template('forgot-password.html')

@app.route('/change_password')
@login_required
def change_password():
    return render_template('change-password2.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('login'))
    # Fetch user details and render profile page
    return render_template('profile.html')

@app.route('/error-404')
def error_404():
    return render_template('error-404.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove 'user_id' from session
    flash('You have been logged out.', 'info')  # Optional: Show a message
    return redirect(url_for('login'))  # Redirect to login page


if __name__ == '__main__':
    app.run(debug=True)
