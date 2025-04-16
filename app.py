from flask import Flask, render_template, request, redirect, url_for, session, send_file,flash,jsonify
from pymongo import MongoClient
import gridfs
import bcrypt
import io
import pickle
import groq
import pandas as pd
import numpy as np
from bson import ObjectId
import smtplib
import secrets
app = Flask(__name__, template_folder="templates")
app.secret_key = "secret"
import secrets
import smtplib
from email.mime.text import MIMEText


# Connect to MongoDB
MONGO_URL = "mongodb+srv://raja:rajaRAJA1234@users.7psqc.mongodb.net/?retryWrites=true&w=majority&appName=users"
client = MongoClient(MONGO_URL)
print("Mongo connected")
db = client["mydatabase"]  # Database name
users_collection = db["userdetails"]  # Collection name and emaile
users_collection_demo = db["userdetails_demo"]  # Collection name and emaile

fs = gridfs.GridFS(db)  # GridFS for storing images

feedbacks_collection1 = db["feedback"]  # Obesity feedback
depression_collection = db["depression"]  # Depression feedback
migraine_collection = db["migraine"]  # Migraine feedback
dengue_collection = db["dengue"]  # Dengue feedback
forgot_collection = db['forgot_password']



# Store tokens temporarily for password reset
reset_tokens = {}

# SMTP Configuration
EMAIL_ADDRESS = "r210264@rguktrkv.ac.in"
EMAIL_PASSWORD = "cdmz ttzb lxmi vdkz"
# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "r210264@rguktrkv.ac.in"
EMAIL_PASSWORD = "cdmz ttzb lxmi vdkz"


# Function to generate a 7-digit OTP
def generate_otp():
    return ''.join(str(secrets.randbelow(10)) for _ in range(7))

# Function to send OTP via email
def send_otp_email(receiver_email, otp):
    try:
        msg = MIMEText(f"Your OTP for password reset is: {otp}")
        msg["Subject"] = "Password Reset OTP"
        msg["From"] = EMAIL_SENDER
        msg["To"] = receiver_email

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
    
@app.route('/forgot')
def forgot():
    return render_template('forms/forgot_password.html')       
    
# Route: Forgot Password (Enter Email)
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    
    if request.method == 'POST':
        email = request.form['email']
        user = users_collection.find_one({"email": email})

        if user:
            otp = generate_otp()
            forgot_collection.update_one({"email": email}, {"$set": {"otp": otp}}, upsert=True)

            if send_otp_email(email, otp):
                session['email'] = email  # Store email in session
                return redirect(url_for('verify_otp'))
            else:
                flash("Failed to send OTP", "danger")
        else:
            flash("Email not registered", "danger")
    
    return render_template('forms/forgot_password.html')


# Route: Forgot Password (Enter Email)
@app.route('/forgot-password-resend', methods=['GET', 'POST'])
def forgot_password_resend():
    
    if request.method == 'POST':
        email = session['email']
        user = users_collection.find_one({"email": email})

        if user:
            otp = generate_otp()
            forgot_collection.update_one({"email": email}, {"$set": {"otp": otp}}, upsert=True)
            print("OTP sent to email:", email)  # Debugging line
            if send_otp_email(email, otp):
                session['email'] = email  # Store email in session
                return redirect(url_for('verify_otp'))
            else:
                flash("Failed to send OTP", "danger")
        else:
            flash("Email not registered", "danger")
    
    return render_template('forms/forgot_password.html')









# Route: Verify OTP
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    print("OTP verification page accessed")  # Debugging line
    if 'email' not in session:
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        otp = request.form['otp']
        print("OTP entered:................................................................", otp)  # Debugging line
        email = session['email']
        record = forgot_collection.find_one({"email": email, "otp": otp})

        if record:
            session.pop('otp', None)
            return redirect(url_for('update_password'))
        else:
            flash("Invalid OTP", "danger")

    return render_template('forms/verify_otp.html')

# Route: Update Password
@app.route('/update-password', methods=['GET', 'POST'])
def update_password():
    if 'email' not in session:
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['password']
        email = session.pop('email', None)

        users_collection.update_one({"email": email}, {"$set": {"password": new_password}})
        flash("Password updated successfully. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('forms/update_password.html')
    
    
    
    
    
@app.route("/")
def start():
    all_collections = [
        feedbacks_collection1,
        depression_collection,
        migraine_collection,
        dengue_collection
        
        
    ]
    
    total_sum = 0
    total_ratings = 0
    total_users = 0
    total_feedbacks = 0
    total_login = 0

    feedbacks = list(users_collection.find())
    total_users += len(feedbacks)
    
    feedbacks = list(users_collection_demo.find())
    total_login += len(feedbacks)
    
    for collection in all_collections:
        feedbacks = list(collection.find())
        total_feedbacks += len(feedbacks)

        for feed in feedbacks:
            if 'rating' in feed:
                try:
                    rating = float(feed['rating'])  # Ensure numeric
                    total_sum += rating
                    total_ratings += 1
                except ValueError:
                    continue

    avg = 0
    if total_ratings > 0:
        avg = round(total_sum / (total_ratings * 5), 1) * 100  # Normalized to 100%

    print(f"Average Feedback Rating: {avg}%")
    print(f"Total Feedback Users: {total_users}")
    
    return render_template("forms/start.html", average_rating=avg, total_users=total_users,total_feedbacks=total_feedbacks,total_login=total_login)
  
     
@app.route("/getstart")
def getstart():
      return render_template("forms/demo_index.html")      
    
# Route to display registration page
@app.route("/signup")
def signup():
    return render_template("forms/signup.html")


# Route to handle registration form submission
@app.route("/signup_action", methods=["POST"])
def signup_action():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    photo = request.files["photo"]
    # Hash Password

    # Store Image in GridFS
    if photo:
        photo_id = fs.put(photo.read(), filename=photo.filename)
    else:
        photo_id = None


    # Check if email already exists
    existing_user = users_collection.find_one({"email": email})
    if existing_user:
        flash("Email already registered. Please log in.", "danger")
        return redirect(url_for("signup"))

    # Insert new user if email does not exist
        # Store User Data in MongoDB
    user_data = {"name": name, "email": email, "password":password, "photo_id": photo_id}
    users_collection.insert_one(user_data)  
    user_data_full = {"name": name, "email": email, "password":password, "photo_id": photo_id}
    users_collection_demo.insert_one(user_data_full)   
    flash("Registration successful!", "success")
    return redirect(url_for("login"))

# Route to display login page
@app.route("/login")
def login():
    return render_template("forms/login.html")

# Route to handle login form submission
@app.route("/login", methods=["POST"])
def login_user():
    email = request.form.get("email")
    password = request.form.get("password")

    # Check if email exists
    user = users_collection.find_one({"email": email})
    if not user:
        flash("Email is not registered. Please sign up.", "danger")
        return redirect(url_for("login"))

    # Check if password matches
    if user["password"] != password:
        flash("Incorrect password. Please try again.", "danger")
        return redirect(url_for("login"))

    # Store user session
    session["user"] = email
    return redirect(url_for("index"))  # Redirect to menu page after login


@app.route("/index")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    user = users_collection.find_one({"email": session["user"]})
    return render_template("forms/index.html",user=user)
@app.route("/obesity")
def obesity():
    if "user" not in session:
        return redirect(url_for("login"))
    user = users_collection.find_one({"email": session["user"]})
    session["name"] = "obesity1"
    return render_template("forms/obesity.html",user=user)
@app.route("/depression")
def depression():
    if "user" not in session:
        return redirect(url_for("login"))
    user = users_collection.find_one({"email": session["user"]})
    session["name"] = "depression1"
    return render_template("forms/depression.html",user=user)
@app.route("/migraine")
def migraine():
    if "user" not in session:
        return redirect(url_for("login"))
    user = users_collection.find_one({"email": session["user"]})
    session["name"] = "migraine1"
    return render_template("forms/migraine.html",user=user)
@app.route("/dengue")
def dengue():
    if "user" not in session:
        return redirect(url_for("login"))
    user = users_collection.find_one({"email": session["user"]})
    session["name"] = "dengue1"
    return render_template("forms/dengue.html",user=user)
@app.route("/About_obesity")
def About_obesity():
    if "user" not in session:
        return redirect(url_for("login"))
    user = users_collection.find_one({"email": session["user"]})
    return render_template("forms/About_Obesity.html",user=user)
@app.route("/About_depression")
def About_depression():
    if "user" not in session:
        return redirect(url_for("login"))
    user = users_collection.find_one({"email": session["user"]})
    return render_template("forms/About_depression.html",user=user)
@app.route("/About_migraint")
def About_migraint():
    if "user" not in session:
        return redirect(url_for("login"))
    user = users_collection.find_one({"email": session["user"]})
    return render_template("forms/About_migraint.html",user=user)
@app.route("/About_dengue")
def About_dengue():
    if "user" not in session:
        return redirect(url_for("login"))
    user = users_collection.find_one({"email": session["user"]})
    return render_template("forms/About_dengue.html",user=user)

@app.route("/contact")
def contact():
    if "user" not in session:
        return redirect(url_for("login"))
    user = users_collection.find_one({"email": session["user"]})
    return render_template("forms/contact_Obesity.html",user=user)

@app.route("/contact_obesity")
def contact_obesity():
    if "user" not in session:
        return redirect(url_for("login"))
    user = users_collection.find_one({"email": session["user"]})
    return render_template("forms/contact_Obesity1.html",user=user)
@app.route("/contact_depression")
def contact_depression():
    if "user" not in session:
        return redirect(url_for("login"))
    user = users_collection.find_one({"email": session["user"]})
    return render_template("forms/contact_depression.html",user=user)
@app.route("/contact_dengue")
def contact_dengue():
    if "user" not in session:
        return redirect(url_for("login"))
    user = users_collection.find_one({"email": session["user"]})
    return render_template("forms/contact_dengue.html",user=user)







@app.route("/userfeedback", methods=["GET", "POST"])
def userfeedback():   
    return render_template("forms/feed.html")
@app.route("/feedback", methods=["GET"])
def feedback():
    return render_template("forms/feedback.html")

from datetime import datetime
# Route to handle feedback submission
@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    email = session["user"]  # Get logged-in user's email
    feedback_text = request.form.get("feedback")
    rating = request.form.get('rating')
    print("Rating:::::::::::::::::::::::::::::", rating)  # Debugging line

    if not feedback_text:
        flash("Please fill in all field!", "danger")
        return redirect(url_for("feedback"))
    
    userpage = session["name"]

    # Default to None (or a safe fallback collection)
    feedbacks_collection = None  

    if userpage == "obesity1":
        feedbacks_collection = feedbacks_collection1
    elif userpage == "depression1":
        feedbacks_collection = depression_collection
    elif userpage == "migraine1":
        feedbacks_collection = migraine_collection
    elif userpage == "dengue1":
        feedbacks_collection = dengue_collection

    # Check if feedbacks_collection is correctly assigned
    if feedbacks_collection is None:
        print("Error: feedbacks_collection is not assigned properly!")
        raise ValueError("Invalid userpage session value: " + str(userpage))

    # Check if feedback already exists for this email
    existing_feedback = feedbacks_collection.find_one({"email": email})
    if existing_feedback:
        flash("You have already submitted feedback!", "danger")
        return redirect(url_for("feedback"))

    useremail = users_collection.find_one({"email": email})
    username = useremail["name"]

    # Get current date and time
    current_date = datetime.now().strftime("%d-%m-%Y")

    # Insert feedback with date
    feedbacks_collection.insert_one({
        "email": email,
        "name": username,
        "feedback": feedback_text,
        "date": current_date,
        "rating": rating
    })

    flash("Feedback submitted successfully!", "success")
    return redirect(url_for("feedback"))


# Route to display all feedback
@app.route("/all_feedback")
def all_feedback():
    user_email = session["user"]
    userpage = session["name"]
    if(userpage == "obesity1"):
        feedbacks_collection = feedbacks_collection1;
    elif(userpage == "depression1"):
        feedbacks_collection =depression_collection;
    elif(userpage == "migraine1"):
        feedbacks_collection =migraine_collection;    
    elif(userpage == "dengue1"):
        feedbacks_collection =dengue_collection; 
    feedbacks = list(feedbacks_collection.find())
    sum_feed = 0
    valid_ratings = 0
    for feed in feedbacks:
        if 'rating' in feed:
            try:
                rating = float(feed['rating'])  # Ensures numeric
                sum_feed += rating
                valid_ratings += 1
            except ValueError:
                continue

    avg = 0
    if valid_ratings > 0:
        avg = round(sum_feed / (valid_ratings * 5), 1) * 100

    print(f"Average Feedback Rating: {avg}%")
    # Fetch all feedbacks
    return render_template("forms/all_feedback.html", feedbacks=feedbacks, user_email=user_email,avg=avg)

# Route to delete feedback
@app.route("/delete_feedback/<feedback_id>", methods=["POST"])
def delete_feedback(feedback_id):
    if "user" not in session:
        flash("You must be logged in to delete feedback.", "danger")
        return redirect(url_for("login"))
    userpage = session["name"]
    if(userpage == "obesity1"):
        feedbacks_collection = feedbacks_collection1;
    elif(userpage == "depression1"):
        feedbacks_collection =depression_collection;
    elif(userpage == "migraine1"):
        feedbacks_collection =migraine_collection;    
    elif(userpage == "dengue1"):
        feedbacks_collection =dengue_collection; 
     
    
    feedback = feedbacks_collection.find_one({"_id": ObjectId(feedback_id)})
    if feedback and feedback["email"] == session["user"]:  
        feedbacks_collection.delete_one({"_id": ObjectId(feedback_id)})
        flash("Feedback deleted successfully!", "success")
    else:
        flash("You are not authorized to delete this feedback.", "danger")

    return redirect(url_for("all_feedback"))
# Route to edit feedback
@app.route("/edit_feedback/<feedback_id>", methods=["POST"])
def edit_feedback(feedback_id):
    if "user" not in session:
        flash("You must be logged in to edit feedback.", "danger")
        return redirect(url_for("login"))
    
    userpage = session["name"]
    if userpage == "obesity1":
        feedbacks_collection = feedbacks_collection1
    elif userpage == "depression1":
        feedbacks_collection = depression_collection
    elif userpage == "migraine1":
        feedbacks_collection = migraine_collection
    elif userpage == "dengue1":
        feedbacks_collection = dengue_collection

    new_feedback_text = request.form.get("edited_feedback")
    rating = request.form.get("rating")
    current_date = datetime.now().strftime("%d-%m-%Y")

    print("Rating:::::::::::::::::::::::::::::", rating)  # Debugging line

    feedback = feedbacks_collection.find_one({"_id": ObjectId(feedback_id)})

    if feedback and feedback["email"] == session["user"]:
        feedbacks_collection.update_one(
            {"_id": ObjectId(feedback_id)},
            {
                "$set": {
                    "feedback": new_feedback_text,
                    "rating": rating,
                    "date": current_date
                }
            }
        )
        flash("Feedback updated successfully!", "success")
    else:
        flash("You are not authorized to edit this feedback.", "danger")

    return redirect(url_for("all_feedback"))




# Route to Profile Page
@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user"]})
    return render_template("forms/profile.html", user=user)

# Route to Fetch User Image
@app.route("/photo/<photo_id>")
def get_photo(photo_id):
    try:
        photo = fs.get(ObjectId(photo_id))  # Convert to ObjectId
        return send_file(io.BytesIO(photo.read()), mimetype="image/jpeg")
    except Exception as e:
        return f"Error: {str(e)}"

# **New Route: Update Name and Profile Picture**
@app.route("/update_profile", methods=["POST"])
def update_profile():
    if "user" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user"]})

    if not user:
        return "User not found!"

    new_name = request.form["new_name"]
    new_photo = request.files.get("new_photo")

    update_data = {"name": new_name}  # Update name

    if new_photo:
        # Delete old photo if exists
        if user.get("photo_id"):
            fs.delete(ObjectId(user["photo_id"]))

        # Store new photo in GridFS
        new_photo_id = fs.put(new_photo.read(), filename=new_photo.filename)
        update_data["photo_id"] = new_photo_id  # Update photo_id

    # Update user's name and/or photo_id in the database
    users_collection.update_one({"email": session["user"]}, {"$set": update_data})

    return redirect(url_for("profile"))

@app.route('/logout')
def logout():
    if "user" in session:
        user_email = session["user"]  # Get logged-in user's email

        # Delete user details from the database
        users_collection.delete_one({"email": user_email})

        # Remove user session
        session.pop("user", None)  
        flash("Your account has been deleted and you have been logged out.", "danger")

    return redirect(url_for('login'))
@app.route('/back_to_login')
def back_to_login():
    return redirect(url_for('login'))

@app.route('/back_to_menu')
def back_to_menu():
    userpage = session["name"]
    if(userpage == "obesity1"):
        return redirect(url_for('obesity'))
    elif(userpage == "depression1"):
        return redirect(url_for('depression'))
    elif(userpage == "migraine1"):
        return redirect(url_for('migraine'))   
    elif(userpage == "dengue1"):
        return redirect(url_for('dengue'))
    
    
 
denguemodel=pickle.load(open("dengue.pkl", "rb"))
model=pickle.load(open("obesity.pkl","rb"))
migrainemodel=pickle.load(open("migraine.pkl","rb"))
depressionmodel=pickle.load(open("depression.pkl","rb"))

#GROQ_API_KEY = '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'GROQ_API_KEY
GROQ_API_KEY="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"
lient = groq.Groq(api_key=GROQ_API_KEY)


def yes_no(str):
   if(str=='yes' or str=='Yes'):
      return 1
   else:
      return 0
   
def numeric(str):
   return float(str)

def gender(str):
   if str=='male':
      return 0
   else:
      return 1

def trans(str):
   if str=="Public_Transportation":
      return 3
   elif str=="Automobile":
      return 0
   elif str=="Walking":
      return 4
   elif str=="Motorbike":
      return 2
   else:
      return 1

def food(str):
   if str=="Sometimes":
      return 2
   elif str=="Frequently":
      return 1
   elif str=="Always":
      return 0
   else:
      return 3


def sleepy(str):
    if str=="less than 5":
       return 2
    elif str=="5-6 hours":
       return 0
    elif str=="7-8 hours":
       return 1
    elif str=="more than 8 hours":
       return 3
    else:
       return 4
    
def diet_habit(str):
   if str=="unhealthy":
      return 3
   elif str=="moderate":
      return 1
   elif str=="healthy":
    return 0
   else:
      return 2

def gend(str):
   if str=='male':
      return 0
   else:
      return 1



@app.route("/submit", methods=['POST','GET'])
def submit():
    try:
        data = request.get_json(force=True)

        if not data:
            return jsonify({'error': 'No data received'}), 400

        print("Received data:", data)  # Debugging
    
        # Extracting form data with default values to prevent NoneType errors
        age = data.get('age', "0")
        height = data.get('height', "0")
        weight = data.get('weight', "0")
        veg_frequency = data.get('veg_frequency', "0")
        activity_frequency = data.get('activity_frequency', "0")
        family_history = data.get('family_history', "no")
        sex = data.get('sex', "unknown")
        high_caloric_food = data.get('high_caloric_food', "no")
        food_between_meals = data.get('food_between_meals', "unknown")
        smoke = data.get('smoke', "no")
        transportation = data.get('transportation', "unknown")

        # Convert input values safely
        try:
            Age = float(age) if age.replace('.', '', 1).isdigit() else 0
            Height = float(height) if height.replace('.', '', 1).isdigit() else 0
            Weight = float(weight) if weight.replace('.', '', 1).isdigit() else 0
            FCVC = float(veg_frequency) if veg_frequency.replace('.', '', 1).isdigit() else 0
            FAF = float(activity_frequency) if activity_frequency.replace('.', '', 1).isdigit() else 0
        except ValueError:
            return jsonify({'error': 'Invalid numeric values'}), 400

        Family_history = yes_no(family_history)
        Sex = gender(sex)
        favc = yes_no(high_caloric_food)
        caec = food(food_between_meals)
        smoke = yes_no(smoke)
        mtrans = trans(transportation)

        # Prepare input for model
        column_names = ["Age", "Height", "Weight", "FCVC", "FAF", "Family_history", 
                        "Sex", "favc", "caec", "smoke", "mtrans"]

        arr = np.array([[Age, Height, Weight, FCVC, FAF, Family_history, 
                         Sex, favc, caec, smoke, mtrans]])

        arr_df = pd.DataFrame(arr, columns=column_names)

        print(f"Input Array: {arr_df}")  # Debugging

        # Make prediction using the model
        pred = model.predict(arr_df)

        print(f"Prediction: {pred}")  # Debugging

        disease_status = pred[0]

        prompt = f"Suggest some recommendations for {disease_status} patient after mentioning which disease he has along with recommendations as paragraphs. If the patient does not have any disease, leave it."

        response = lient.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )

        response_text = response.choices[0].message.content

        return jsonify({'reply': response_text})

    except Exception as e:
        print(f"Error in /submit: {str(e)}")  # Logs error to console
        return jsonify({'error': str(e)}), 500

@app.route("/click", methods=['POST', 'GET'])
def click():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data received'}), 400

        print(f"Received data: {data}")  # Debugging

        # Extracting form data
        fe = data.get('fever')
        head = data.get('headache')
        joint = data.get('jointPain')
        bledd = data.get('bleeding')

        # Convert input values
        Fever = yes_no(fe)
        Headache = yes_no(head)
        JointPain = yes_no(joint)
        Bleeding =yes_no(bledd)

        column_names = ["Fever", "Headache", "JointPain", "Bleeding"]
        arr = np.array([[Fever, Headache, JointPain, Bleeding]])
        arr_df = pd.DataFrame(arr, columns=column_names)

        print(f"Input Array: {arr_df}")  # Debugging

        # Use the correct model for dengue
        pred = denguemodel.predict(arr_df)

        print(f"Prediction: {pred}")  # Debugging

        if pred[0] == 0:
            x = "Dengue"
        else:
            x = "No Dengue"

        prompt = f"Suggest some recommendations for {x} patient after mentioning which disease he has along with recommendations as paragraphs. If the patient does not have any disease, leave it."

        response = lient.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )

        response_text = response.choices[0].message.content

        return jsonify({'reply': response_text})

    except Exception as e:
        print(f"Error in /click: {str(e)}")  # Logs error to console
        return jsonify({'error': str(e)}), 500


@app.route("/give", methods=['POST', 'GET'])
def give():
    try:
        # Get JSON data
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data received'}), 400

        print(f"Received data: {data}")  # Debugging

        # Extracting form data with default values to prevent NoneType errors
        age = data.get('age', "0")  
        severity = data.get("severity", "0")
        vomit_sensation = data.get("vomit_sensation", "no")
        vomit = data.get("vomit", "no")
        sound_sensitivity = data.get("sound_sensitivity", "no")
        light_sensitivity = data.get("light_sensitivity", "no")
        movement_sensation = data.get("movement_sensation", "no")
        ear_noise = data.get("ear_noise", "no")
        hearing_loss = data.get("hearing_loss", "no")
        double_vision = data.get("double_vision", "no")
        pricking_sensation = data.get("pricking_sensation", "no")

        # Convert input values safely
        try:
            Age = float(age) if age.replace('.', '', 1).isdigit() else 0
            Frequency = float(severity) if severity.isdigit() else 0
        except ValueError:
            return jsonify({'error': 'Invalid numeric values'}), 400

        Nausea = yes_no(vomit_sensation)
        Vomit = yes_no(vomit)
        Phonophobia = yes_no(sound_sensitivity)
        Photophobia = yes_no(light_sensitivity)
        Vertigo = yes_no(movement_sensation)
        Tinnitus = yes_no(ear_noise)
        Hypoacusis = yes_no(hearing_loss)
        Diplopia = yes_no(double_vision)
        Paresthesia = yes_no(pricking_sensation)

        # Prepare input for model
        column_names = ["Age", "Frequency", "Nausea", "Vomit", "Phonophobia", "Photophobia",
                        "Vertigo", "Tinnitus", "Hypoacusis", "Diplopia", "Paresthesia"]

        arr = np.array([[Age, Frequency, Nausea, Vomit, Phonophobia, Photophobia,
                         Vertigo, Tinnitus, Hypoacusis, Diplopia, Paresthesia]])

        arr_df = pd.DataFrame(arr, columns=column_names)

        print(f"Input Array: {arr_df}")  # Debugging

        # Make prediction using the migraine model
        pred = migrainemodel.predict(arr_df)

        print(f"Prediction: {pred}")  # Debugging

        if pred[0] == 1:
            disease_status = "Migraine"
            print("hi");
        else:
            disease_status = "No Migraine"

        # Generate recommendation response
        prompt = f"Suggest some recommendations for {disease_status} patient after mentioning which disease he has along with recommendations as paragraphs. If the patient does not have any disease, leave it."

        response = lient.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )

        response_text = response.choices[0].message.content

        return jsonify({'reply': response_text})

    except Exception as e:
        print(f"Error in /give: {str(e)}")  # Logs error to console
        return jsonify({'error': str(e)}), 500

@app.route("/enter", methods=['POST', 'GET'])
def enter():
    try:
        # Get JSON data
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data received'}), 400

        print(f"Received data: {data}")  # Debugging

        # Extracting form data with default values
        age = data.get('age', "0")
        acd_pressure = data.get('acd_pressure', "0")
        cgpa = data.get('cgpa', "0.0")
        study_hours = data.get('study_hours', "0")
        fin_stress = data.get('fin_stress', "0")
        sleep_data = data.get('sleep', "unknown")
        diet_data = data.get('diet', "unknown")
        smoke = data.get('suicide', "no")  # Assuming it's about suicide thought
        mental_ill = data.get('mental_ill', "no")
        gender_data = data.get('gender', "unknown")

        # Convert input values safely
        try:
            Age = float(age) if age.replace('.', '', 1).isdigit() else 0
            Academic_Pressure = float(acd_pressure) if acd_pressure.replace('.', '', 1).isdigit() else 0
            CGPA = float(cgpa) if cgpa.replace('.', '', 1).isdigit() else 0
            StudyHours = float(study_hours) if study_hours.replace('.', '', 1).isdigit() else 0
            Financial_Stress = float(fin_stress) if fin_stress.replace('.', '', 1).isdigit() else 0
        except ValueError:
            return jsonify({'error': 'Invalid numeric values'}), 400

        # Map categorical inputs using helper functions
        Sleep_Duration = sleepy(sleep_data)
        Dietary_Habits = diet_habit(diet_data)
        Suicide = yes_no(smoke)
        Mental_Illness_History = yes_no(mental_ill)
        Gender = gender(gender_data)

        # Prepare input DataFrame for model
        column_names = ["Age", "Academic_Pressure", "CGPA", "StudyHours", "Financial_Stress", 
                        "Sleep_Duration", "Dietary_Habits", "Suicide", "Mental_Illness_History", "Gender"]

        arr = [[Age, Academic_Pressure, CGPA, StudyHours, Financial_Stress, 
                Sleep_Duration, Dietary_Habits, Suicide, Mental_Illness_History, Gender]]

        arr_df = pd.DataFrame(arr, columns=column_names)

        print(f"Input Array: {arr_df}")  # Debugging

        # Make prediction using the depression model
        pred = depressionmodel.predict(arr_df.values)

        print(f"Prediction: {pred}")  # Debugging
# After prediction:
        if pred[0] == 1:
            disease_status = "Depression"
        else:
            disease_status = "No Depression"

        prompt = f"Suggest some recommendations for {disease_status} patient after mentioning which disease he has along with recommendations as paragraphs. If the patient does not have any disease, leave it."

        response = lient.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )

        response_text = response.choices[0].message.content
        print(response_text)
        return jsonify({'reply': response_text})

    except Exception as e:
        print(f"Error in /enter: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
if __name__ == "__main__":
    app.run(debug=True, port=5000)