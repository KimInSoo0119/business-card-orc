import reflex as rx
import httpx
from typing import List, Dict, Any

# 1. 상태 클래스
class State(rx.State):
    filter_company: str = "전체"
    customers: List[Dict] = []
    companies: List[str] = ["전체"]
    upload_result: str = ""
    preview_url: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, "_upload_files", None)

    async def set_filter_company(self, company: str):
        self.filter_company = company
        await self.get_customers()


    async def get_customers(self):
        url = "http://localhost:8000/api/business-card/list/"
        params = {}
        if self.filter_company != "전체":
            params["company"] = self.filter_company
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
        if response.status_code == 200:
            self.customers = response.json()
            all_companies = {c["company"] for c in self.customers if c.get("company")}
            self.companies = ["전체"] + sorted(all_companies)
        else:
            self.customers = []
            self.companies = ["전체"]

    @rx.event
    async def handle_drop(self, files: Any):
        if not files:
            self.upload_result = "파일을 선택해주세요."
            return

        object.__setattr__(self, "_upload_files", files)

        file = files[0]
        if hasattr(file, "read"):
            update_file = await file.read()
            mime = getattr(file, "content_type", "application/octet-stream")
        else:
            update_file = file
            mime = "application/octet-stream"
        import base64
        encoded = base64.b64encode(update_file).decode("utf-8")
        self.preview_url = f"data:{mime};base64,{encoded}"

    @rx.event
    async def handle_upload(self):
        upload_files = getattr(self, "_upload_files", None)
        if not upload_files:
            self.upload_result = "파일이 선택되지 않았습니다."
            return
        file = upload_files[0]
        try:
            if hasattr(file, "read"):
                upload_data = await file.read()
                filename = getattr(file, "filename", "uploaded_file")
                content_type = getattr(file, "content_type", "application/octet-stream")
            else:
                upload_data = file
                filename = "uploaded_file"
                content_type = "application/octet-stream"

            url = "http://localhost:8000/api/business-card/"
            files_data = {'image': (filename, upload_data, content_type)}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, files=files_data)

            if response.status_code == 201:
                self.upload_result = f"{filename} 업로드 및 저장 성공!"
                await self.get_customers()
            else:
                self.upload_result = f"업로드 실패! ({response.status_code})"

        except Exception as e:
            self.upload_result = f"업로드 중 예외 발생: {str(e)}"

    @rx.event
    async def delete_customer(self, customer_id: str):
        url = f"http://localhost:8000/api/business-card/{customer_id}/"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(url)
        if response.status_code == 204:
            await self.get_customers()

    @rx.event
    async def reset_upload_state(self):
        self.preview_url = ""
        self.upload_result = ""
        object.__setattr__(self, "_upload_files", None)

# 2. 메인 페이지
def main_page():
    return rx.center(
        rx.vstack(
            rx.heading("💼 명함 관리 시스템", size="8", color="#f0f8ff"),
            rx.hstack(
                rx.link(
                    rx.button("📤 업로드", color_scheme="cyan", size="4", variant="solid", border_radius="full", box_shadow="xl"),
                    href="/upload"
                ),
                rx.link(
                    rx.button("📊 대시보드", color_scheme="cyan", size="4", variant="solid", border_radius="full", box_shadow="xl"),
                    href="/dashboard"
                ),
                spacing="8"
            ),
            rx.text(
                "명함 이미지를 업로드하고 고객 정보를 스마트하게 관리하세요.",
                font_size="2xl",
                color="#edf2f7",
                margin_top="40px",
                text_align="center",
                font_weight="medium"
            ),
            spacing="9",
            padding="80px",
            border_radius="28px",
            box_shadow="0 12px 48px rgba(0, 0, 0, 0.2)",
            background="rgba(255,255,255,0.1)"
        ),
        min_height="100vh",
        background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    )

# 3. 업로드 페이지
@rx.page(route="/upload", on_load=State.reset_upload_state)
def upload_page():
    upload_id = "upload1"
    return rx.center(
        rx.vstack(
            # 상단 헤더영역: 제목 + 내비게이션 버튼
            rx.hstack(
                rx.heading("📤 명함 업로드", size="6", color="#234e52"),
                rx.spacer(),
                rx.link(
                    rx.button("🏠 메인 페이지", color_scheme="red", variant="ghost"),
                    href="/"
                ),
                rx.link(
                    rx.button("📊 대시보드", color_scheme="red", variant="ghost"),
                    href="/dashboard"
                ),
                spacing="4",
                width="100%",
            ),

            # 업로드 박스 + 삭제 버튼(좌측 상단)
            rx.box(
                rx.upload(
                    rx.cond(
                        State.preview_url == "",
                        rx.vstack(
                            rx.icon("upload", size=32, color="#2c7a7b"),
                            rx.text("더블클릭후, 명함이미지를 선택해주세요.", font_weight="semibold", color="#2c7a7b")
                        )
                    ),
                    id=upload_id,
                    key=State.preview_url,
                    multiple=False,
                    accept={"image/png": [".png"], "image/jpeg": [".jpg", ".jpeg"]},
                    max_files=1,
                    min_height="186px",
                    min_width="404px",
                    border="3px dashed #2c7a7b",
                    padding="56px",
                    border_radius="20px",
                    margin_bottom="24px",
                    on_drop=State.handle_drop,
                    background=rx.cond(
                        State.preview_url != "",
                        "url({}) center/cover no-repeat".format(State.preview_url),
                        "#ebf8ff"
                    ),
                ),

                # 삭제 버튼 (이미지 왼쪽 상단)
                rx.cond(
                    State.preview_url != "",
                    rx.button(
                        "🗑️",
                        on_click=State.reset_upload_state,
                        position="absolute",
                        top="8px",
                        right="8px",
                        size="2",
                        color_scheme="red",
                        variant="solid",
                        border_radius="full",
                        box_shadow="lg",
                        _hover={"transform": "scale(1.1)", "transition": "all 0.2s"}
                    ),
                ),
                position="relative",
            ),

            # 업로드 실행 버튼
            rx.button(
                "업로드",
                on_click=State.handle_upload,
                color_scheme="teal",
                size="4",
                width="100%",
                border_radius="full",
                box_shadow="lg"
            ),

            # 업로드 결과 메시지
            rx.cond(
                State.upload_result != "",
                rx.box(
                    rx.text(State.upload_result, color="#2f855a", font_weight="bold"),
                    margin_top="24px",
                    padding="16px",
                    border_radius="12px",
                    background="#f0fff4",
                    box_shadow="0 4px 12px rgba(72, 187, 120, 0.4)"
                )
            ),
            spacing="6"
        ),
        min_height="100vh",
        background="linear-gradient(135deg, #a8edea, #fed6e3)"
    )

# 4. 대시보드 페이지
@rx.page(route="/dashboard", on_load=State.get_customers)
def dashboard_page():
    def customer_card(c):
        return rx.box(
            rx.vstack(
                rx.heading(c['name'], size="5", color="#ffffff"),
                rx.text(f"🏢 {c['company']}", font_size="lg", color="#e2e8f0"),
                rx.text(f"📧 {c['email']}", color="#cbd5e0"),
                rx.text(f"📞 {c['phone']}", color="#cbd5e0"),
                rx.button(
                    "삭제",
                    color_scheme="red",
                    size="2",
                    variant="solid",
                    border_radius="full",
                    box_shadow="md",
                    on_click=lambda: State.delete_customer(c['_id']),
                    margin_top="8px"
                ),
                spacing="3"
            ),
            border="1px solid #4a5568",
            border_radius="20px",
            padding="28px",
            margin="12px",
            background="rgba(255, 255, 255, 0.08)",
            box_shadow="0 6px 20px rgba(0,0,0,0.2)",
            _hover={
                "transform": "scale(1.05)",
                "box_shadow": "0 16px 32px rgba(144, 205, 244, 0.4)",
                "transition": "all 0.3s ease-in-out"
            },
            min_width="280px",
            max_width="360px"
        )

    return rx.center(
        rx.vstack(
            rx.hstack(
                rx.link(
                    rx.button("🏠 메인 페이지", color_scheme="gray", variant="ghost"),
                    href="/"
                ),
                rx.link(
                    rx.button("📤 업로드", color_scheme="gray", variant="ghost"),
                    href="/upload"
                ),
                spacing="4",
                justify="end",
                width="100%",
                padding_bottom="12px"
            ),
            rx.heading("📊 대시보드", size="6", color="#ffffff"),
            rx.select(
                items=State.companies,
                value=State.filter_company,
                on_change=State.set_filter_company,
                label="회사별 필터",
                size="3",
                width="320px",
                margin_bottom="32px",
                color="#2b6cb0"
            ),
            rx.grid(
                rx.foreach(State.customers, customer_card),
                columns="3",
                spacing="6",
                justify_content="center"
            ),
            spacing="8",
            padding="60px",
            border_radius="20px",
            box_shadow="0 10px 40px rgba(0, 0, 0, 0.4)",
            background="rgba(255, 255, 255, 0.05)"
        ),
        min_height="100vh",
        background="linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)"
    )

# 5. 앱 생성 및 페이지 등록
app = rx.App()
app.add_page(main_page, route="/")
app.add_page(upload_page, route="/upload")
app.add_page(dashboard_page, route="/dashboard")