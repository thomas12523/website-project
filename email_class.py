import smtplib
from dotenv import load_dotenv
import os

class mail:
    def __init__(self):
        pass

    def send_menssage(self,mail_origin,subject,body,name):
        load_dotenv()
        my_email=os.getenv('MAIL_USERNAME')
        password=os.getenv('MAIL_PASSWORD')
        with smtplib.SMTP("smtp.gmail.com") as connection:
            aux=body+"\n"+f"sent by {mail_origin},{name}"
            connection.starttls()
            connection.login(user=my_email,password=password)
            connection.sendmail(from_addr=my_email,to_addrs=my_email,msg=f"Subject:{subject}!\nMIME-Version: 1.0\nContent-Type: text/plain; charset=utf-8\n\n{aux}")

