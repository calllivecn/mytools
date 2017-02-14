#!/usr/bin/env python3
#coding=utf-8



import getopt,sys,os,smtplib,base64,argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



#---------------------------------------------------------------
# initrd
#user = 'linzxmail@qq.com'
#passwd=bytes('bXlAcHl0aG9uJDM0\n','ascii')

server='smtp.qq.com'


#----------------------------------------------------------------

parse=argparse.ArgumentParser(description="{} is a cmdline smtp mail".format(sys.argv[0]))

parse.add_argument('-T','--to',nargs='+',required=True,help='to mail address list')

parse.add_argument('-t','--text',default='this is a test mail.\n',help='mail test')

parse.add_argument('-u','--user',default='linzxmail@qq.com',help='mail user')

parse.add_argument('-p','--passwd',default=bytes('bXlAcHl0aG9uJDM0\n','ascii'),help='mail password')

parse.add_argument('-s','--subject',default='',help='mail content')

parse.add_argument('-f','--file',nargs='+',help='mail content text file')

parse.add_argument('-a','--attach',nargs='+',help='mail attach')

parse.add_argument('-v','--verbose',help='verbose')


args=parse.parse_args()

msg = MIMEMultipart()
msg['From']=args.user
msg['Subject'] = args.subject

if args.file:
	for f in args.file:
		f=open(f)
		text+='####    filename :'+f.name+'\n\n'
		text+=f.read()
		f.close()

if args.attach:
	

	for a in args.attach:
		basename = os.path.basename(a)
		fp = open(a, 'rb')
		att = MIMEText(fp.read(), 'base64', 'utf-8')
		fp.close()
		att["Content-Type"] = 'application/octet-stream'
		att.add_header('Content-Disposition', 'attachment',filename=('utf-8', '', basename))
		#encoders.encode_base64(att)
		msg.attach(att)

content1 = MIMEText(args.text, 'plain', 'utf-8')
msg.attach(content1)



#-----------------------------------------------------------
s = smtplib.SMTP()

if args.verbose: s.set_debuglevel(1)

s.connect(server,25)
#s.esmtp_features["auth"]="LOGIN PLAIN"
s.helo()
s.ehlo()
s.login(args.user,base64.decodebytes(args.passwd).decode('utf-8'))
if s.sendmail(args.user, args.to, msg.as_string()):
		print('Recv : error.')
s.close()
