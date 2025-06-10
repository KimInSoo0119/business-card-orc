import cv2
import easyocr
import re

# === 0️⃣ 공통 교정 사전 ===
COMMON_OCR_ERRORS = {
    '콩': '홍',
    '훙': '홍',
    '굉': '홍',
    '곡': '홍'
    # 필요시 추가 확장 가능
}

# 1️⃣ 이미지 전처리 (한글 인식률 개선)
def preprocess_image(image_path):
    img = cv2.imread(image_path)
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Noise reduction + edge preserving
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    # Adaptive Threshold
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )
    return thresh

# 2️⃣ EasyOCR 추출
def extract_texts_with_boxes(image):
    reader = easyocr.Reader(['ko', 'en'])  # 한글 + 영어
    results = reader.readtext(image)
    return results

# 3️⃣ 이메일 기반 회사명 추출
def extract_company_from_email(email):
    match = re.search(r'@([A-Za-z0-9\-]+)\.', email)
    if match:
        company_candidate = match.group(1)
        company_candidate = company_candidate.replace('-', '').upper()
        return company_candidate
    return None

# 💡 OCR 오류 교정 + 괄호 정규화
def clean_company_text(text):
    # 작은 따옴표 제거
    text = text.replace("'", "").replace("'", "").replace("'", "")
    # 괄호 정규화 (유니코드 괄호 → ASCII 괄호)
    text = text.replace("（", "(").replace("）", ")").replace("【", "(").replace("】", ")")
    # OCR 오류 교정
    text = text.replace('(쥐', '(주)').replace('(주', '(주)').replace('(쥬', '(주)').replace('쥐식회사', '주식회사').replace('쥬식회사', '주식회사')
    return text.strip()

# 4️⃣ 패턴 기반 회사명 추출
def extract_company_from_patterns(results):
    company_patterns = [
        r'\(주\).*',
        r'주식회사.*',
        r'\bInc\b\s*\S+',
        r'\bInc\.\b\s*\S+',
        r'\bCo\.\b\s*\S+',
        r'\bLtd\b\s*\S+',
        r'\bLLC\b\s*\S+',
        r'유한회사.*'
    ]

    # 1️⃣ line 기반 확인
    for _, text, _ in results:
        clean_text = clean_company_text(text)
        print(f"[DEBUG CLEAN TEXT] {clean_text}")  # 디버그 확인

        for pattern in company_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                company = match.group().strip()
                print(f"[DEBUG MATCH] {company}")  # 디버그 확인
                return company

    # 2️⃣ full_text 기반 확인
    full_text = " ".join([clean_company_text(text) for _, text, _ in results])
    for pattern in company_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            company = match.group().strip()
            print(f"[DEBUG MATCH - FULL TEXT] {company}")  # 디버그 확인
            return company

    return None

# 5️⃣ 이름 추출 (한글 우선 + 교정 적용)
def extract_name_from_patterns(results, exclude_texts):
    hangul_name_patterns = [
        r'이름[:：]?\s*([가-힣\s]{2,8})',
        r'^([가-힣\s]{2,8})$',
        r'([가-힣]{2,4})\s+[A-Za-z]{2,}'
    ]

    english_name_patterns = [
        r'Name[:：]?\s*([A-Za-z]{2,}\s+[A-Za-z]{2,})',
        r'^([A-Za-z]{2,}\s+[A-Za-z]{2,})$'
    ]

    # 1️⃣ 한글 이름 패턴 우선
    for _, text, _ in results:
        for pattern in hangul_name_patterns:
            match = re.search(pattern, text)
            if match:
                corrected_name = match.group(1).replace(" ", "").strip()
                # 교정 사전 적용
                for wrong, correct in COMMON_OCR_ERRORS.items():
                    corrected_name = corrected_name.replace(wrong, correct)
                return corrected_name

    # 2️⃣ 영문 이름 패턴
    for _, text, _ in results:
        for pattern in english_name_patterns:
            match = re.search(pattern, text)
            if match:
                corrected_name = match.group(1).strip()
                return corrected_name

    # 3️⃣ fallback 휴리스틱
    candidate_names = []
    for _, text, _ in results:
        stripped_text = text.strip()
        no_space_text = stripped_text.replace(" ", "")

        if (
            stripped_text not in exclude_texts
            and 2 <= len(no_space_text) <= 10
            and not re.search(r'\d', stripped_text)
            and '@' not in stripped_text
            and re.search(r'[가-힣A-Za-z]', stripped_text)
        ):
            # 교정 사전 적용
            corrected_text = no_space_text
            for wrong, correct in COMMON_OCR_ERRORS.items():
                corrected_text = corrected_text.replace(wrong, correct)

            candidate_names.append(corrected_text)

    return candidate_names[0] if candidate_names else None

# 6️⃣ 정보 종합 추출
def extract_info(results):
    full_text = " ".join([clean_company_text(text) for _, text, _ in results])

    phone_match = re.search(r'\d{2,3}-\d{3,4}-\d{4}', full_text)
    phone = phone_match.group() if phone_match else None

    email_match = re.search(r'[\w\.-]+@[\w\.-]+', full_text)
    email = email_match.group() if email_match else None

    company_from_pattern = extract_company_from_patterns(results)
    company_from_email = extract_company_from_email(email) if email else None
    company = company_from_pattern if company_from_pattern else company_from_email

    exclude_texts = set()
    if company:
        exclude_texts.add(company)
    if email:
        exclude_texts.add(email)
    if phone:
        exclude_texts.add(phone)

    name = extract_name_from_patterns(results, exclude_texts)

    return {
        'name': name,
        'phone': phone,
        'email': email,
        'company': company
    }

# 7️⃣ 최종 프로세스 함수
def process_business_card(image_path):
    img = preprocess_image(image_path)
    results = extract_texts_with_boxes(img)

    print("===== OCR Results =====")
    for r in results:
        print(r)

    info = extract_info(results)
    return info