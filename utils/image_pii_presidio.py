import cv2
import pytesseract
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern, RecognizerResult
from presidio_anonymizer import AnonymizerEngine
import re

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# 1. URL Recognizer (works for www, http, https, etc.)
url_pattern = Pattern(
    name="url_pattern",
    regex=r"(https?:\/\/)?(www\.)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(\/[^\s]*)?",
    score=0.9
)
url_recognizer = PatternRecognizer(supported_entity="URL", patterns=[url_pattern])
analyzer.registry.add_recognizer(url_recognizer)

# 2. Hospital Name Recognizer
hospital_keywords = ["hospital", "clinic", "medical center", "nursing home"]
hospital_pattern = Pattern(
    name="hospital_pattern",
    regex=r"\\b([A-Z][a-z]+ )*(Hospital|Clinic|Medical Center|Nursing Home)\\b",
    score=0.85
)


hospital_recognizer = PatternRecognizer(supported_entity="HOSPITAL", patterns=[hospital_pattern])
analyzer.registry.add_recognizer(hospital_recognizer)


# 3. Patient Name Recognizer (simple heuristic: capitalized words, titles)
patient_name_pattern = Pattern(
    name="patient_name_pattern",
    regex=r"(Patient\s*Name\s*[:\-]?\s*[A-Z][a-zA-Z]+\s*[A-Z]?[a-zA-Z]*)|(Mr\.|Mrs\.|Miss\s+[A-Z][a-zA-Z]+)",
    score=0.9
)

patient_name_recognizer = PatternRecognizer(
    supported_entity="PATIENT_NAME",
    patterns=[patient_name_pattern]
)
analyzer.registry.add_recognizer(patient_name_recognizer)


# 4. Doctor Name Recognizer (similar to patient but with "Dr." prefix)
doctor_name_pattern = Pattern(
    name="doctor_name_pattern",
    regex=r"\b(?:Dr|Doctor|Prof|Sir|Madam)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b",
    score=0.8,
)

doctor_name_recognizer = PatternRecognizer(
    supported_entity="DOCTOR_NAME",
    patterns=[doctor_name_pattern],
    context=["doctor", "physician", "consultant", "specialist"]
)
analyzer.registry.add_recognizer(doctor_name_recognizer)

# 5. Email Recognizer (custom pattern)
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}"

# Presidio pattern recognizer for email
email_pattern = Pattern(name="email_pattern", regex=EMAIL_REGEX, score=0.8)

# Custom recognizer for Email
email_recognizer = PatternRecognizer(
    supported_entity="EMAIL_CUSTOM",  # aap apna naam de sakte ho
    patterns=[email_pattern]
)
analyzer.registry.add_recognizer(email_recognizer)

# 6. Contact Number Recognizer (custom pattern)
contact_number_pattern = Pattern(
    name="contact_number_pattern",
    regex=r"(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{6,10}",
    score=0.6,
)

contact_number_recognizer = PatternRecognizer(
    supported_entity="CONTACT_NUMBER",
    patterns=[contact_number_pattern],
)
analyzer.registry.add_recognizer(contact_number_recognizer)

# 7. Fax Number Recognizer (custom pattern)
fax_number_pattern = Pattern(
    name="fax_number_pattern",
    regex=r"(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{6,10}",
    score=0.6,
)

fax_number_recognizer = PatternRecognizer(
    supported_entity="FAX_NUMBER",
    patterns=[fax_number_pattern],
)
analyzer.registry.add_recognizer(fax_number_recognizer)


# 8. Address Recognizer (custom pattern)
address_pattern = Pattern(
    name="address_pattern",
    regex=r"(\b(House\s*No\.?|H\.?No\.?|Flat\s*No\.?|Street|St\.|Road|Rd\.|Colony|Nagar|Ward|Block|Sector|Avenue|Lane|Hospital|Clinic|Medical\s*Center)\b[\s\S]{0,40}(\d{6}|\d{5}(-\d{4})?))",
    score=0.85
)

address_recognizer = PatternRecognizer(
    supported_entity="ADDRESS",
    patterns=[address_pattern],
    context=["address", "location", "residence", "hospital", "clinic", "colony", "ward"]
)
analyzer.registry.add_recognizer(address_recognizer)


# 9. Date Recognizer (custom pattern)
date_pattern = Pattern(name="date_pattern",
    regex=r"\b(?:\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}|\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})\b",
    score=0.6)

date_recognizer = PatternRecognizer(
    supported_entity="DATE",
    patterns=[date_pattern],
    context=["date", "dob", "admission", "discharge"]
)
analyzer.registry.add_recognizer(date_recognizer)


# 10. Age Recognizer (custom pattern)
age_pattern = Pattern(name="age_pattern",
    regex=r"\b(?:[1-9][0-9]?|1[01][0-9]|120)\s?(years|yrs|year old|y/o)\b",
    score=0.6)

age_recognizer = PatternRecognizer(
    supported_entity="AGE",
    patterns=[age_pattern],
    context=["age"]
)
analyzer.registry.add_recognizer(age_recognizer)


# 11. ID Number Recognizer (Aadhaar, PAN, Passport, MRN)
id_patterns = [
    Pattern(name="aadhaar", regex=r"\b\d{4}\s\d{4}\s\d{4}\b", score=0.7),
    Pattern(name="pan", regex=r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", score=0.7),
    Pattern(name="passport", regex=r"\b[A-PR-WYa-pr-wy][1-9]\d\s?\d{4}[1-9]\b", score=0.7),
    Pattern(name="mrn", regex=r"\bMRN[:\s]?\d{6,10}\b", score=0.6)
]

id_recognizer = PatternRecognizer(
    supported_entity="ID_NUMBER",
    patterns=id_patterns,
    context=["id", "aadhaar", "passport", "pan", "mrn", "insurance"]
)
analyzer.registry.add_recognizer(id_recognizer)

def mask_logo(image):
    h, w, _ = image.shape
    # Mask top 15% area (logo/header zone)
    cv2.rectangle(image, (0,0), (w, int(h*0.15)), (0,0,0), -1)
    cv2.putText(image, "<LOGO/HEADER>", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    return image

def mask_signature(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = image.shape[:2]
    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        # Filter: likely signature = wide & low height, near bottom
        if ch < 80 and cw > 100 and y > int(h*0.7):
            cv2.rectangle(image, (x,y), (x+cw,y+ch), (0,0,0), -1)
            cv2.putText(image, "<SIGNATURE>", (x,y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
    return image


# ---------------------------
# OCR and Image Anonymization
# ---------------------------




# def anonymize_image(image_path, output_path):
#     image = cv2.imread(image_path)

#     # 1. Mask PII text (already via Presidio)
#     # ... (existing OCR + analyzer code)

    

#     cv2.imwrite(output_path, image)







def anonymize_image(image_path, output_path):
    image = cv2.imread(image_path)


    # 2. Mask Logo/Header
    image = mask_logo(image)

    # 3. Mask Barcode/QR
    
    # 4. Mask Signatures
    image = mask_signature(image)

    boxes = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config="--psm 6")
    n = len(boxes['text'])

    for i in range(n):
        word = boxes['text'][i].strip()
        if not word:
            continue

        # Run analyzer only once per word (can be extended to line level)
        pii_results = analyzer.analyze(text=word, language='en')

        for result in pii_results:
            if result.score >= 0.75:  # Higher threshold
                x, y, w, h = boxes['left'][i], boxes['top'][i], boxes['width'][i], boxes['height'][i]

                # Black rectangle masking instead of blur (faster & clear)
                cv2.rectangle(image, (x, y), (x+w, y+h), (0, 0, 0), -1)
                cv2.putText(image, "<PII>", (x, y+h-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.imwrite(output_path, image)

