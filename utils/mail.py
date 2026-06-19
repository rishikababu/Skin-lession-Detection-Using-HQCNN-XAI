
from flask_mail import Mail, Message

mail = Mail()

def send_mail(app, recipient_email, pdf_path):
    with app.app_context():
        msg = Message(
            subject="Hybrid Quantum Medical AI - Report",
            recipients=[recipient_email]
        )

        msg.body = """
Hello,

Your AI diagnosis report has been generated successfully.

Please find the attached PDF report.

Regards,
Hybrid Quantum Medical AI System
"""

        with app.open_resource(pdf_path) as fp:
            msg.attach(
                filename="Medical_Report.pdf",
                content_type="application/pdf",
                data=fp.read()
            )

        mail.send(msg)
