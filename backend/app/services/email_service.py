import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

logger = logging.getLogger("email")

ROLE_LABELS = {"admin": "管理员", "product": "产品", "developer": "开发"}


def send_invitation_email(to_email: str, token: str, role: str, inviter_name: str) -> bool:
    """Send invitation email. Returns True on success."""
    invite_url = f"{settings.SITE_URL}/accept-invite?token={token}"
    role_label = ROLE_LABELS.get(role, role)

    html = f"""
    <div style="max-width:560px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
      <div style="background:#1d1e2c;padding:30px;text-align:center;border-radius:12px 12px 0 0">
        <h1 style="color:#409eff;margin:0;font-size:24px">团队协作密码平台</h1>
      </div>
      <div style="background:#fff;padding:30px;border:1px solid #e8e8e8;border-top:none;border-radius:0 0 12px 12px">
        <p style="font-size:16px;color:#333">你好！</p>
        <p style="color:#666;line-height:1.8">
          <strong>{inviter_name}</strong> 邀请你加入团队协作密码平台，角色为
          <span style="color:#409eff;font-weight:600">{role_label}</span>。
        </p>
        <div style="text-align:center;margin:30px 0">
          <a href="{invite_url}"
             style="background:#409eff;color:#fff;padding:12px 36px;border-radius:6px;text-decoration:none;font-size:16px;font-weight:600;display:inline-block">
            接受邀请
          </a>
        </div>
        <p style="color:#999;font-size:13px">
          邀请链接 {settings.INVITE_EXPIRE_HOURS} 小时内有效。如果按钮无法点击，请复制以下链接到浏览器：
        </p>
        <p style="color:#409eff;font-size:13px;word-break:break-all">{invite_url}</p>
      </div>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"邀请加入密码平台 - 来自 {inviter_name}"
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html", "utf-8"))

    if not settings.SMTP_HOST:
        logger.warning(f"SMTP not configured. Invite URL: {invite_url}")
        return True  # Allow to proceed without email in dev

    try:
        if settings.SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USER, to_email, msg.as_string())
        server.quit()
        logger.info(f"Invitation email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False
