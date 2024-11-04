from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from docx import Document
import fitz  # PyMuPDF
import nltk

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Predefined skills and MCQs
skills = {
    'Python': [
        ("What is the output of print(2 ** 3)?", "8", ["8", "6", "9", "10"]),
        ("What data type is the variable x in x = (1, 2, 3)?", "tuple", ["list", "tuple", "dict", "set"]),
        ("Which of the following is not a valid variable name?", "2var", ["var2", "2var", "_var", "var_2"]),
        ("What keyword is used to define a function in Python?", "def", ["function", "define", "def", "func"]),
        ("Which of the following is a Python tuple?", "()", ["[]", "{}", "()", "<>"])
    ],
    'Java': [
        ("Which keyword is used to define a class in Java?", "class", ["class", "def", "function", "object"]),
        ("What is the default value of a boolean variable in Java?", "false", ["true", "false", "1", "0"]),
        ("Which of the following is not a Java keyword?", "object", ["class", "object", "interface", "extends"]),
        ("What is the entry point of a Java application?", "main", ["start", "main", "init", "run"]),
        ("Which of these is a Java framework?", "Spring", ["Spring", "Django", "Flask", "Ruby on Rails"])
    ],
    'SQL': [
        ("What is the command to select all records from a table?", "SELECT *", ["SELECT *", "GET ALL", "SHOW", "FETCH"]),
        ("Which SQL statement is used to update data in a database?", "UPDATE", ["UPDATE", "MODIFY", "SET", "CHANGE"]),
        ("What does SQL stand for?", "Structured Query Language", ["Structured Query Language", "Simple Query Language", "Structured Question Language", "None of the above"]),
        ("Which command is used to delete data in SQL?", "DELETE", ["DELETE", "DROP", "REMOVE", "CLEAR"]),
        ("What keyword is used to filter records?", "WHERE", ["FILTER", "WHERE", "HAVING", "ORDER BY"])
    ],
    'JavaScript': [
        ("Which symbol is used for comments in JavaScript?", "//", ["#", "//", "/*", "<!--"]),
        ("What does DOM stand for?", "Document Object Model", ["Data Object Model", "Document Object Model", "Document Orientation Model", "Data Orientation Model"]),
        ("Which of the following is a JavaScript data type?", "Undefined", ["String", "Boolean", "Undefined", "All of the above"]),
        ("Which method is used to write HTML output in JavaScript?", "document.write()", ["document.output()", "document.write()", "write.document()", "output.document()"]),
        ("How do you create a function in JavaScript?", "function myFunction()", ["function myFunction()", "function:myFunction()", "myFunction()", "create myFunction()"])
    ],
    'HTML': [
        ("What does HTML stand for?", "HyperText Markup Language", ["HyperText Markup Language", "HyperText Multiple Language", "HighText Markup Language", "None of the above"]),
        ("Which HTML tag is used to define an internal style sheet?", "<style>", ["<style>", "<css>", "<script>", "<stylesheet>"]),
        ("Which attribute is used to define the inline styles?", "style", ["style", "class", "font", "styles"]),
        ("Which HTML tag is used to define an unordered list?", "<ul>", ["<ol>", "<li>", "<ul>", "<list>"]),
        ("What is the correct HTML element for the largest heading?", "<h1>", ["<h1>", "<heading>", "<h6>", "<h5>"])
    ],
    'CSS': [
        ("What does CSS stand for?", "Cascading Style Sheets", ["Creative Style Sheets", "Cascading Style Sheets", "Colorful Style Sheets", "Computer Style Sheets"]),
        ("Which HTML attribute is used to define inline styles?", "style", ["styles", "style", "font", "class"]),
        ("What is the correct CSS syntax to change the text color of an element?", "element { color: red; }", ["element { text-color: red; }", "element { color: red; }", "{color: red;}", "element:color(red);"]),
        ("Which property is used to change the font of an element in CSS?", "font-family", ["font-family", "font-style", "text-font", "text-style"]),
        ("How do you add a comment in CSS?", "/* Comment */", ["// Comment", "<!-- Comment -->", "/* Comment */", "## Comment"])
    ],
    'PHP': [
        ("What does PHP stand for?", "Hypertext Preprocessor", ["Personal Home Page", "Hypertext Preprocessor", "Private Home Page", "Preprocessor Home Page"]),
        ("Which symbol is used to end a statement in PHP?", ";", [".", ";", ":", ","]),
        ("Which function is used to include a file in PHP?", "include()", ["require()", "include()", "require_once()", "file()"]),
        ("How do you create an array in PHP?", "$array = array()", ["$array = array()", "array[]", "array = {}", "array[] = {}"]),
        ("Which PHP function is used to get the length of a string?", "strlen()", ["length()", "strlen()", "getLength()", "count()"])
    ]
}

# Function to extract text from DOCX files
def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return '\n'.join([para.text for para in doc.paragraphs])

# Function to extract text from PDF files
def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

# Function to analyze the resume for skills
def analyze_resume_for_skills(resume_text):
    found_skills = [skill for skill in skills.keys() if skill.lower() in resume_text.lower()]
    return found_skills

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))

        # Create new user and save to the database
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!')
            return redirect(url_for('upload_resume'))
        else:
            flash('Invalid credentials. Please try again.')

    return render_template('login.html')

# Route for uploading resume
@app.route('/upload', methods=['GET', 'POST'])
def upload_resume():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        resume_file = request.files['resume']
        if resume_file:
            filename = resume_file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            resume_file.save(file_path)

            # Extract text based on file type
            if filename.endswith('.docx'):
                resume_text = extract_text_from_docx(file_path)
            elif filename.endswith('.pdf'):
                resume_text = extract_text_from_pdf(file_path)
            else:
                flash('Invalid file type. Please upload a .docx or .pdf file.')
                return redirect(url_for('upload_resume'))

            # Analyze the resume for skills
            found_skills = analyze_resume_for_skills(resume_text)
            session['found_skills'] = found_skills  # Store found skills in session
            
            if found_skills:
                return redirect(url_for('take_mcq'))
            else:
                flash('No relevant skills found in the resume.')
                return redirect(url_for('upload_resume'))

    return render_template('upload.html')

@app.route('/mcq', methods=['GET', 'POST'])
def take_mcq():
    if 'found_skills' not in session:
        return redirect(url_for('upload_resume'))

    skill_results = {}
    
    # Handle MCQ submission
    if request.method == 'POST':
        for skill in session['found_skills']:
            score = 0  # Initialize score for each skill
            # Get the answers for the specific skill
            for index, (question, correct_answer, choices) in enumerate(skills[skill]):
                # Use the index to access the correct input name
                user_answer = request.form.get(f'user_answers_{skill}_{index}')
                if user_answer == correct_answer:
                    score += 1  # Increment score for correct answer

            # Convert to percentage
            skill_results[skill] = (score / len(skills[skill])) * 100 if skills[skill] else 0  

        session['skill_results'] = skill_results  # Store results in session
        return redirect(url_for('show_scores'))

    # Prepare MCQ questions for the skills found
    questions = {skill: skills[skill] for skill in session['found_skills']}
    
    # Prepare questions with indices
    indexed_questions = {skill: list(enumerate(questions[skill])) for skill in questions}

    return render_template('mcq.html', questions=indexed_questions)


# Route for showing the scores after MCQs
@app.route('/scores')
def show_scores():
    skill_results = session.get('skill_results', {})
    recommendations_for_skills = {}
    
    for skill, score in skill_results.items():
        if score < 50:
            recommendations_for_skills[skill] = recommendations[skill]['tutorials']
        elif score >= 50 and score <= 70:
            recommendations_for_skills[skill] = recommendations[skill]['courses']
        else:
            recommendations_for_skills[skill] = "Great job! Keep up the good work."

    return render_template('scores.html', skill_results=skill_results, recommendations=recommendations_for_skills)


# Route for logging out
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('found_skills', None)
    session.pop('skill_results', None)
    flash('Logged out successfully.')
    return redirect(url_for('login'))



# Define recommendations based on score ranges
recommendations = {
    'Python': {
        'tutorials': "Recommended tutorial: Python for Everybody - [link- Python for Everybody Specialization]",
        'courses': "Recommended referral course: Python Data Science - [link- Complete Python Bootcamp: Go from zero to hero in Python 3]"
    },
    'Java': {
        'tutorials': "Recommended tutorial: Java Programming for Beginners - [link- Java Programming and Software Engineering Fundamentals]",
        'courses': "Recommended referral course: Java Certification - [link- Java Programming Masterclass for Software Developers]"
    },
    'SQL': {
        'tutorials': "Recommended tutorial: SQL Basics - [link- Databases and SQL for Data Science with Python]",
        'courses': "Recommended referral course: SQL for Data Science - [link- The Complete SQL Bootcamp: Go from Zero to Hero]"
    },
    'JavaScript': {
        'tutorials': "Recommended tutorial: JavaScript Basics - [link- JavaScript for Beginners]",
        'courses': "Recommended referral course: Advanced JavaScript - [link- JavaScript: Understanding the Weird Parts]"
    },
    'HTML': {
        'tutorials': "Recommended tutorial: HTML Crash Course - [link- HTML, CSS, and Javascript for Web Developers]",
        'courses': "Recommended referral course: Web Development Bootcamp - [link- The Complete Web Developer Course 2.0]"
    },
    'CSS': {
        'tutorials': "Recommended tutorial: CSS Fundamentals - [link- CSS Basics]",
        'courses': "Recommended referral course: Responsive Web Design - [link- Responsive Web Design Certification]"
    },
    'PHP': {
        'tutorials': "Recommended tutorial: Learn PHP - [link- PHP for Beginners - Become a PHP Master - CMS Project]",
        'courses': "Recommended referral course: PHP for Web Development - [link- Learn PHP Programming From Scratch]"
    }
}




if __name__ == '__main__':
    with app.app_context():  # Ensure the app context is active
        db.create_all()  # Create database tables
    app.run(debug=True)
