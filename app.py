import os
from flask import Flask, render_template, request, redirect, url_for, flash
from PIL import Image
import numpy as np
import pickle
import pandas as pd
import cv2
from datetime import datetime
import uuid
from tensorflow.keras.models import load_model
from utils.mail import mail, send_mail

# Database + Login
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from tensorflow.keras.layers import Input, Conv2D
from tensorflow.keras.models import Model

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "secretkey"

# ---------------- MAIL CONFIGURATION ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ir1793748@gmail.com'
app.config['MAIL_PASSWORD'] = 'iusktbawczzzuobx'
app.config['MAIL_DEFAULT_SENDER'] = 'ir1793748@gmail.com'
mail.init_app(app)

UPLOAD_FOLDER = os.path.join("static", "uploads")
REPORT_FOLDER = os.path.join("static", "reports")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ---------- DATABASE ----------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False) 
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(150)) 
    patient_name = db.Column(db.String(150))
    
from datetime import datetime

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    disease = db.Column(db.String(100))
    confidence = db.Column(db.Float)
    status = db.Column(db.String(50), default="Pending")

    user_id = db.Column(db.Integer)
    username = db.Column(db.String(150))
    patient_name = db.Column(db.String(150))

    # ✅ NEW COLUMN
    report_path = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------- LOAD MODEL & ENCODER ----------
def sequential_to_functional(sequential_model):
    inp = Input(shape=sequential_model.input_shape[1:])
    out = sequential_model(inp)
    return Model(inputs=inp, outputs=out)

_seq_model = load_model("models/hqcnn_medical_model.keras", compile=False)
model = sequential_to_functional(_seq_model)
_ = model.predict(np.zeros((1, 64, 64, 3)))
with open("models/label_encoder.pkl", "rb") as f:
    encoder = pickle.load(f)
metadata = pd.read_csv("data/HAM10000_metadata.csv")


print(model.summary())
submodel = model.layers[1]   # if your first layer is input, second is model
print([ (l.name, l.__class__.__name__) for l in submodel.layers ])
  
  
# ---------- DISEASE INFO ----------
disease_causes = {
    "mel": {"full_form": "Melanoma", "cause": "Excessive UV radiation exposure"},
    "bcc": {"full_form": "Basal Cell Carcinoma", "cause": "Prolonged sun exposure"},
    "nv": {"full_form": "Melanocytic Nevi", "cause": "Pigment cell growth"},
    "akiec": {"full_form": "Actinic Keratoses", "cause": "Chronic sun damage"},
    "vasc": {"full_form": "Vascular Lesions", "cause": "Blood vessel abnormality"},
    "df": {"full_form": "Dermatofibroma", "cause": "Minor skin injury"},
    "bkl": {"full_form": "Benign Keratosis", "cause": "Aging & sun exposure"}
}

# ---------- IMAGE PREPROCESS ----------
def preprocess(img_path):
    img = Image.open(img_path).convert("RGB")
    img = img.resize((64, 64))
    img = np.array(img) / 255.0
    img = np.expand_dims(img, axis=0)
    return img

# ---------- ROUTES ----------
@app.route("/")
def front():
    return render_template("front.html")

@app.route("/home")
@login_required
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        
        name = request.form.get("name")
        username = request.form.get("username")
        email = request.form.get("email") 
        password = request.form.get("password")
        role = request.form.get("role")

        if not name or not username or not password or not role:
            flash("Please fill all fields")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("User already exists")
            return redirect(url_for("register"))

        hashed_pw = generate_password_hash(password)

        # ✅ THIS IS THE CORRECT LINE
        new_user = User(
            name=name,
            username=username,
            email=email,
            password=hashed_pw,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful!")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            elif user.role == "doctor":
                return redirect(url_for("doctor_dashboard"))
            else:
                return redirect(url_for("home"))
        else:
            flash("Invalid Username or Password")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout Successfully")
    return redirect(url_for("front"))

@app.route("/approve/<int:id>")
@login_required
def approve(id):
    if current_user.role != "doctor":
        return redirect(url_for("home"))

    record = Prediction.query.get_or_404(id)

    # 🚫 Prevent re-action
    if record.status != "Pending":
        flash("Action already taken!")
        return redirect(url_for("doctor_dashboard"))

    record.status = "Approved"
    db.session.commit()
    return redirect(url_for("doctor_dashboard"))

@app.route("/reject/<int:id>")
@login_required
def reject(id):
    if current_user.role != "doctor":
        return redirect(url_for("home"))

    record = Prediction.query.get_or_404(id)

    # 🚫 Prevent re-action
    if record.status != "Pending":
        flash("Action already taken!")
        return redirect(url_for("doctor_dashboard"))

    record.status = "Rejected"
    db.session.commit()
    return redirect(url_for("doctor_dashboard"))

@app.route("/patient_dashboard")
@login_required
def patient_dashboard():
    search = request.args.get("search")

    if search:
        records = Prediction.query.filter(
            Prediction.patient_name.ilike(f"%{search}%")
        ).order_by(Prediction.timestamp.desc()).all()
    else:
        records = Prediction.query.order_by(Prediction.timestamp.desc()).all()

    return render_template("patient_dashboard.html", records=records)

# ---------- PREDICTION ----------
@app.route('/predict', methods=['POST'])
@login_required
def predict():
    if 'file' not in request.files or request.files['file'].filename == '':
        flash("No file uploaded")
        return redirect(url_for("home"))

    file = request.files['file']
    ext = os.path.splitext(file.filename)[1]
    secure_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    filename = f"{secure_id}{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # --- Prediction ---
    img = preprocess(filepath)
    prediction = model.predict(img)
    confidence = float(np.max(prediction))
    
    
    disease_code = encoder.inverse_transform([np.argmax(prediction)])[0]
    disease_full = disease_causes[disease_code]["full_form"]
    disease_reason = disease_causes[disease_code]["cause"]

    # --- Metadata ---
    sample = metadata.sample(1)
    predicted_age = sample["age"].values[0]
    predicted_sex = sample["sex"].values[0]
    predicted_localization = sample["localization"].values[0]



    print("Current user name:", current_user.name)
    
    print("Raw prediction:", prediction)
    print("Predicted index:", np.argmax(prediction))
    print("Classes:", encoder.classes_)
    # --- Severity calculation ---
    from utils.severity import severity_stage
    severity = severity_stage(confidence)

    # --- Heatmap Generation ---
    from utils.heatmap import generate_heatmap, overlay_heatmap
    print("Heatmap functions loaded successfully")
    # 🔥 Access inner Sequential model
    submodel = model.layers[1]

# 🔥 Get Conv layers inside it
    conv_layers = [layer for layer in submodel.layers if isinstance(layer, Conv2D)]

    if not conv_layers:
       raise ValueError("No Conv2D layers found inside submodel!")

    last_conv_layer_name = conv_layers[-1].name

    print("Using last conv layer:", last_conv_layer_name)
    heatmap_path = ""
    try:
        original_img = cv2.imread(filepath)
        if original_img is None:
            raise RuntimeError("Image could not be loaded by cv2.")
        original_img = cv2.resize(original_img, (64, 64))
        img_for_heatmap = original_img.astype("float32") / 255.0
        heatmap = generate_heatmap(img_for_heatmap, model, last_conv_layer_name)
        overlay = overlay_heatmap(original_img, heatmap)
        heatmap_filename = f"heatmap_{filename}.png"
        heatmap_save_path = os.path.join(UPLOAD_FOLDER, heatmap_filename)
        cv2.imwrite(heatmap_save_path, overlay)
        heatmap_path = f"static/uploads/{heatmap_filename}"
    except Exception as e:
        print(f"Heatmap generation failed: {e}")
        heatmap_path = ""
        
    print("Heatmap path:", heatmap_path)

    # --- PDF Report ---
    from utils.report import generate_report
    report_filename = f"report_{filename}.pdf"
    report_full_path = os.path.join(REPORT_FOLDER, report_filename)
    generate_report(report_full_path, disease_full, confidence, severity)
    report_path = f"static/reports/{report_filename}"
    image_path = f"static/uploads/{filename}"
    
    # --- Save to DB (NOW CORRECT) ---
    new_prediction = Prediction(
       disease=disease_full,
       confidence=confidence,
       user_id=current_user.id,
       patient_name = current_user.name,
       username=current_user.name,
       report_path=report_path
    )

    db.session.add(new_prediction)
    db.session.commit()

    # --- Custom PDF report for email ---
    report_folder = "reports"
    os.makedirs(report_folder, exist_ok=True)
    pdf_path = os.path.join(report_folder, f"{secure_id}.pdf")
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    doc = SimpleDocTemplate(pdf_path)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph("<b>Hybrid Quantum Medical AI Report</b>", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Disease Predicted: {disease_full}", styles['Normal']))
    elements.append(Paragraph(f"Confidence: {round(confidence*100,2)}%", styles['Normal']))
    elements.append(Paragraph(f"Cause: {disease_reason}", styles['Normal']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Age: {predicted_age}", styles['Normal']))
    elements.append(Paragraph(f"Sex: {predicted_sex}", styles['Normal']))
    elements.append(Paragraph(f"Localization: {predicted_localization}", styles['Normal']))
    doc.build(elements)

    try:
        if current_user.role == "patient":
            send_mail(app, current_user.email, pdf_path)
    except Exception as e:
        print("Mail sending failed:", e)

    return render_template(
        "result.html",
        disease=disease_full,
        cause=disease_reason,
        confidence=confidence,
        severity=severity,
        heatmap=heatmap_path,
        report=report_path,
        image=image_path,
        age=predicted_age,
        sex=predicted_sex,
        localization=predicted_localization,
    )

@app.route("/heatmap")
def show_heatmap():
    heatmap_path = request.args.get("heatmap_path")
    return render_template("heatmap.html", heatmap=heatmap_path)

@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return redirect(url_for("home"))
    total_predictions = Prediction.query.count()
    total_users = User.query.count()
    disease_data = db.session.query(Prediction.disease, func.count(Prediction.disease)).group_by(Prediction.disease).all()
    labels = [d[0] for d in disease_data]
    values = [d[1] for d in disease_data]
    return render_template("dashboard.html", total_predictions=total_predictions, total_users=total_users, labels=labels, values=values)

@app.route("/doctor_dashboard")
@login_required
def doctor_dashboard():
    if current_user.role != "doctor":
        flash("Unauthorized Access")
        return redirect(url_for("login"))
    records = Prediction.query.all()
    return render_template("doctor_dashboard.html", records=records)



@app.route("/result/<int:prediction_id>")
@login_required
def view_result(prediction_id):
    record = Prediction.query.get_or_404(prediction_id)
    return render_template("result.html", disease=record.disease, confidence=record.confidence, status=record.status)

@app.route("/quantum_visual")
@login_required
def quantum_visual():
    return render_template("quantum_visual.html")

@app.route("/quantum")
@login_required
def quantum_page():
    quantum_plot = "static/uploads/sample_quantum.png"
    return render_template("quantum.html", quantum_plot=quantum_plot)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()
