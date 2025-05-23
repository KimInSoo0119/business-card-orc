from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from .models import insert_customer, get_customers, delete_customer
from bson import ObjectId
from .ocr import extract_text_from_image

class BusinessCardUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({'error': '이미지 파일이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        # 1. OCR로 텍스트 추출 (bytes로 변환)
        image_file.seek(0)
        text = extract_text_from_image(image_file.read())
        # 2. 정보 파싱
        customer_data = self.parse_ocr_text(text)
        # 3. 암호화/복호화 없이 바로 저장
        inserted = insert_customer(customer_data)
        # 4. ObjectId를 문자열로 변환해서 응답에 포함
        customer_data['_id'] = str(inserted.inserted_id)
        return Response(customer_data, status=status.HTTP_201_CREATED)

    def parse_ocr_text(self, text):
        """명함 텍스트에서 정보 추출"""
        name, company, email, phone = '', '', '', ''
        for line in text.split('\n'):
            if '@' in line and not email:
                email = line.strip()
            elif ('010' in line or '-' in line) and not phone:
                phone = line.strip()
            elif not name:
                name = line.strip()
            elif not company:
                company = line.strip()
        return {
            'name': name,
            'company': company,
            'email': email,
            'phone': phone
        }

class CustomerListView(APIView):
    """고객 정보 목록/필터 API (회사명 기준)"""
    def get(self, request):
        company = request.query_params.get('company')
        customers = get_customers(company)
        # ObjectId만 문자열로 변환
        for customer in customers:
            customer['_id'] = str(customer['_id'])
        return Response(customers)

class CustomerDeleteView(APIView):
    """고객 정보 삭제 API"""
    def delete(self, request, customer_id):
        deleted_count = delete_customer(customer_id)
        if deleted_count == 1:
            return Response({'message': '삭제 성공'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'error': '해당 고객을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

