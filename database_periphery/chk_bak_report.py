# -*- coding:utf-8 -*-
#by ericzyg@2015/8/16 11:48
from __future__ import with_statement
import os
import time
import logging
import smtplib
import datetime
from shutil import rmtree
from glob import glob
from hashlib import md5
from collections import OrderedDict
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from xml.dom.minidom import parseString
from xml.etree.ElementTree import Element, SubElement, tostring

class XMLFilter(object):
    def __init__(self,agentpath):
        self.agentpath = agentpath

    def xmlpath(self):
        return self.agentpath + "/xml"

    def agentspid(self):
        return self.agentpath.split("/")[-1].lower()

    @staticmethod
    def xmlfilter(xmlist):
        xmlistlen = len(xmlist)
        i = 0
        popid = []
        if xmlistlen > 1:
            while i < xmlistlen:
                for j in range(i+1,xmlistlen):
                    if not j in popid:
                        if xmlist[i].split("/")[-1].split("_")[1] == xmlist[j].split("/")[-1].split("_")[1]:
                            if int(xmlist[i].split("/")[-1].split("_")[-1].split(".")[0]) < \
                                int(xmlist[j].split("/")[-1].split("_")[-1].split(".")[0]):
                                xmlist[i] = xmlist[j]
                            popid.append(j)
                i += 1
            popid.sort()
            popid.reverse()
            for i in popid:
                xmlist.pop(i)

        return xmlist

    def xmlfile(self,date):
        filefilter = "%s/%s_*_md5_%s_*.xml" % (self.xmlpath(),self.agentspid(),date)
        xmlist = self.xmlfilter(glob(filefilter))
        for f in xmlist:
            allip.append(f.split("/")[-1].split("_")[1])
            yield f

def md5sum(f):
    h = md5()
    with open(f,'rb') as myfile:
        h.update(myfile.read())
    return h.hexdigest()

def agentiter():
    for agent in glob(backuppath + "[A-Z,1-9][A-Z,0-9][A-Z,0-9]"):
        if os.path.isdir(agent):
            yield agent

def runcheck():
    logger = log()
    lastday = date - datetime.timedelta(days=1)
    total = OrderedDict([("Spid",0),("SrvNum(last)",0),("SrvNum",0),("GSrvNum(last)",0),("GSrvNum",0),
                         ("ActorNum",0),("ActorSize(MB)",0),("RuntimeNum",0),("RuntimeSize(KB)",0),("ErrNum",0)])
    for agent in agentiter():
        total["Spid"] += 1
        spid = OrderedDict([("Spid",""),("SrvNum(last)",0),("SrvNum",0),("GSrvNum(last)",0),("GSrvNum",0),
                            ("ActorNum",0),("ActorSize(MB)",0),("RuntimeNum",0),("RuntimeSize(KB)",0),("ErrNum",0)])

        spid["Spid"] = agent.split("/")[-1].lower()
        agentxml = XMLFilter(agent)
        for f in agentxml.xmlfile(date):
            print f
            tree = ET.parse(f)
            root = tree.getroot()
            spid["SrvNum"] += 1
            total["SrvNum"] += 1
            for server in root:
                spid["GSrvNum"] += 1
                total["GSrvNum"] += 1
                ip = server.get("ctip")
                for zippack in server:
                    if zippack.tag == "cqactor":
                        ret = match(zippack,logger,ip)
                        spid["ActorNum"] += ret[0]
                        total["ActorNum"] += ret[0]
                        spid["ActorSize(MB)"] += ret[1]/1024
                        total["ActorSize(MB)"] += ret[1]/1024
                        spid["ErrNum"] += ret[2]
                        total["ErrNum"] += ret[2]
                    elif zippack.tag == "runtime":
                        ret = match(zippack,logger,ip)
                        spid["RuntimeNum"] += ret[0]
                        total["RuntimeNum"] += ret[0]
                        spid["RuntimeSize(KB)"] += ret[1]
                        total["RuntimeSize(KB)"] += ret[1]
                        spid["ErrNum"] += ret[2]
                        total["ErrNum"] += ret[2]

        for f in agentxml.xmlfile(lastday):
            tree = ET.parse(f)
            root = tree.getroot()
            spid["SrvNum(last)"] += 1
            total["SrvNum(last)"] += 1
            for server in root:
                spid["GSrvNum(last)"] += 1
                total["GSrvNum(last)"] += 1
        backupmess.append(spid)
    total["Spid"] = "total %s"  % total["Spid"]
    backupmess.append(total)
    vrdallip = [line.split()[2] for line in open("/home/script/wycqip.txt").readlines() if "engine" in line]
    notbakip =  list(set(vrdallip) - set(allip))
    for ip in notbakip:
        mess = "ServerIP:%s  doesn't excute backup scripts."   % ip
        errmess.append(mess)
def match(zippack,logger,ip):
    ret = [1,0,0] # (num,size,err)
    f = backuppath + zippack.get("path") + zippack.get("name")
    if os.path.isfile(f):
        #if int(zippack.get("size")) < 5:
        #    mess = "ServerIP:%s  %s  filesize is smaller than 5KB." % (ip,zippack.get("name"))
        #    logging.error(mess)
        #    errmess.append(mess)
        #    ret[2] = 1
        if not zippack.get("md5") == md5sum(f):
            mess = "ServerIP:%s  %s  md5 unmatch." % (ip,zippack.get("name"))
            logger.error(mess)
            errmess.append(mess)
            ret[2] = 1
        ret[1] = int(zippack.get("size"))
    else:
        mess = "ServerIP:%s  %s  doesn't exist." % (ip,zippack.get("name"))
        logger.error(mess)
        errmess.append(mess)
        ret[0] = 0
        ret[2] = 1

    return ret

def log():
    logger = logging.getLogger("checkbackup")
    formatter = logging.Formatter("%(asctime)s %(name)s [%(levelname)s]: %(message)s")
    logger.setLevel(logging.DEBUG)
    log = logging.FileHandler(logfile)
    log.setLevel(logging.DEBUG)
    log.setFormatter(formatter)
    logger.addHandler(log)
    return logger

def chklog():
    if not os.path.exists(chklogpath):
        os.mkdir(chklogpath)
    chklogfile = "%s/chkbak.log" % chklogpath
    title = "Backup Check Report %s".center(126,"*") % date

    with open(chklogfile,"a") as f:
        f.write(title)
        f.write("\n")
        if backupmess:
            for filed in backupmess[0].keys():
                f.write(filed.ljust(14))
            f.write("\n")
            for agent in backupmess:
                for value in agent.values():
                    f.write(str(value).ljust(14))
                f.write("\n")
        f.write("*".center(134,"*"))
        f.write("\n")
        for err in errmess:
            f.write(err + "\n")
        f.write("\n\n\n\n")

def chkhtmllog():
    #chkhtmllogfile = "%s/chkbak_%s.html" % (chklogpath,date)
    html = Element("html")
    SubElement(html,"title").text= u"XXXX备份检查报告 %s" % date
    body = SubElement(html,"body")
    table = SubElement(body,"table",attrib={"border":"1","cellpadding":"10",
                                            "bgcolor":"#ABCDEF","align":"center","bordercolor":"white"})
    SubElement(table,"caption",attrib={"style":"font-size: 24px;color: #336699;font-weight:bold"}).text = "Backup Check Report %s" % date
    ftr = SubElement(table,"tr",attrib={"bgcolor":"#003366","style":"font-size:16px;color:white"})

    if backupmess:
        for filed in backupmess[0].keys():
            SubElement(ftr,"td").text = filed
        for agent in backupmess:
            ftr = SubElement(table,"tr")
            for value in agent.values():
                SubElement(ftr,"td").text = str(value)

    for err in errmess:
        etr = SubElement(table,"tr")
        SubElement(etr,"td",attrib={"colspan":"10","style":"font-size:18px;color:red"}).text = err

    xml = tostring(html)
    dom = parseString(xml)
    xml_message = dom.toprettyxml('    ',encoding="utf-8")

    #with open(chkhtmllogfile,"w+") as f:
    #   f.write(xml_message)

    mail(xml_message)

def mail(message):
    mailserver = "smtp.qq.com"
    frommail = "*******@qq.com"
    user = "******"
    password = "******"
    toall = ["********@qq.com",  # alex
              ]    
    #with open(chklogfile) as f:
    #    msg = MIMEText(f.read(),_subtype="html",_charset="utf-8")
    msg = MIMEText(message,_subtype="html",_charset="utf-8")
    msg['Subject'] = "****备份检查报告 %s" % date 
    #msg['From'] = "BackupCenter"
    msg['From'] = "*****@qq.com"
    for to in toall:
        s = smtplib.SMTP(mailserver)
        s.login(user,password)
        s.sendmail(frommail,[to],msg.as_string())
        s.quit()
        time.sleep(240)

def deloldbak(d):
    deldate = date - datetime.timedelta(days=d)
    backupdatelist = glob(backuppath + "[A-Z,0-9][A-Z,0-9][A-Z,0-9]/20[1-9][0-9]-[0-3][0-9]/20[1-9][0-9]-[0-1][0-9]-[0-3][0-9]")
    xmllist = glob(backuppath + "???/xml/*.xml")
    for f in backupdatelist:
        daylist = map(int,f.split("/")[-1].split("-"))
        day = datetime.date(daylist[0],daylist[1],daylist[2])
        if day < deldate:
            try:
                rmtree(f)
            except:
                pass
    for f in xmllist:
        if not os.path.getsize(f):
            os.remove(f)
        daylist = map(int,f.split("_")[3].split("-"))
        day = datetime.date(daylist[0],daylist[1],daylist[2])
        if day < deldate:
            try:
                os.remove(f)
            except:
                pass
if __name__ == "__main__":
    backuppath = "/data/BACKUP/02/WYCQ/LOGIC/"
    chklogpath = "%schkbaklog" % backuppath
    logfile = "/tmp/wycheckbackup.log"
    date = datetime.date.today()
    backupmess = []
    errmess = []
    allip = []
    deloldbak(5)
    runcheck()
    chklog()
    chkhtmllog()
