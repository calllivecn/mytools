#!/usr/bin/env python3
# coding=utf-8
# update 2022-11-07 11:58


import os
import sys
import base64
import smtplib
import argparse
import traceback
import configparser
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# config information
CFG="""\
[Smtp]
Server = smtp.qq.com
;Email =
;Password =
"""

HOME = os.environ.get("HOME")

if HOME:
    CONF = Path(HOME) / ".config/smail.conf"
else:
    CONF = Path(".config/smail.conf")

def readcfg(filename, init_context=None):
    conf = configparser.ConfigParser()
    if filename.exists():
        conf.read(str(filename))
        return conf
    else:
        if init_context is None:
            raise Exception(f"初始化配置文本没有提供: {init_context}")
        else:
            with open(filename, "w") as fp:
                fp.write(init_context)

            conf.read_string(init_context)
            return conf


# -----------------------------------------------------------
def send(server, email, passwd, to, msg, verbose):
    try:
        s = smtplib.SMTP_SSL(server)

        if verbose:
            s.set_debuglevel(verbose)

        # s.connect(server)
        #s.esmtp_features["auth"]="LOGIN PLAIN"

        code = s.ehlo()[0]
        usesesmtp = True

        if not (200 <= code <= 299):
            usesesmtp = False
            code = s.helo()[0]

            if not (200 <= code <= 299):
                raise smtplib.SMTPHeloError

        # print("msg:", len(msg))
        msg_as_string = msg.as_string()
        # print("msg_as_string:", len(msg_as_string))

        if usesesmtp and s.has_extn("size"):
            sizelimit = int(s.esmtp_features["size"])
            size = round(sizelimit / (1 << 20), 2)
            # print(f"sizelimit: {sizelimit} size: {size}MB")
            if len(msg_as_string) > sizelimit:
                print(f"Maximum message size is {size}MB")
                print("Message too large ; aborting.")
                sys.exit(2)

        # s.starttls()
        # s.helo()
        # s.login(args.user, args.passwd)
        s.login(email, passwd)
        if s.sendmail(email, to, msg_as_string):
            print("Recv : error.")

    except (smtplib.SMTPException, smtplib.SMTPHeloError) as e:
        print("SMTPException:")
        traceback.print_exc(e)
        sys.exit(1)

    finally:
        # s.close()
        s.quit()



def main():
    PROG = Path(sys.argv[0]).name
    parse = argparse.ArgumentParser(description="%(prog)s SMTP mail 发送工具")

    parse.add_argument("-c", "--conf", default=CONF, help=f"配置(default: ~/.config/smail.conf")

    # parse.add_argument("-u", "--user", help="mail user")
    # parse.add_argument("-p", "--passwd", help="mail password")

    parse.add_argument("-T", "--to", nargs="+", required=True, help="发送给谁, 可以多个地址。")
    parse.add_argument("-s", "--subject", default="测试邮件", help="邮件主题")

    # text = parse.add_argument_group(title="文件内容选项")
    text = parse.add_mutually_exclusive_group()
    text.add_argument( "-t", "--text", default=f"{PROG} 工具默认邮件内容", help="邮件内容(Max: 1M)")
    text.add_argument("--text-infile", dest="infile", type=Path, help="从一个文体文件读取内容(Max: 1M)")
    text.add_argument("--text-stdin", dest="stdin", action="store_true", help="从标准输入读取内容(Max: 1M")

    parse.add_argument("-F", "--From", help="Mail From.")

    parse.add_argument("-a", "--attach", nargs="+", help="邮件附件")

    parse.add_argument("-v", "--verbose", action="count", default=0, help="verbose")

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)


    args = parse.parse_args()

    if args.parse:
        print(args)
        sys.exit(0)
    
    # conf 
    cfg = readcfg(CONF, CFG)

    try:
        config = cfg["Smtp"]
        server = config["Server"]
        email = config["Email"]
        password = config["Password"]
        # print(locals())
    except Exception:
        print(f"需要配置({CONF}):")
        print(CFG)
        sys.exit(1)

    msg = MIMEMultipart()

    if args.From:
        msg["From"] = args.From
    else:
        msg["From"] = email

    msg["Subject"] = args.subject
    

    if args.infile:
        with open(args.infile) as f:
            text = f"#### 从文件里读取文本: {args.infile.name} ####\n\n"
            text += f.read(1<<20)

        Text = text

    elif args.stdin:
        Text = sys.stdin.read(1<<20)

    elif args.text:
        Text = args.text

    content1 = MIMEText(Text, "plain", "utf-8")

    if args.attach:
        for a in args.attach:
            p = Path(a)
            with open(a, "rb") as fp:
                att = MIMEText(fp.read(), "base64", "utf-8")

            att["Content-Type"] = "application/octet-stream"
            att.add_header("Content-Disposition", "attachment", filename=("utf-8", "", p.name))
            # encoders.encode_base64(att)
            msg.attach(att)

    msg.attach(content1)

    send(server, email, password, args.to, msg, args.verbose)



if __name__ == "__main__":
    main()