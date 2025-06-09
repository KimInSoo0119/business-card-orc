import reflex as rx
import httpx
from typing import List, Dict

# 1. 상태 클래스
class State(rx.State):
    filter_company: str = "전체"
    customers: List[Dict] = []
    companies: List[str] = ["전체"]
    upload_result: str = ""
    preview_url: str = ""

    async def set_filter_company(self, company: str):
        self.filter_company = company
        await self.get_customers()


    async def get_customers(self):
        url = "http://localhost:8000/api/business-card/list/"
        params = {}
        if self.filter_company != "전체":
            params["company"] = self.filter_company
        # async with httpx.AsyncClient() as client:
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
    async def handle_upload(self, files: List[rx.UploadFile]):
        if not files:
            self.upload_result = "파일이 선택되지 않았습니다."
            return
        file = files[0]
        upload_data = await file.read()

        import base64
        encoded = base64.b64encode(upload_data).decode("utf-8")
        mime = file.content_type
        self.preview_url = f"data:{mime};base64,{encoded}"

        url = "http://localhost:8000/api/business-card/"
        files_data = {'image': (file.filename, upload_data, file.content_type)}
        # async with httpx.AsyncClient() as client:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, files=files_data)
        if response.status_code == 201:
            self.upload_result = f"{file.filename} 업로드 및 저장 성공!"
            await self.get_customers()
        else:
            self.upload_result = f"업로드 실패!"

    @rx.event
    async def delete_customer(self, customer_id: str):
        url = f"http://localhost:8000/api/business-card/{customer_id}/"
        # async with httpx.AsyncClient() as client:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(url)
        if response.status_code == 204:
            # 삭제 성공 시 목록 갱신
            await self.get_customers()

    @rx.event
    async def reset_upload_state(self):
        self.preview_url = ""
        self.upload_result = ""

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
             rx.hstack(
                rx.link(
                    rx.button("🏠 메인 페이지", color_scheme="gray", variant="ghost"),
                    href="/"
                ),
                rx.link(
                    rx.button("📊 대시보드", color_scheme="gray", variant="ghost"),
                    href="/dashboard"
                ),
                spacing="4",
                justify="end",
                width="100%",
                padding_bottom="12px"
            ),
            rx.heading("📤 명함 업로드", size="6", color="#234e52"),
            rx.upload(
                # rx.vstack(
                #     rx.icon("upload", size=32, color="#2c7a7b"),
                #     rx.text("명함 이미지를 선택하거나 드래그하세요", font_weight="semibold", color="#2c7a7b")
                # ),
                rx.cond(
                  State.preview_url == "",
                  rx.vstack(
                      rx.icon("upload", size=32, color="#2c7a7b"),
                      rx.text("더블클릭후, 명함이미지를 선택해주세요.", font_weight="semibold", color="#2c7a7b")
                  )
                ),
                id=upload_id,
                multiple=False,
                accept={"image/png": [".png"], "image/jpeg": [".jpg", ".jpeg"]},
                max_files=1,
                min_height="186px",
                min_width="404px",
                border="3px dashed #2c7a7b",
                padding="56px",
                border_radius="20px",
                margin_bottom="24px",
                # background를 상태에 따라 동적으로 변경
                background=rx.cond(
                    State.preview_url != "",
                    "url({}) center/cover no-repeat".format(State.preview_url),
                    "#ebf8ff"
                ),
            ),
            rx.button(
                "업로드",
                on_click=lambda: State.handle_upload(rx.upload_files(upload_id)),
                color_scheme="teal",
                size="4",
                width="100%",
                border_radius="full",
                box_shadow="lg"
            ),
            rx.cond(
                State.preview_url != "",
                rx.button(
                    "🗑️ 이미지 삭제",
                    on_click=State.reset_upload_state,
                    color_scheme="red",
                    variant="ghost",
                    margin_top="8px"
                )
            ),
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
            background="rgba(255, 255, 255, 0.08)",  # 반투명 배경
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