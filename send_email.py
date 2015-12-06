"""
Send file as email attachment.
"""

__author__ = "Tyrone van Balla"
__version__ = "Version 1.0.0"
__description__ = "Send file as email attachment"

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(filename, table_name, to_user, from_user, password):
    """
    Sends file as email attachment.
    Used to send arp table for cluster. 
    """
    
    msg = MIMEMultipart('alternative')
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.ehlo()
    s.starttls()
    s.login(from_user, password)

    msg['Subject'] = table_name
    msg['From'] = from_user
    body = "ARP Table: {} attached".format(table_name)

    f = file(filename)
    attachment = MIMEText(f.read())
    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(attachment)
    
    content = MIMEText(body, 'plain')
    msg.attach(content)
    
    s.sendmail(from_user, to_user, msg.as_string())
