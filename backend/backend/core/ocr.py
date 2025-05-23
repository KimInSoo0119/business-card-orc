import easyocr

reader = easyocr.Reader(['ko', 'en'])  # 한글/영어 지원

def extract_text_from_image(image_bytes):
    from easyocr import Reader
    reader = Reader(['ko', 'en'])
    result = reader.readtext(image_bytes)
    text = '\n'.join([item[1] for item in result])
    return text
