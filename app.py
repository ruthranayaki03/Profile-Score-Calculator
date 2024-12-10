from flask import Flask,render_template as render,request,redirect,url_for
import mysql.connector
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="code architect"
)
cursor = db.cursor()

#folder upload
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def home():
    return render("index.html")

@app.route("/personalinfo", methods=['GET','POST'])
def personal_info():
    if request.method == "POST":
        # Get form data
        profile_photo = request.files['profile_photo']
        name = request.form['name']
        description = request.form['description']
        email = request.form['email']
        phone = request.form['phone']
        education = request.form['education']
        occupation = request.form['cs']
        interest = request.form['interest']
        resume = request.files['resume']
        qualification = request.form['qualification']
        language = request.form['lang']
        
        # profile photo
        profile_photo_filename = secure_filename(profile_photo.filename)
        profile_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_photo_filename)
        profile_photo.save(profile_photo_path)
        
        # resume
        resume_filename = secure_filename(resume.filename)
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)
        resume.save(resume_path)
        
        sql = """
        INSERT INTO employer_details (name, description, email, phone, education, occupation, interest, resume, qualification, language,profile_photo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (name, description, email, phone, education, occupation, interest, resume_filename, qualification, language,profile_photo_filename)
        
        cursor.execute(sql, values)
        db.commit()
        
        return redirect(url_for('home'))
    
    return render("personalinfoinsert.html")


@app.route("/candidate-dash")
def candidatedash():
    return render("candidate-dashboard.html")

@app.route("/job-details")
def jobdetails():
    return render("jobdetails.html")



@app.route("/employer-dash")
def employerdash():
    return render("employer-dash.html")





if __name__=="__main__":
    app.run(debug=True)