import sys
import rake
import re
import mysql.connector
import os
from googleapiclient.discovery import build
from PyPDF2 import PdfFileWriter, PdfFileReader
import datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


my_api_key = "AIzaSyBX7n9j5SfCBxOLtWGsE4SwmMMdQOD7sdY"
my_cse_id = "001888581548700543885:hcpwduckiys"

def send_email_not_found():
    fromaddr = "mosis.doc.search@gmail.com"
    toaddr = ["neelusin@usc.edu"]
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = ", ".join(toaddr)
    msg['Subject'] = "Document Search - No Documents Found"
    body = "We searched the Internet and did not find any documents today."
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "MarinaTowers")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()
		 
def send_email_found():
    fromaddr = "mosis.doc.search@gmail.com"
    toaddr = ["neelusin@usc.edu"]
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = ", ".join(toaddr)
    msg['Subject'] = "Document Search - Documents Found on Google"
    body = "We searched the Internet and found search results for some documents.\n\n"
    body += "Please check the below link for the results:- \n http://localhost:89/"
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "MarinaTowers")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

if __name__=="__main__":
	config = {
        'host': 'localhost',
        'port': 3306,
        'database': 'testdb',
        'user': 'root',
        'password': 'Backspacebar@1',
        'charset': 'utf8',
        'use_unicode': True,
        'get_warnings': True,
    }
	filename=sys.argv[1]
	stopwordfile=sys.argv[2]
	cnx = mysql.connector.connect(**config)
	cursor = cnx.cursor()
	now = datetime.datetime.now()
	print(now.strftime("%Y-%m-%d %H:%M:%S"))
	date = now.strftime("%Y-%m-%d %H:%M:%S")
	while('true'):
		flag = 'false'
		for file in os.listdir(filename):
			lastDate = datetime.datetime.strptime(time.ctime(os.path.getmtime(filename + '\\' + file)),"%a %b %d %H:%M:%S %Y")
			print(file)
			sql = "select keywords from FILE_METADATA where filename='%s' and date > '%s' order by date desc limit 1;" % (file,lastDate)
			cursor.execute(sql)
			keywordAllData=""
			total=0
			counter=0
			for (keywords) in cursor:
				keywordAllData = str(keywords)[2:len(str(keywords))-3]
			print(keywordAllData)
			if (keywordAllData==""):				
				rake_object = rake.Rake(stopwordfile, 5, 5, 2)
				path = filename + '\\' + file
				print(path)
				watermark = PdfFileReader(open(path, "rb"))
				pdfdata=""
				for j in range(0, watermark.getNumPages()):
					pdfdata=pdfdata+watermark.getPage(j).extractText()
				print(len(pdfdata))
				keywords = rake_object.run(pdfdata)
				keyword_limit = min(len(keywords), 5)
				i = keyword_limit
				while i > 0:
					print(keywords[i][0])
					if not re.match(r'.*[\%\$\^\*\@\!\-\(\)\:\;\'\"\{\}\[\]].*', keywords[i][0]) :
						keywordAllData=keywordAllData+"\""+keywords[i][0] +"\","
					i = i -1
			print(keywordAllData)
			sql = "INSERT INTO FILE_METADATA(FILENAME,DATE, keywords) VALUES ('%s' , '%s' , '%s')" % (file, date , keywordAllData)
			cursor.execute(sql)
			id = cursor.lastrowid
			cnx.commit()
			service = build("customsearch", "v1", developerKey=my_api_key)
			res = service.cse().list(q=keywordAllData, cx=my_cse_id, filter='0').execute()
			print('Top 10 google search urls are:-')
			if (len(res) == 6):
				for result in res['items']:
					flag = 'true'
					print(result['link'])
					sql = "INSERT INTO URL(FILE_ID,URL_NAME) VALUES (%s , '%s')" % (id,result['link'])
					cursor.execute(sql)
					cnx.commit()
					counter=counter+1
					if ("github.com/NeeluSingla8" in result['link']):
						total = total +1		
			if (counter != 0):
				print("precison is :- " + str((total/counter)))
				print("recall is :- " + str((total/max(total,counter))))
			else:
				print("precison is :- 0")
				print("recall is :- 0")
		print("Going to send email")
		if(flag=='true'):
			send_email_found()
		else:
			send_email_not_found()
		print("Email send")
		print("going to run after 1 day")
		time.sleep(24*3600)