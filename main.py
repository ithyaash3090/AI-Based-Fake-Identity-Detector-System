import io
import cv2
import numpy as np
import pytesseract
import re
from PIL import Image, ImageChops, ImageEnhance
from fastapi import FastAPI, UploadFile, File, HTTPException

# Explicitly set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = FastAPI(
    title="DocGuard AI Core Engine",
    description="Offline Dual-Path Passport Verification API (MRZ + ELA Forgery Detection)",
    version="2.0.0"
)

# ---------------------------------------------------------
# PHASE 1: ICAO 9303 CHECKSUM CALCULATOR
# ---------------------------------------------------------
def calculate_icao_check_digit(mrz_string: str) -> int:
    """Calculates ICAO 9303 Modulus 10 check digit with zero-value filler handling."""
    weights = [7, 3, 1]
    total = 0
    
    for i, char in enumerate(mrz_string):
        if char == '<' or not char.isalnum():
            val = 0
        elif char.isdigit():
            val = int(char)
        elif char.isalpha():
            val = ord(char.upper()) - 55  # A=10, B=11, ..., Z=35
        else:
            val = 0
            
        total += val * weights[i % 3]
        
    return total % 10

def fix_mrz_digits(text: str) -> str:
    """Fixes common OCR letter-to-digit misread errors in numeric fields."""
    mapping = {'O': '0', 'Q': '0', 'D': '0', 'I': '1', 'L': '1', 'Z': '2', 'S': '5', 'B': '8'}
    return "".join(mapping.get(c, c) for c in text)


# ---------------------------------------------------------
# PHASE 2: ERROR LEVEL ANALYSIS (ELA) FORGERY DETECTOR
# ---------------------------------------------------------
def analyze_error_level(image_bytes: bytes, quality: int = 95) -> dict:
    """
    Performs Error Level Analysis (ELA) to detect digital tampering/editing.
    Resaves image at fixed compression quality and measures pixel difference variance.
    """
    original = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # Save image to temporary buffer with target JPEG quality
    buffer = io.BytesIO()
    original.save(buffer, "JPEG", quality=quality)
    buffer.seek(0)
    resaved = Image.open(buffer)
    
    # Calculate absolute difference between original and resaved image
    ela_image = ImageChops.difference(original, resaved)
    
    # Scale contrast to highlight subtle edits
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0:
        max_diff = 1
    
    scale = 255.0 / max_diff
    ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
    
    # Convert ELA image to NumPy array for mathematical metric extraction
    ela_np = np.array(ela_image)
    mean_ela_score = float(np.mean(ela_np))
    max_ela_score = float(np.max(ela_np))
    std_ela_score = float(np.std(ela_np))

    # Higher variance indicates localized compression anomalies (digital tampering)
    is_tampered = mean_ela_score > 35.0 or std_ela_score > 40.0

    return {
        "mean_error_score": round(mean_ela_score, 2),
        "max_error_score": round(max_ela_score, 2),
        "variance_score": round(std_ela_score, 2),
        "ela_tamper_detected": is_tampered,
        "ela_status": "POSSIBLE ALTERATION DETECTED" if is_tampered else "AUTHENTIC COMPRESSION PROFILE"
    }


# ---------------------------------------------------------
# API ROUTE
# ---------------------------------------------------------
@app.get("/")
def health_check():
    return {"status": "DocGuard AI Core Engine Online (100% Offline Mode)"}

@app.post("/api/v1/verify-mrz")
async def verify_passport_mrz(file: UploadFile = File(...)):
    """Extracts MRZ, performs ICAO Modulus 10 checksums, and runs ELA tampering detection."""
    
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image file uploaded.")

    # 1. Execute Phase 2: Error Level Analysis (ELA)
    ela_results = analyze_error_level(contents)

    # 2. Execute Phase 1: Preprocessing & OCR
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    if w < 1200:
        gray = cv2.resize(gray, (1200, int(h * (1200 / w))))

    ocr_config = r'--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<'
    raw_ocr_text = pytesseract.image_to_string(gray, config=ocr_config)

    mrz_lines = []
    for line in raw_ocr_text.split('\n'):
        cleaned_line = re.sub(r'[^A-Z0-9<]', '', line.strip().upper())
        if '<' in cleaned_line and len(cleaned_line) >= 20:
            mrz_lines.append(cleaned_line)

    if len(mrz_lines) < 2:
        return {
            "success": False,
            "message": "MRZ zone could not be extracted automatically.",
            "ela_forensics": ela_results,
            "raw_text_detected_by_ocr": raw_ocr_text
        }

    line2 = mrz_lines[-1]
    
    if len(line2) > 44:
        match = re.search(r'[A-Z0-9<]{44}', line2)
        line2 = match.group(0) if match else line2[:44]

    # Parse Fields
    raw_doc_num = line2[0:9] if len(line2) >= 10 else ""
    doc_num_check = fix_mrz_digits(line2[9]) if len(line2) >= 10 else ""

    raw_dob = line2[13:19] if len(line2) >= 20 else ""
    dob_check = fix_mrz_digits(line2[19]) if len(line2) >= 20 else ""

    raw_expiry = line2[21:27] if len(line2) >= 28 else ""
    expiry_check = fix_mrz_digits(line2[27]) if len(line2) >= 28 else ""

    doc_num = raw_doc_num
    dob = fix_mrz_digits(raw_dob)
    expiry = fix_mrz_digits(raw_expiry)

    # Run Checksums
    calc_num_check = str(calculate_icao_check_digit(doc_num)) if doc_num else ""
    calc_dob_check = str(calculate_icao_check_digit(dob)) if dob else ""
    calc_exp_check = str(calculate_icao_check_digit(expiry)) if expiry else ""

    num_valid = (calc_num_check == doc_num_check)
    dob_valid = (calc_dob_check == dob_check)
    exp_valid = (calc_exp_check == expiry_check)

    mrz_passed = num_valid and dob_valid and exp_valid
    overall_passed = mrz_passed and not ela_results["ela_tamper_detected"]

    return {
        "success": True,
        "mrz_lines_detected": mrz_lines,
        "extracted_fields": {
            "document_number": doc_num,
            "date_of_birth": dob,
            "expiration_date": expiry
        },
        "mrz_validation_results": {
            "document_number_checksum": "PASS" if num_valid else f"FAIL (Calc: {calc_num_check} vs Read: {doc_num_check})",
            "dob_checksum": "PASS" if dob_valid else f"FAIL (Calc: {calc_dob_check} vs Read: {dob_check})",
            "expiry_checksum": "PASS" if exp_valid else f"FAIL (Calc: {calc_exp_check} vs Read: {expiry_check})",
            "mrz_checksum_status": "VALID" if mrz_passed else "CHECKSUM FAILED"
        },
        "ela_image_forensics": ela_results,
        "overall_document_integrity": "PASSED ALL VERIFICATIONS" if overall_passed else "FLAGGED / SUSPECTED TAMPERING"
    }