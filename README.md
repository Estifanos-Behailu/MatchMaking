# Study Sphere Matchmaking System

This is a web application built using Flask for a collaborative learning platform called **Study Sphere**. The platform includes features for user registration, profile management, and a matchmaking system that suggests collaboration partners based on skills, experience, education, and languages. The project integrates machine learning for matching users using the **Universal Sentence Encoder (USE)** model to calculate similarity between users.

## Features
- **User Registration**: Users can register by entering their details, including skills, experience, education, and languages.
- **Profile Management**: Each user has a profile page displaying their information.
- **Matchmaking**: Users can find potential collaborators based on a matching algorithm that compares profiles.
- **Collaboration Request**: Users can send collaboration requests via email to potential matches.
  
## Technologies Used
- **Flask**: Python web framework.
- **PostgreSQL**: Database to store user profiles.
- **Flask-Mail**: To send email requests for collaboration.
- **TensorFlow Hub**: For loading the Universal Sentence Encoder model.
- **SciPy**: Used for calculating cosine similarity between users’ profile data.

## Installation

### Prerequisites
- Python 3.7 or above
- PostgreSQL database
- Neon (for database hosting) or any PostgreSQL-compatible hosting service

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/study-sphere.git
   cd study-sphere
   ```

2. **Install the required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file or export these variables in your terminal:
   ```bash
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=your_secret_key
   MAIL_USERNAME=e3stifs@gmail.com
   MAIL_PASSWORD=your_mail_password
   ```

4. **Database Setup**:
   Create a PostgreSQL database and update the connection details in `app.py`:
   ```python
   conn = psycopg2.connect(
       host='your_neon_host',
       database='your_database_name',
       user='your_database_user',
       password='your_password',
       port='5432'
   )
   ```

5. **Run the application**:
   ```bash
   flask run
   ```

   The app will be available at `http://127.0.0.1:5000/`.

## Usage

### Registering a New User
Navigate to `/register` to create a new profile. Fill in the required information such as:
- Name
- Email
- Skills (comma-separated)
- Job title
- Experience (job title, company, start/end date)
- Education (degree, institution, graduation year)
- Languages (primary language and proficiency level)

### Viewing a Profile
Once registered, you can view your profile at `/profile?email=your_email`.

### Finding Matches
To find potential collaborators, navigate to `/match?email=your_email`. The system will compare your profile with other users and provide matches with a similarity score. Only users with a match score higher than **0.7** will be displayed.

### Sending Collaboration Requests
After finding a match, you can send a collaboration request via email by submitting a form on the matches page.

## Matchmaking Algorithm

The matchmaking algorithm compares users' skills, experience, education, and languages using the **Universal Sentence Encoder (USE)** and calculates a similarity score using the cosine similarity formula. The matching score is weighted as follows:
- Skills: 40%
- Experience: 30%
- Education: 20%
- Languages: 10%
