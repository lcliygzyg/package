#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,sys
import socket
import re
import socket
import commands
import json,time
import smtplib
import logging,glob
import smtplib
from email.mime.text import MIMEText

def record_log(flag,msg):
    loger=logging.getLogger()
    loger.setLevel(logging.DEBUG)
    hf=logging.FileHandler("/usr/local/keepalived_change.log")
    recordfmt=logging.Formatter('%(asctime)s\t\t%(levelname)s: %(message)s')
    hf.setFormatter(recordfmt)
    loger.addHandler(hf)
    if flag:
        loger.error(msg)
    else:
        loger.info(msg)
def mail(title,message):
    mailserver = "smtp.exmail.qq.com"
    frommail = '****'
    user = '******'
    password = "****"
    toall = [
             "email", # 
              ]
    msg = MIMEText(message,_subtype="html",_charset="utf-8")
    msg['Subject'] = title
    msg['From'] = "*******"
    for to in toall:
        s = smtplib.SMTP(mailserver)
        s.login(user,password)
        s.sendmail(frommail,[to],msg.as_string())
        s.quit()
        time.sleep(30)

def send_mg(localIP,currenttime):
           title="[注意]长生剑P3-mysql VIP切换到了ip:%s" % str(localIP)
           content='keepalived高可用组件在%s发生vip自动切换,请检查故障原因!' % (currenttime)
           mail(title,content)

if __name__=='__main__':
    skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    skt.connect(('8.8.8.8',80))
    socketIpPort = skt.getsockname()
    localIP = socketIpPort[0]
    skt.close()
    currenttime=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
    send_mg(localIP,currenttime)
