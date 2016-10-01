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

#api key and cse_id to connect to google using custom search.
my_api_key = "AIzaSyBX7n9j5SfCBxOLtWGsE4SwmMMdQOD7sdY"
my_cse_id = "001888581548700543885:hcpwduckiys"

#method to send mail to receipents if none of the document found in the search. uses smtp module and email.mime module.
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

#method to send mail to receipents if one or more documents are found in the search. uses smtp module and email.mime module.	
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

#main method from where execution of the program starts.
if __name__=="__main__":
	#connection setting of the mysql database.
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
	#directory name where all documents are kept.
	filename=sys.argv[1]
	#sstopword list file name
	stopwordfile=sys.argv[2]
	cnx = mysql.connector.connect(**config)
	cursor = cnx.cursor()
	now = datetime.datetime.now()
	#getting the current datetime in below specified format.
	print(now.strftime("%Y-%m-%d %H:%M:%S"))
	date = now.strftime("%Y-%m-%d %H:%M:%S")
	#making a demon process while never ending while loop
	while('true'):
		flag = 'false'
		#iterating over the files in the given directory
		for file in os.listdir(filename):
			#checking the last modified date of the file
			lastDate = datetime.datetime.strptime(time.ctime(os.path.getmtime(filename + '\\' + file)),"%a %b %d %H:%M:%S %Y")
			print(file)
			#checking the whether this file last modified date calcuated above is less than or grater than when last time this rake ran on this file.
			sql = "select keywords from FILE_METADATA where filename='%s' and date > '%s' order by date desc limit 1;" % (file,lastDate)
			cursor.execute(sql)
			keywordAllData=""
			total=0
			counter=0
			#getting the keywords for the file if file is modified before last time rake ran on this file.
			for (keywords) in cursor:
				keywordAllData = str(keywords)[2:len(str(keywords))-3]
			print(keywordAllData)
			#if file is modified after last time rake ran on this file then running rake on this file
			if (keywordAllData==""):				
				rake_object = rake.Rake(stopwordfile, 5, 5, 2)
				path = filename + '\\' + file
				print(path)
				#reading content of the file for rake.
				watermark = PdfFileReader(open(path, "rb"))
				pdfdata=""
				for j in range(0, watermark.getNumPages()):
					pdfdata=pdfdata+watermark.getPage(j).extractText()
				print(len(pdfdata))
				#getting keywords for the file
				keywords = rake_object.run(pdfdata)
				keyword_limit = min(len(keywords), 5)
				i = keyword_limit
				#removing keywords with special charachter. 
				while i > 0:
					print(keywords[i][0])
					if not re.match(r'.*[\%\$\^\*\@\!\-\(\)\:\;\'\"\{\}\[\]].*', keywords[i][0]) :
						keywordAllData=keywordAllData+"\""+keywords[i][0] +"\","
					i = i -1
			print(keywordAllData)
			#inserting the currnt date, keywords and filename into database.
			sql = "INSERT INTO FILE_METADATA(FILENAME,DATE, keywords) VALUES ('%s' , '%s' , '%s')" % (file, date , keywordAllData)
			cursor.execute(sql)
			id = cursor.lastrowid
			cnx.commit()
			#setting the parameters for google custom search.
			service = build("customsearch", "v1", developerKey=my_api_key)
			res = service.cse().list(q=keywordAllData, cx=my_cse_id, filter='0').execute()
			print('Top 10 google search urls are:-')
			#getting the result from the google custom search.
			if (len(res) == 6):
				for result in res['items']:
					flag = 'true'
					print(result['link'])
					#inserting each result into database for web-api to display on web-interface.
					sql = "INSERT INTO URL(FILE_ID,URL_NAME) VALUES (%s , '%s')" % (id,result['link'])
					cursor.execute(sql)
					cnx.commit()
					counter=counter+1
					if ("github.com/NeeluSingla8" in result['link']):
						total = total +1		
			#calculating precison and recall values for this google search.
			if (counter != 0):
				print("precison is :- " + str((total/counter)))
				print("recall is :- " + str((total/max(total,counter))))
			else:
				print("precison is :- 0")
				print("recall is :- 0")
		#sending mail by calling send_email_found() or send_email_not_found() based on search result.
		print("Going to send email")
		if(flag=='true'):
			send_email_found()
		else:
			send_email_not_found()
		print("Email send")
		print("going to run after 1 day")
		#sleeping for 1 day bafore next time to run the code.
		time.sleep(24*3600)
