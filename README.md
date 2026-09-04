# 🛡️ AI-Based Fake Identity Detector System (DocGuard AI)

An enterprise-grade, fully offline passport verification and identity authentication suite designed for high-security border control and document verification pipelines. 

The system combines Machine Readable Zone (MRZ) structural parsing, Error Level Analysis (ELA) image forensics, and ArcFace 1:1 facial biometric matching into a local interactive dashboard backed by an API engine.

---

## 🚀 Key Features

* **MRZ Checksum & Parsing**: Extracts document details and validates structural integrity using Modulus 10 check digits.
* **Error Level Analysis (ELA) Forensics**: Detects digital image tampering, photo swapping, and text edits by analyzing compression artifacts.
* **ArcFace 1:1 Biometric Facial Matching**: Extracts 512-dimensional facial embeddings to perform strict cosine-similarity matching between the passport photo and a live webcam feed.
* **Offline Audit Logging**: Writes all verification checks, timestamps, and integrity metrics to a local SQLite database for compliance and auditing.
* **Fully Offline Architecture**: Runs entirely on local hardware without sending sensitive personal data to external cloud APIs.

---

## 🛠️ Tech Stack

* **Frontend**: Streamlit
* **Backend API**: FastAPI, Uvicorn
* **Computer Vision & AI**: DeepFace (ArcFace Model), OpenCV, Pillow, NumPy
* **Database**: SQLite
* **Language**: Python 3.10+

---

## ⚙️ Installation & Setup

### 1. Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies
```Bash

pip install -r requirements.txt
pip install opencv-contrib-python
```
### 🚦 How to Run
Launch the backend API and frontend interface in separate terminal windows:

Terminal 1 : Launch the API Backend
```Bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Terminal 2 : Launch The Frontend App
```Bash
streamlit run app.py
```

Usage Workflow
Open http://localhost:8501 in your browser.

Step 1: Upload a passport document scan (.jpg or .png).

Step 2: Enable the local webcam and capture a live photograph of the traveler.

Click 🚀 Run Full Verification Routine.

Review the generated Forensic Analysis Report and ArcFace 1:1 Biometric Match verdict.
