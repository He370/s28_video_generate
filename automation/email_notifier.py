import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailNotifier:
    def __init__(self, config_path="automation/config.json"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            # Try looking relative to this file if not found
            base_dir = os.path.dirname(os.path.abspath(__file__))
            alt_path = os.path.join(base_dir, "config.json")
            if os.path.exists(alt_path):
                self.config_path = alt_path
                with open(alt_path, 'r') as f:
                    return json.load(f)
            return {}
            
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def send_error_alert(self, project_name, error_log):
        """Sends an email alert about a failure."""
        email_config = self.config.get("email", {})
        sender_email = email_config.get("sender_email")
        sender_password = email_config.get("sender_password")
        recipient_email = email_config.get("recipient_email", "ldh.sjtu@gmail.com")
        smtp_server = email_config.get("smtp_server", "smtp.gmail.com")
        smtp_port = email_config.get("smtp_port", 587)

        if not sender_email or not sender_password:
            print("Error: Email credentials not found in config.json. Skipping email alert.")
            return

        subject = f"🚨 FAILED: {project_name} Automation"
        body = f"""
        The automation job for project '{project_name}' has failed.
        
        Error Log:
        ----------------------------------------
        {error_log}
        ----------------------------------------
        
        Please check the server.
        """

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()
            print(f"Alert email sent to {recipient_email}")
        except Exception as e:
            print(f"Failed to send email: {e}")

if __name__ == "__main__":
    # Test
    notifier = EmailNotifier()
    notifier.send_error_alert("Test Project", "This is a test error log.")
