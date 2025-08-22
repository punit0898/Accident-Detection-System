import smtplib
import json  # Ensure this import is here
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os

class EmailSender:
    def __init__(self, config_file="config.json"):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            email_config = config['email']
            self.sender = email_config['sender']
            self.password = email_config['password']
            self.recipient = email_config['recipient']
            self.smtp_server = email_config['smtp_server']
            self.smtp_port = email_config['smtp_port']
        except:
            # Default settings if config file is missing
            self.sender = "accident.alert.system00@gmail.com"
            self.password = "your_app_password_here"
            self.recipient = "singhpunitice00@gmail.com"
            self.smtp_server = "smtp.gmail.com"
            self.smtp_port = 587
    
    def send_alert(self, video_name, timestamp, screenshot_path=None):
        subject = f"ACCIDENT DETECTED in {video_name}"
        body = f"""
        <html>
          <body>
            <h2>Accident Alert!</h2>
            <p>An accident has been detected in the video <b>{video_name}</b> at timestamp <b>{timestamp}</b>.</p>
            <p>Please review the video immediately.</p>
          </body>
        </html>
        """
        
        message = MIMEMultipart()
        message["From"] = self.sender
        message["To"] = self.recipient
        message["Subject"] = subject
        
        # Attach HTML body
        message.attach(MIMEText(body, "html"))
        
        # Attach screenshot if available
        if screenshot_path and os.path.exists(screenshot_path):
            with open(screenshot_path, 'rb') as f:
                img_data = f.read()
            image = MIMEImage(img_data, name=os.path.basename(screenshot_path))
            message.attach(image)
        
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender, self.password)
            server.sendmail(self.sender, self.recipient, message.as_string())
            server.quit()
            print("Email alert sent successfully!")
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False