#!/usr/bin/env python3
# coding=utf-8
# update 2022-11-07 11:58


import io
import os
import sys
import smtplib
import argparse
import traceback
import configparser
from pathlib import Path

from email import encoders
from email.utils import formataddr
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart


# config information
CFG="""\
[Smtp]
Server = smtp.qq.com
;Port = 465
;Email =
# 发件人显示名称[可选]
;From_name =
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


class EmailSender:

    def __init__(self, server: str, email: str, password: str, port: int = 465, verbose=False):
        self.server = server
        self.port = port
        self.email = email
        self.password = password
        self.verbose = verbose
        self.msg = MIMEMultipart("mixed")
        self.alternative = MIMEMultipart("alternative")

    def Subject(self, subject: str):
        self.msg['Subject'] = subject

    def set_text(self, text: str):
        text_content = MIMEText(text, "plain", "utf-8")
        self.alternative.attach(text_content)

    def set_html(self, body):
        html_content = MIMEText(body, 'html', 'utf-8')
        self.alternative.attach(html_content)
    
    def attach(self, filenames: list[Path]):
        for a in filenames:
            with open(a, "rb") as fp:
                att = MIMEBase("application", "octet-stream")
                att.set_payload(fp.read())
                encoders.encode_base64(att)

            att.add_header("Content-Disposition", "attachment", filename=("utf-8", "", a.name))

            self.msg.attach(att)


    def send(self, to_email: list[str], from_name: str|None = None):

        if from_name:
            self.msg['From'] = formataddr((from_name, self.email))
        else:
            self.msg['From'] = self.email

        self.msg['To'] = ', '.join(to_email)

        self.msg.attach(self.alternative)

        try:
            s = smtplib.SMTP_SSL(self.server, self.port)
        except Exception as e:
            print(f"连接服务器出错：{e}")
            sys.exit(1)

        try:
            if self.verbose:
                s.set_debuglevel(self.verbose)

            code = s.ehlo()[0]
            usesesmtp = True

            if not (200 <= code <= 299):
                usesesmtp = False
                code = s.helo()[0]

                if not (200 <= code <= 299):
                    raise smtplib.SMTPHeloError(code, "HELO error")

            msg_as_string = self.msg.as_string()

            if usesesmtp and s.has_extn("size"):
                sizelimit = int(s.esmtp_features["size"])
                size = round(sizelimit / (1 << 20), 2)
                print(f"sizelimit: {sizelimit} size: {size}MB")
                if len(msg_as_string) > sizelimit:
                    print(f"Maximum message size is {size}MB")
                    print("Message too large ; aborting.")
                    sys.exit(2)

            s.login(self.email, self.password)
            if s.sendmail(self.email, to_email, msg_as_string):
                print("Recv : error.")

        except (smtplib.SMTPException, smtplib.SMTPHeloError) as e:
            print("SMTPException:")
            traceback.print_exc()
            sys.exit(1)

        finally:
            s.quit()


def main():
    PROG = Path(sys.argv[0]).name
    parse = argparse.ArgumentParser(description="%(prog)s SMTP mail 发送工具")

    parse.add_argument("-c", "--conf", default=CONF, help="配置(default: ~/.config/smail.conf)")

    # parse.add_argument("-u", "--user", help="mail user")
    # parse.add_argument("-p", "--passwd", help="mail password")

    parse.add_argument("-s", "--subject", default="测试邮件", help="邮件主题(default: 测试邮件)")
    parse.add_argument("-T", "--to", nargs="+", required=True, help="发送给谁, 可以多个地址。")
    parse.add_argument("--cc", nargs="*", default=[], help="抄送给谁, 可以多个地址。")
    parse.add_argument("--bcc", nargs="*", default=[], help="密送给谁, 可以多个地址。")

    # text = parse.add_argument_group(title="文件内容选项")
    text = parse.add_mutually_exclusive_group()
    text.add_argument( "-t", "--text", default=f"{PROG} 工具默认邮件内容", help="邮件内容(Max: 1M)")
    text.add_argument("--text-infile", dest="infile", type=Path, help="从一个文体文件读取内容(Max: 1M)")
    text.add_argument("--text-stdin", dest="stdin", action="store_true", help="从标准输入读取内容(Max: 1M)")

    text.add_argument("--html-stdin", dest="html_stdin", action="store_true", help="从标准输入读取html内容(Max: 1M, 与--text-stdin冲突)")

    parse.add_argument("--html", dest="html", help="邮件html内容(Max: 1M)")
    parse.add_argument("--html-infile", dest="html_infile", type=Path, help="从标准输入读取html内容(Max: 1M)")

    parse.add_argument("-F", "--From", help="从那个邮件发送的。")

    parse.add_argument("-a", "--attach", nargs="+", type=Path, help="邮件附件")

    parse.add_argument("-v", "--verbose", action="count", default=0, help="verbose")

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)


    args = parse.parse_args()

    if args.parse:
        print(args)
        sys.exit(0)
    
    cfg = readcfg(CONF, CFG)
    
    try:
        config = cfg["Smtp"]
        server = config["Server"]
        email = config["Email"]
        password = config["Password"]
    except Exception:
        print(f"需要配置({CONF}):")
        print(CFG)
        sys.exit(1)

    try:
        port = int(config["Port"])
    except Exception:
        port = 465


    es = EmailSender(server, email, password, port, args.verbose)

    if args.cc:
        es.msg["Cc"] = ",".join(args.cc)

    es.Subject(args.subject)

    # choice: ["text", "html"]
    content_mode = "text"
    Text = io.StringIO()
    if args.infile:
        with open(args.infile) as f:
            Text.write(f"#### 从文件里读取文本: {args.infile.name} ####\n\n")
            Text.write(f.read(1<<20))

    elif args.stdin:
        Text.write(sys.stdin.read(1<<20))

    elif args.text:
        Text.write(args.text)

    es.set_text(Text.getvalue())
    Text.close()

    Html = io.StringIO()
    if args.html:
        content_mode = "html"
        Html.write(args.html)

    elif args.html_infile:
        content_mode = "html"
        with open(args.html_infile) as f:
            Html.write(f.read(1<<20))

    elif args.html_stdin:
        content_mode = "html"
        Html.write(sys.stdin.read(1<<20))

    if content_mode == "html":
        es.set_html(Html.getvalue())
    Html.close()

    if args.attach:
        es.attach(args.attach)

    all_addrs = args.to + args.cc + args.bcc
    es.send(all_addrs, config.get("from_name"))


if __name__ == "__main__":
    main()