from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# 환경 변수 로드
load_dotenv()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# 데이터베이스 연결 함수
def get_db_connection():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)
    return conn

# 애플리케이션 시작 시 테이블 생성
@app.on_event("startup")
def create_tables_if_needed():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS my_beaty (
            id SERIAL PRIMARY KEY,
            color TEXT NOT NULL,
            time TIMESTAMP NOT NULL
        )
        """
    )
    conn.commit()
    cursor.close()
    conn.close()

class BeatyPayload(BaseModel):
    color: str
    time: str  # ISO 8601 문자열

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # 기본 경로에서 바로 form 페이지를 렌더링합니다.
    return templates.TemplateResponse("form.html", {"request": request})

@app.get("/hello")
async def hello():
    return {"message": "Hello FastAPI  with PostgreSQL"}

@app.get("/db-test")
async def db_test():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        cursor.close()
        conn.close()
        return {"database_version": db_version["version"]}
    except Exception as e:
        return {"error": str(e)}

@app.get("/dump")
async def dump_beaty():
    """테이블 상태 확인용: my_beaty 최근 10개 행을 반환합니다."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, color, time FROM my_beaty ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/form", response_class=HTMLResponse)
async def form(request: Request):
    # templates/form.html을 렌더링해서 반환
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/save")
async def save_beaty(payload: BeatyPayload):
    try:
        # 입력된 시간 문자열을 파싱 (문법 불일치 시 예외 발생)
        parsed_time = datetime.fromisoformat(payload.time)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO my_beaty (color, time) VALUES (%s, %s) RETURNING id",
            (payload.color, parsed_time),
        )
        new_id = cursor.fetchone()["id"]
        conn.commit()
        cursor.close()
        conn.close()

        return {"id": new_id, "color": payload.color, "time": payload.time}
    except Exception as e:
        # 실제 오류를 클라이언트가 확인할 수 있도록 HTTP 예외로 반환
        raise HTTPException(status_code=500, detail=str(e))

# 자바의 main() 메서드 역할을 하는 블록
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)