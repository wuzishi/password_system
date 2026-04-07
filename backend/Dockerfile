# ---- 构建阶段 ----
FROM python:3.12-slim AS builder

WORKDIR /build
ENV HTTP_PROXY="" HTTPS_PROXY="" http_proxy="" https_proxy=""
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# ---- 运行阶段 ----
FROM python:3.12-slim

# 安全: 非 root 运行
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /bin/false appuser

WORKDIR /app

# 复制依赖
COPY --from=builder /install /usr/local

# 复制代码
COPY . .

# 移除不必要的文件
RUN rm -f .env .env.* Dockerfile requirements.txt && \
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 切换到非 root 用户
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
