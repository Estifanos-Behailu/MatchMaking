from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mail import Mail, Message
from scipy.spatial.distance import cosine
import tensorflow_hub as hub
import json
import psycopg2
import os

# Flask app configuration
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set your secret key

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'e3stifs@gmail.com'
app.config['MAIL_PASSWORD'] = 'lpkz rhti dhdu xeni'

mail = Mail(app)

# Database connection function
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host='ep-polished-wave-a50wwuzy.us-east-2.aws.neon.tech',
            database='match',
            user='match_owner',
            password='2bpa6gWifLxM',
            port='5432'
        )
        return conn
    except Exception as e:
        print(f"An error occurred while connecting to the database: {e}")
        return None

# Utility function to fetch a user by their email
def get_user_by_email(email):
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_resumes WHERE user_email = %s', (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user is None:
        return None

    return {
        'id': user[0],
        'user_name': user[1],
        'user_email': user[2],
        'job_title': user[3],
        'skills': user[4],
        'experience': user[5],
        'education': user[6],
        'languages': user[7]
    }

# Load Universal Sentence Encoder model
try:
    model = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# Modify the similarity function to handle potential connection issues
def use_similarity(text_a, text_b):
    if model is None:
        return 0.5  # Return a default middle score if model failed to load
    try:
        embedding_a = model([text_a])[0].numpy()
        embedding_b = model([text_b])[0].numpy()
        similarity_score = 1 - cosine(embedding_a, embedding_b)
        return similarity_score
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.5  # Return middle score in case of errors

# Calculate match score between two users
def calculate_match_with_use(user_a, user_b):
    skill_score = use_similarity(json.dumps(user_a['skills']), json.dumps(user_b['skills']))
    experience_score = use_similarity(json.dumps(user_a['experience']), json.dumps(user_b['experience']))
    education_score = use_similarity(json.dumps(user_a['education']), json.dumps(user_b['education']))
    languages_score = use_similarity(json.dumps(user_a['languages']), json.dumps(user_b['languages']))

    match_score = (skill_score * 0.4) + (experience_score * 0.3) + (education_score * 0.2) + (languages_score * 0.1)
    return match_score

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_name = request.form['user_name']
        user_email = request.form['user_email']
        job_title = request.form['job_title']
        
        # Process skills input (comma-separated string)
        skills = request.form['skills'].split(',')
        skills = [skill.strip() for skill in skills if skill.strip()]  # Remove empty entries and trim spaces

        # Process experience input
        experience_job_title = request.form.get('experience_job_title', '').strip()
        experience_company = request.form.get('experience_company', '').strip()
        experience_start_date = request.form.get('experience_start_date', '').strip()
        experience_end_date = request.form.get('experience_end_date', '').strip()

        if not all([experience_job_title, experience_company, experience_start_date, experience_end_date]):
            flash('Please fill out all experience fields.', 'danger')
            return redirect(url_for('register'))

        experience = [{
            "job_title": experience_job_title,
            "company": experience_company,
            "start_date": experience_start_date,
            "end_date": experience_end_date
        }]

        # Process education input
        education_degree = request.form.get('education_degree', '').strip()
        education_institution = request.form.get('education_institution', '').strip()
        education_year = request.form.get('education_year', '').strip()

        if not all([education_degree, education_institution, education_year]):
            flash('Please fill out all education fields.', 'danger')
            return redirect(url_for('register'))

        education = [{
            "degree": education_degree,
            "institution": education_institution,
            "graduation_year": education_year
        }]

        # Process language inputs
        primary_language = request.form.get('primary_language', '').strip()
        language_level = request.form.get('language_level', '').strip()

        if not primary_language or not language_level:
            flash('Please select both a primary language and its proficiency level.', 'danger')
            return redirect(url_for('register'))

        languages = [{"name": primary_language, "level": language_level}]

        # Convert lists and dictionaries to JSON
        try:
            skills_json = json.dumps(skills)
            experience_json = json.dumps(experience)
            education_json = json.dumps(education)
            languages_json = json.dumps(languages)
        except Exception as e:
            flash(f'Error processing data: {str(e)}', 'danger')
            return redirect(url_for('register'))

        conn = get_db_connection()
        if conn is None:
            flash('Database connection failed. Please try again later.', 'danger')
            return redirect(url_for('home'))

        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO user_resumes (user_name, user_email, job_title, skills, experience, education, languages)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_name, user_email, job_title, skills_json, experience_json, education_json, languages_json))
            conn.commit()
        except Exception as e:
            conn.rollback()
            flash(f'Error saving to database: {str(e)}', 'danger')
            return redirect(url_for('register'))
        finally:
            cur.close()
            conn.close()

        flash('Registration successful!', 'success')
        return redirect(url_for('profile', email=user_email))

    return render_template('register.html')

# Profile page route
@app.route('/profile')
def profile():
    email = request.args.get('email')
    if not email:
        flash('Please provide an email to view your profile.', 'danger')
        return redirect(url_for('home'))

    user = get_user_by_email(email)
    if user is None:
        flash('User not found. Please register.', 'danger')
        return redirect(url_for('register'))

    return render_template('profile.html', user=user)

# Matching users route
@app.route('/match')
def match_users():
    email = request.args.get('email')
    email_status = request.args.get('email_status')
    if not email:
        flash('Please provide your email to find matches.', 'danger')
        return redirect(url_for('home'))

    current_user = get_user_by_email(email)
    if not current_user:
        flash('User not found. Please register.', 'danger')
        return redirect(url_for('register'))

    conn = get_db_connection()
    if conn is None:
        flash('Database connection failed. Please try again later.', 'danger')
        return redirect(url_for('home'))

    cur = conn.cursor()
    cur.execute("SELECT * FROM user_resumes WHERE user_email != %s", (email,))
    other_users = cur.fetchall()
    cur.close()
    conn.close()

    matches = []
    for user in other_users:
        other_user = {
            'id': user[0],
            'user_name': user[1],
            'user_email': user[2],
            'job_title': user[3],
            'skills': user[4],
            'experience': user[5],
            'education': user[6],
            'languages': user[7]
        }
        match_score = calculate_match_with_use(current_user, other_user)
        if match_score > 0.7:
            matches.append((other_user, match_score))

    matches.sort(key=lambda x: x[1], reverse=True)

    return render_template('matches.html', matches=matches, user=current_user, email_status=email_status)

# Collaboration request route
@app.route('/send_collaboration_request', methods=['POST'])
def send_collaboration_request():
    match_email = request.form.get('match_email')
    sender_email = request.form.get('sender_email')

    if not match_email or not sender_email:
        return jsonify({'status': 'error', 'message': 'Invalid request. Please try again.'})

    message = Message('Study Sphere Collaboration Request', 
        sender='noreply@app.com',
        recipients=[match_email],
    )
    
    message.body = f'You have received a collaboration request from {sender_email} to collaborate on StudySphere!'
    
    try:
        mail.send(message)
        return jsonify({'status': 'success', 'message': f'Collaboration request sent to {match_email}!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error sending collaboration request: {str(e)}'})

# Home route
@app.route('/')
def home():
    return render_template('home.html')

# Run the application
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use environment variable for port
    app.run(host='0.0.0.0', port=port, debug=False)  # Set debug=False for production
