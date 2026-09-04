import streamlit as st
import cv2
import numpy as np
import requests
from PIL import Image
from deepface import DeepFace

st.set_page_config(
    page_title="DocGuard AI - Offline Verification Suite",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ DocGuard AI: Passport Verification & ArcFace Matching")
st.markdown("---")

# Backend API Endpoint
API_URL = "http://127.0.0.1:8000/api/v1/verify-mrz"

col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Step 1: Upload Passport Scan")
    uploaded_passport = st.file_uploader("Choose Passport Image (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_passport:
        passport_image = Image.open(uploaded_passport)
        st.image(passport_image, caption="Uploaded Passport Document", width="stretch")

with col2:
    st.subheader("📸 Step 2: Live Traveler Face Capture")
    enable_camera = st.checkbox("Enable Local Webcam")
    camera_image = None
    
    if enable_camera:
        camera_image = st.camera_input("Capture Live Photo")

st.markdown("---")

if st.button("🚀 Run Full Verification Routine"):
    if not uploaded_passport:
        st.error("Please upload a passport image to proceed.")
    else:
        with st.spinner("Analyzing MRZ Checksums, ELA Image Compression, and ArcFace Embeddings..."):
            
            # 1. Reset buffer pointer and read original file bytes
            uploaded_passport.seek(0)
            raw_pass_bytes = uploaded_passport.read()
            
            # 2. Post file to local FastAPI backend
            files = {"file": (uploaded_passport.name, raw_pass_bytes, uploaded_passport.type)}
            try:
                response = requests.post(API_URL, files=files)
                api_result = response.json()
            except Exception as e:
                st.error(f"Cannot connect to FastAPI server at {API_URL}. Make sure 'uvicorn main:app' is running.")
                st.stop()
                
            # 3. Render Verification Metrics
            st.subheader("📊 Forensic Analysis Report")
            m1, m2, m3 = st.columns(3)
            
            ela_info = api_result.get("ela_image_forensics") or api_result.get("ela_forensics", {})
            ela_status = ela_info.get("ela_status", "N/A")
            mrz_status = api_result.get("mrz_validation_results", {}).get("mrz_checksum_status", "EXTRACTION FAILED")
            overall = api_result.get("overall_document_integrity", "FAILED")
            
            m1.metric("MRZ Data Checksum", mrz_status)
            m2.metric("ELA Forgery Check", ela_status)
            m3.metric("Final Document Verdict", overall)
            
            with st.expander("🔍 View Detailed JSON Payload"):
                st.json(api_result)
                
            # 4. Strict ArcFace 1:1 Facial Matching
            # 4. Strict ArcFace 1:1 Facial Matching
            if camera_image:
                st.markdown("---")
                st.subheader("👤 ArcFace 1:1 Facial Matching Result")
                
                cam_bytes = camera_image.getvalue()
                
                # Decode BGR images from byte buffers
                pass_bgr = cv2.imdecode(np.frombuffer(raw_pass_bytes, np.uint8), cv2.IMREAD_COLOR)
                cam_bgr = cv2.imdecode(np.frombuffer(cam_bytes, np.uint8), cv2.IMREAD_COLOR)
                
                if pass_bgr is None or cam_bgr is None:
                    st.error("Error decoding uploaded images. Please re-upload clean JPG/PNG files.")
                else:
                    # Convert BGR (OpenCV) to RGB (DeepFace expected format)
                    pass_rgb = cv2.cvtColor(pass_bgr, cv2.COLOR_BGR2RGB)
                    cam_rgb = cv2.cvtColor(cam_bgr, cv2.COLOR_BGR2RGB)
                    
                    try:
                        # ArcFace matching using 'skip' detector to bypass OpenCV DNN/Cascade dependencies
                        face_verify = DeepFace.verify(
                            img1_path=pass_rgb,
                            img2_path=cam_rgb,
                            model_name="ArcFace",
                            detector_backend="skip",
                            enforce_detection=False,
                            distance_metric="cosine"
                        )
                        
                        is_matched = face_verify.get("verified", False)
                        distance = round(float(face_verify.get("distance", 1.0)), 4)
                        
                        # Strict Cosine Distance Cutoff (< 0.68 indicates a true match)
                        if is_matched and distance < 0.65:
                            st.success(f"✅ FACE MATCH CONFIRMED (ArcFace Distance Score: {distance})")
                        else:
                            st.error(f"❌ FACE MISMATCH DETECTED (ArcFace Distance Score: {distance})")
                            
                    except Exception as e:
                        st.error(f"Facial Matching Engine Error: {str(e)}")