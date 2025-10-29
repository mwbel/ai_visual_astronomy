from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="AI Visual Astronomy API")

# 将 /app 映射到本地 app/ 目录，便于直接预览静态页面
app.mount("/app", StaticFiles(directory="app", html=True), name="app")

@app.get("/api/health")
def health():
    return {"ok": True}
