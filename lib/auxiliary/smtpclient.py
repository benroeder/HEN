import smtplib, datetime, time

class SMTPClient:
    
    def __init__(self, serverURL):
        self.__session = smtplib.SMTP(serverURL)

    def close(self):
        self.__session.quit()
        
    def sendEmail(self, recipient, sender, subject, text):
        today = datetime.date.today()
        dateSent = today.strftime("%A, %B %d, %Y at ") + time.strftime("%H:%M")
        message = "To: " + str(recipient) + "\n" \
                  "From: " + str(sender) + "\n" \
                  "Date: " + str(dateSent) + "\n" \
                  "Subject: " + str(subject) + "\n\n" + text

        smtpresult = self.__session.sendmail(sender, recipient, message)
        if smtpresult:
            errstr = ""
            for recip in smtpresult.keys():
                errstr = """Could not delivery mail to: %s
                Server said: %s
                %s
                %s""" % (recip, smtpresult[recip][0], smtpresult[recip][1], errstr)
                raise smtplib.SMTPException, errstr
