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
    hf=logging.FileHandler("/home/ericzyg/moniter_replication_log")
    recordfmt=logging.Formatter('%(asctime)s\t\t%(levelname)s: %(message)s')
    hf.setFormatter(recordfmt)
    loger.addHandler(hf)
    if flag:
        loger.error(msg)
    else:
        loger.info(msg)
def mail(title,message):
    mailserver = "smtp.exmail.qq.com"
    frommail = 'monitor@haima.me'
    user = 'monitor@haima.me'
    password = "haima.M.2016"
    toall = [
             "mailaddress", # 张三
              ]
    msg = MIMEText(message,_subtype="html",_charset="utf-8")
    msg['Subject'] = title
    msg['From'] = "monitor@haima.me"
    for to in toall:
        s = smtplib.SMTP(mailserver)
        s.login(user,password)
        s.sendmail(frommail,[to],msg.as_string())
        s.quit()
        time.sleep(30)
def checkbackup(localIP):
    portlist = []
    packlist = []
    m = re.compile('\d{4}')
    portstr = glob.glob('/usr/local/script/mysqlbackup*.sh')
    for F in portstr:
        if m.search(F):
            portlist.append(m.search(F).group())
    T=time.strftime("%Y%m%d",time.localtime())
    for P in portlist:
        packlist.extend(glob.glob('/data2/mysql_backup/database'+P+'_'+T+'.tar.gz'))
    print packlist
    for CHP in portlist:
        print CHP, type(CHP)
        chpk_rt = 0
        for PA in packlist:
            if PA.find(CHP) == -1:
                pass
            else:
                chpk_rt=1
                break
        if not chpk_rt:
            title = "SDK 从库备份报警 [warning] ip:%s" % str(localIP)
            content="mysql从库%s备份文件不存在，请检查/data2/mysql_backup/目录！" % CHP
            mail(title, content)
        else:
            SZ=os.stat(PA).st_size/1000/1000
            if int(SZ)<100:
                title = "SDK 从库备份报警 [warning] ip:%s" % str(localIP)
                content="mysql从库%s备份大小不正常，请检查！" % CHP
                mail(title, content)


def checkrepl(localIP):
    conlist=[]
    mysql_conf = glob.glob('/usr/local/script/mysqlbackup*.sh')
    for FD in mysql_conf:
        with open(FD, 'r') as f:
            K=re.search('port=\d+', f.read())
            conpt=K.group().split('=')
        with open(FD, 'r') as f:
            pwd=re.search('password=.*', f.read())
            conpwd=pwd.group().split('=')
        conlist.append((conpt[1],conpwd[1]))
    for conn in conlist:
        PORT,PASSWORD=conn
        cmd='/usr/bin/mysql -uroot -P%s -p"%s" -h 127.0.0.1 -e "show slave status\G" | grep -E "(Slave_IO_Running|Slave_SQL_Running)"' % (PORT,PASSWORD)
        status,result=commands.getstatusoutput(cmd)
        if result.find('No') == -1:
           pass
        else:
           title="主从同步告警[warning] ip:%s" % str(localIP)
           content='IP: %s 从库 %s 同步已停止,请检查!' % (localIP,PORT)
           mail(title,content)



if __name__=='__main__':
    skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    skt.connect(('8.8.8.8',80))
    socketIpPort = skt.getsockname()
    localIP = socketIpPort[0]
    skt.close()
    checkrepl(localIP)
    currenttime=int(time.strftime('%H',time.localtime()))
    if 9<currenttime<11:
       checkbackup(localIP)
