import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

# Realistic dataset of links from government portals to train the ML model
data = [
    # Class 1: Direct Apply/Registration Links
    ("https://upsconline.nic.in/ora/candidate/registration.php", "UPSC New Candidate Registration ORA", 1),
    ("https://ssc.gov.in/login", "SSC Direct Login and Apply Portal", 1),
    ("https://ibpsonline.ibps.in/crp-so-nov23/registration.php", "IBPS SO Apply Online Form", 1),
    ("https://recruitment.stpi.in/register", "STPI Online Registration Form", 1),
    ("https://bank.sbi/web/careers/apply-online", "SBI SO Specialist Apply Online Button", 1),
    ("https://rac.gov.in/apply", "DRDO Scientist B Online Application Form", 1),
    ("https://careers.ecil.co.in/login.php", "ECIL GET Direct Registration & Login", 1),
    ("https://www.joinindiannavy.gov.in/en/account/login", "Indian Navy Candidate Apply Login Page", 1),
    ("https://register-delhi.nielit.gov.in/", "NIELIT Scientist B Apply Portal Registration", 1),
    ("https://www.rrbapply.gov.in/", "RRB Recruitment Application Login", 1),
    ("https://exams.nta.ac.in/UGC-NET/register", "UGC NET Apply Registration Link", 1),
    ("https://internal.bsnl.co.in/apply", "BSNL Recruitment Registration Form Portal", 1),
    
    # Class 0: Generic Pages / Home Pages / Non-Application links
    ("https://upsc.gov.in/", "UPSC Home Page Union Public Service Commission", 0),
    ("https://ssc.gov.in/noticeboard", "SSC Noticeboard PDF Notification circular", 0),
    ("https://www.isro.gov.in/Careers.html", "ISRO Careers Current Openings Index page", 0),
    ("https://www.nic.in/careers/", "NIC Careers General Page vacancies", 0),
    ("https://www.railtel.in/careers/current-openings.html", "RailTel Vacancies Current List", 0),
    ("https://licindia.in/careers", "LIC Insurance General Careers Homepage", 0),
    ("https://uidai.gov.in/en/about-uidai/work-with-uidai.html", "UIDAI Work with Aadhaar recruitment", 0),
    ("https://www.powergrid.in/careers", "Power Grid Corporation Careers portal", 0),
    ("https://www.cdac.in/index.aspx?id=contact", "C-DAC Contact Us addresses map", 0),
    ("https://www.hal-india.co.in/disclaimer.aspx", "HAL Disclaimer policies website rules", 0),
    ("https://facebook.com/govtjobs", "Share on Facebook profile page link", 0),
    ("https://twitter.com/upschq", "UPSC Twitter Handle account updates", 0),
]

df = pd.DataFrame(data, columns=["url", "text", "label"])

# Combine URL and Text into features
df["combined_features"] = df["url"] + " " + df["text"]

# Train TF-IDF + Logistic Regression pipeline
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1, 2), token_pattern=r'(?u)\b\w+\b')),
    ('clf', LogisticRegression())
])

pipeline.fit(df["combined_features"], df["label"])

# Save the trained ML model pipeline to disk
with open("ai-service/model_pipeline.pkl", "wb") as f:
    pickle.dump(pipeline, f)

print("✅ AI/ML link classification model pipeline trained and saved successfully.")
