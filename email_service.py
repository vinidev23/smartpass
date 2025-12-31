import smtplib
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

def send_welcome_email(to_email, name, unique_id, qr_path):
    msg = EmailMessage()
    msg["Subject"] = "🎫 Seu acesso SmartPass"
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email
    
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 20px;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td align="center">
              <table width="600" style="background:#ffffff; border-radius:8px; padding:30px;">
                
                <tr>
                  <td align="center">
                    <h1 style="color:#2c3e50;">SmartPass</h1>
                    <p style="font-size:16px; color:#555;">
                      Olá <strong>{name}</strong>, seu cadastro foi realizado com sucesso.
                    </p>
                  </td>
                </tr>

                <tr>
                  <td align="center" style="padding:20px;">
                    <p style="font-size:15px; color:#333;">
                      Utilize o QR Code abaixo para acessar o sistema:
                    </p>
                    <img src="cid:qrcode" width="200" alt="QR Code">
                  </td>
                </tr>

                <tr>
                  <td style="padding-top:20px;">
                    <p style="font-size:14px; color:#555;">
                      <strong>ID único:</strong> {unique_id}
                    </p>
                  </td>
                </tr>

                <tr>
                  <td style="padding-top:30px;">
                    <p style="font-size:13px; color:#888;">
                      Guarde este QR Code com segurança.<br>
                      Equipe SmartPass
                    </p>
                  </td>
                </tr>

              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """
    
    msg.set_content("Seu email não suporta HTML.")
    msg.add_alternative(html_content, subtype="html")
    
    qr_file = Path(qr_path)
    with open(qr_file, "rb") as f:
        msg.get_payload()[1].add_related(
            f.read(),
            maintype="image",
            subtype="png",
            cid="qrcode"
        )
        
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
    
