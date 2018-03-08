#!/usr/bin/env python3
#coding=utf-8



import getopt,sys,os,smtplib,base64,argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


#---------------------------------------------------------------
# config information
server='smtp.qq.com'
username=''
password=''

#----------------------------------------------------------------

parse=argparse.ArgumentParser(description="%(prog)s is a cmdline smtp mail")

parse.add_argument('-T','--to',nargs='+',required=True,help='to mail address list')

parse.add_argument('-t','--text',default='this is a test mail.',help='mail test')

parse.add_argument('-u','--user',default=username,help='mail user')

parse.add_argument('-p','--passwd',default=password,help='mail password')

parse.add_argument('-s','--subject',default='known subject',help='mail content')

#parse.add_argument('-F','--From',default='qq@qq.com',help='Nothing')
parse.add_argument('-F','--From',help='Nothing')

parse.add_argument('-f','--file',help='mail content text file')

parse.add_argument('-a','--attach',nargs='+',help='mail attach')

parse.add_argument('-v','--verbose',action='count',default=0,help='verbose')


args=parse.parse_args()

#print(args)

msg = MIMEMultipart()

if args.From: 
    msg['From']=args.From
else:
    msg['From']=args.user

msg['Subject'] = args.subject

if args.file:
    with open(args.file) as f:
        text = '#### Email send content filename :' + f.name + '\n\n'
        text += f.read()
    args.text = text

if args.attach:
    for a in args.attach:

        basename = os.path.basename(a)

        with open(a, 'rb') as fp:
            att = MIMEText(fp.read(), 'base64', 'utf-8')

        att["Content-Type"] = 'application/octet-stream'
        att.add_header('Content-Disposition', 'attachment',filename=('utf-8', '', basename))
        #encoders.encode_base64(att)
        msg.attach(att)

content1 = MIMEText(args.text, 'plain', 'utf-8')
msg.attach(content1)



#-----------------------------------------------------------
try:
    s = smtplib.SMTP_SSL(server)

    if args.verbose:
        s.set_debuglevel(args.verbose)

    #s.connect(server)
    #s.esmtp_features["auth"]="LOGIN PLAIN"

    code = s.ehlo()[0]
    usesesmtp=True
    if not (200<= code<=299):
        usesesmtp=False
        code = helo()[0]
        if not (200<=code<=299):
            raise smtplib.SMTPHeloError
    if usesesmtp and s.has_extn('size'):
        if len(msg) > int(s.esmtp_features['size']):
            print('Maximum message size is {}MB'.format(int(s.esmtp_features['size']) / (1<<20)))
            print('Message too large ; aborting.')
            exit(2)

    #s.starttls()
    #s.helo()
    s.login(args.user,args.passwd)
    if s.sendmail(args.user, args.to, msg.as_string()):
        print('Recv : error.')
except (smtplib.SMTPException ,smtplib.SMTPHeloError) as e:
    print('SMTPException ',e)
    exit(1)
finally:
#    s.close()
    s.quit()
    
