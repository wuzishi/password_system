"""安全头中间件 — 防 XSS、点击劫持、MIME 嗅探、信息泄露等。"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # 阻止浏览器 MIME 嗅探
        response.headers["X-Content-Type-Options"] = "nosniff"
        # 阻止被嵌入 iframe（防点击劫持）
        response.headers["X-Frame-Options"] = "DENY"
        # 启用浏览器内置 XSS 过滤器
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # 限制 Referrer 泄露
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # 限制浏览器功能
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        # CSP — 严格限制脚本来源
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        # 强制 HTTPS（生产环境启用）
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        # 隐藏服务器信息
        if "server" in response.headers:
            del response.headers["server"]
        # 防止缓存敏感接口
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response
