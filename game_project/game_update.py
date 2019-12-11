#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
import shutil
import time
import subprocess
from os.path import join, getsize

# 变量定义

gamePath = r"D:\games"
versionPath = r"D:\cqAdmin\version"
updatelist = glob.glob(r"%s\*" % versionPath)
serviceList = ["DBServer","LogicServer","GateServer","LocalLogServer"]
gatePath = r"%s\GateServer" % gamePath
localLogPath = r"%s\LocalLogServer" % gamePath
DBList = glob.glob(r"%s\DBServer*" % (gamePath))
logicList = glob.glob(r"%s\LogicServer*" % (gamePath))
log_path = "D:\\backup\\log"
locallogExe = 'LocalLogServer64_R.exe'
DBconfig = 'DBServer.txt'

mysqlDataPath = r'D:\MysqlData\data'
if os.path.exists(r'D:\Program Files\MySQL\MySQL Server 5.5\bin'):
    mysqlBinPath = r'D:\Program Files\MySQL\MySQL Server 5.5\bin'
elif os.path.exists(r"D:\MySQL\MySQL Server 5.5\bin"):
    mysqlBinPath = r"D:\MySQL\MySQL Server 5.5\bin"
else:
    mysqlBinPath = "error,please check"
actor = 'actor'

today = time.strftime("%Y%m%d", time.localtime())
bak_log = "%s\\update_version_%s.log" % (log_path,today)
timestat = time.strftime("%Y%m%d.%H%M%S", time.localtime())
if not os.path.exists(log_path):
    os.makedirs(log_path)
    if not os.path.exists(bak_log):
        systemlog=open(bak_log,'w')
        systemlog.close()
    else:
        systemlog=open(bak_log,'a')
        systemlog.close()

# 定义日志文件
def syslog(message=''):
    systemlog=open(bak_log,'a')
    systemlog.write(message+'\n')
    systemlog.close()
# 获取目录大小
def getdirsize(dir):
   size = 0L
   for root, dirs, files in os.walk(dir):
      size += sum([getsize(join(root, name)) for name in files])
   return size
# 拷贝文件
def copytree(src, dst, symlinks=False):
    names = os.listdir(src)
    if not os.path.isdir(dst):
        os.makedirs(dst)
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks)
            else:
                if os.path.isdir(dstname):
                    os.rmdir(dstname)
                elif os.path.isfile(dstname):
                    os.remove(dstname)
                shutil.copy2(srcname, dstname)
        except (IOError, os.error) as why:
            errors.append((srcname, dstname, str(why)))
        except OSError as err:
            errors.extend(err.args[0])
    try:
        shutil.copystat(src, dst)
    except WindowsError:
    # can't copy file access times on Windows
        pass
    except OSError as why:
        errors.extend((src, dst, str(why)))
    if errors:
        raise shutil.Error(errors)
# rsync同步版本，并显示最大版本内容信息
def rsync_version(ctype=None):
    syslog("[%s]:   开始rsync同步版本信息： " % timestat)
    rsync_bin = r"D:\cqAdmin\cwRsync_5.5.0\bin\rsync.exe"
    version_info = []
    if ctype == 'tw':
        rsync_option = r"-vzrtopg --progress --delete  root@ip::tmld_up_version/tw/ /cygdrive/D/cqAdmin/version/"
        version_info.append(u'rsync tw 台湾 version')
    elif ctype == 'nox':
        rsync_option = r"-vzrtopg --progress --delete  root@ip::tmld_up_version/nox/ /cygdrive/D/cqAdmin/version/"
        version_info.append(u'rsync nox 韩国 version')
    elif ctype == 'comm':
        rsync_option = r"-vzrtopg --progress --delete  root@ip::tmld_up_version/comm/ /cygdrive/D/cqAdmin/version/"
        version_info.append(u'rsync nox 综合服 version')
    else:
        rsync_option = r"-vzrtopg --progress --delete  root@ip::tmld_up_version/china/ /cygdrive/D/cqAdmin/version/"
        version_info.append(u'rsync china 大陆平台 version')

    versionPath = r"D:\cqAdmin\version"
    #version_info.append(u"rsync同步版本，并显示最大版本内容信息")
    try:
        rsync = os.system("\"%s\" %s" % (rsync_bin,rsync_option))
        if rsync == 0:
            syslog("[%s]:       rsync version success" % timestat)
            version_info.append("rsync version success")

            syslog("[%s]:   显示版本信息： " % timestat)
            versionLists = glob.glob(r"%s\*" % versionPath)
            verLists = []
            for ver in versionLists:
                verLists.append(ver.split('\\')[-1])
            if verLists:
                lists = []
                for ver in verLists:
                    #lists.append("版本目录：[%s]" % ver)
		            lists.append("目录：[%s] --> 大小：[%sb]" % (ver,getdirsize("%s\\%s" % (versionPath,ver))))
                    #lists.extend(glob.glob(r"%s\%s\*" % (versionPath,ver)))
                    #lists.append("[%sb]" % getdirsize("%s\\%s" % (versionPath,ver)))
                for l in lists:
                    syslog("[%s]:      :%s " % (timestat,l))
                version_info.extend(lists)
            else:
                syslog("[%s]:      not exits version " % timestat)
                version_info.append("not exits version")
        else:
            syslog("[%s]:       rsync version fail" % timestat)
            version_info.append("rsync version fail")
    except:
        version_info.append("os.system() fail")
        syslog("[%s]:       os.system() fail" % timestat)
    version_success = []
    version_fail = []
    for version in version_info:
        if "fail" in version:
            version_fail.append(version)
        else:
            version_success.append(version)
    if version_fail:
        return version_fail
    else:
        return version_success
# 获取机器游戏信息 spdi zone spguid
def get_game_info():
    # 获取机器上的平台spid
    splist = glob.glob(r'%s\*' % gamePath)
    spids = []
    for spid in splist:
        if 'LocalLogServer' not in spid and os.path.isdir(spid):
            spids.append(spid)
        #if spid.split('\\')[-1] == "LocalLogServer" :
        #    spids.remove(spid)
        #if os.path.isfile(spid):
        #    spids.remove(spid)
    # 获取平台的游戏区服
    games = []
    for spid in spids:
        zones = glob.glob('%s\*' % spid)
        for zone in zones:
            if os.path.isfile(zone):
                zones.remove(zone)
        games.extend(zones)
    return spids,games
# 显示程序运行状态
def check_games_status():
    syslog("[%s]:   检查游戏运行状态： " % timestat)
    checkService = ['DBServer64_R.exe','LogicServerCQ64_R.exe','GateServer64_R.exe','LocalLogServer64_R.exe']
    serviceList = []
    spacing = 25
    for service in checkService:
        tmplist = []
        if "LocalLogServer" in service:
            tmpservicelist = os.popen('wmic process where name="%s" get executablepath | find "%s"' % (service,service))
            for tmp in tmpservicelist:
                tmplist.append(tmp)
            str = "%s : %s" % (service.ljust(spacing),len(tmplist))
            serviceList.append(str)
            syslog("[%s]:       %s" % (timestat,str))

        else:
            zone_index = []
            try:
                tmpservicelist = os.popen('wmic process where name="%s" get executablepath | find "%s"' % (service,service))
            except Exception,e:
                syslog("[%s]:       获取%s程序进程信息失败,[%s]" % (timestat,service,e))
            for tmp in tmpservicelist:
                tmplist.append(tmp)
                zone_index.append("%s_%s" % (tmp.split('\\')[2],tmp.split("\\")[3]))
            str = "%s : %s  -->%s" % (service.ljust(spacing),len(tmplist),zone_index)
            serviceList.append(str)
            syslog("[%s]:       %s" % (timestat,str))

    return serviceList
# 获取进程列表
def getProcess(*arg):
    Process = []
    for engine in arg:
        enginList = os.popen('wmic process where name="%s" get executablepath | find "%s"' % (engine,engine))
        for engine in enginList:
            Process.append(r"%s_%s" % (engine.split('\\')[2],engine.split('\\')[3]))
    return Process
# 获取退出区服列表
def quit_engine_list():
    DBOnList = getProcess('DBServer64_R.exe','DBServer64_D.exe')
    LogicOnList = getProcess('LogicServerCQ64_R.exe','LogicServerCQ64_D.exe')
    spids, games = get_game_info()
    quitList = []
    for zone in games:
        zone_num = r"%s_%s" % (zone.split('\\')[2],zone.split('\\')[3])
        if zone_num not in DBOnList and zone_num not in LogicOnList:
            quitList.append(zone)

    return quitList
# 更新游戏区服代码,针对停服更新,过滤已开启的区服
def update_engine(version=0,spid=0,zone=0):
    quitList = quit_engine_list()
    syslog("[%s]:   模块[update_engine]更新日志记录： " % timestat)
    print "[%s]:   模块[update_engine]更新日志记录： " % timestat
    str = ""
    sql_str = ''
    status = []
    ok = "update_ok"
    fail = "update_fail"
    sql_ok = "sql_ok"
    sql_fail = "sql_fail"

    mysqlPath = r'"D:\Program Files\MySQL\MySQL Server 5.1\bin\mysql"'
    mysqlUpOption = '-uroot -plogic!@#happy'

    if version == 0 or spid == 0 or zone == 0:
        syslog("[%s]:       更新参数错误设置错误 " % timestat)
        return u"更新参数设置错误"
    else:
        if quitList:
            upVersion = r"%s\%s" % (versionPath,version)
            upVersionList = glob.glob(r"%s\*" % upVersion)

            sqlList = glob.glob(r"%s\%s\sql\*.sql" % (upVersion,serviceList[0]))
            print u"本次更新sql文件：%s" % sqlList
            if os.path.exists(upVersion) and len(upVersionList):

                if spid == 'all' and zone == 'all':
                    # 更新全部平台的所有区服
                    syslog("[%s]:       更新参数为:%s 平台的 %s 区服 " % (timestat,spid,zone))
                    print "[%s]:       更新参数为:%s 平台的 %s 区服 " % (timestat,spid,zone)
                    for zone in quitList:
                        # 程序代码更新操作
                        zone_num = r'%s_%s' % (zone.split('\\')[-2],zone.split('\\')[-1])
                        try:
                            copytree('%s\\' % upVersion, zone)
                            str += "%s:%s " % (zone_num, ok)
                            status.append("%s:%s" % (zone_num, ok))
                            syslog("[%s]:           %s 更新成功 " % (timestat, zone_num))
                        except Exception,e:
                            print Exception,":",e
                            str += "%s:%s " % (zone_num, fail)
                            status.append("%s:%s" % (zone_num, fail))
                            syslog("[%s]:           %s 更新失败 ,%s" % (timestat, zone_num,e))
                    status_ok = []
                    status_fail = []
                    for st in status:
                        if "fail" in st:
                            status_fail.append(st)
                        else:
                            status_ok.append(st)
                    if status_fail:
                        syslog("[%s]:       更新失败的程序列表为：%s " % (timestat,status_fail))
                        return status_fail
                    else:
                        syslog("[%s]:       更新成功的程序列表为：%s " % (timestat,status_ok))
                        status_ok.append("ALL engine update ok")
                        return status_ok

                elif spid != 'all' and zone == 'all':
                    # 更新某个平台的所有区服
                    syslog("[%s]:       更新参数为:%s 平台的 %s 区服 " % (timestat,spid,zone))
                    print "[%s]:       更新参数为:%s 平台的 %s 区服 " % (timestat,spid,zone)
                    for zone in quitList:
                        if spid in zone:
                            # 程序代码更新操作
                            zone_num = r'%s_%s' % (zone.split('\\')[-2], zone.split('\\')[-1])
                            print zone_num
                            try:
                                copytree('%s\\' % upVersion, zone)
                                str += "%s:%s " % (zone_num, ok)
                                status.append("%s:%s" % (zone_num, ok))
                                syslog("[%s]:           %s 更新成功 " % (timestat, zone_num))
                            except:
                                str += "%s:%s " % (zone_num, fail)
                                status.append("%s:%s" % (zone_num, fail))
                                syslog("[%s]:           %s 更新失败 " % (timestat, zone_num))
                        else:
                            return u"%s平台的区服未部署在此机器上" % spid

                    status_ok = []
                    status_fail = []
                    if status:
                        for st in status:
                            if "fail" in st:
                                status_fail.append(st)
                            else:
                                status_ok.append(st)

                        if status_fail:
                            syslog("[%s]:       更新失败的程序列表为：%s " % (timestat, status_fail))
                            return status_fail
                        else:
                            syslog("[%s]:       更新成功的程序列表为：%s " % (timestat, status_ok))
                            status_ok.append("ALL engine update ok")
                            return status_ok
                    else:
                        return u"%s平台的区服正在运行" % spid
                elif spid != 'all' and zone != 'all':
                    #
                    syslog("[%s]:       更新参数为指定[%s_s%s]区服更新 " % (timestat,spid,zone))
                    print "[%s]:       更新参数为指定[%s_s%s]区服更新 " % (timestat, spid, zone)
                    zone_num = r'%s\%s' % (spid,zone)
                    if os.path.exists(r'%s\%s' % (gamePath,zone_num)):
                        for z in quitList:
                            spid_zone = z.split('\\')[-2]+'_'+z.split('\\')[-1]
                            run_spid_zone = spid + '_' + zone
                            if spid_zone == run_spid_zone:
                                # 程序代码更新操作
                                try:
                                    copytree('%s\\' % upVersion, z)
                                    str += "%s_%s:%s " % (spid,zone,ok)
                                    status.append("%s_%s:%s " % (spid,zone,ok))
                                    syslog("[%s]:           %s_%s 更新成功 " % (timestat, spid,zone))
                                except:
                                    str += "%s_%s:%s " % (spid,zone,fail)
                                    status.append("%s_%s:%s " % (spid,zone,fail))
                                    syslog("[%s]:           %s_%s 更新失败 " % (timestat, spid,zone))
                    else:
                        return u"%s平台的%s_%s区服未部署在这台机器上，请检查参数设置" % (spid,spid,zone)
                    status_ok = []
                    status_fail = []
                    if status:
                        for st in status:
                            if "fail" in st:
                                status_fail.append(st)
                            else:
                                status_ok.append(st)

                        if status_fail:
                            syslog("[%s]:       更新失败的程序列表为：%s " % (timestat, status_fail))
                            return status_fail
                        else:
                            syslog("[%s]:       更新成功的程序列表为：%s " % (timestat, status_ok))
                            status_ok.append("ALL engine update ok")
                            return status_ok
                    else:
                        return u"%s平台的%s_%s区服正在运行" % (spid,spid,zone)
                else:
                    syslog("[%s]:       更新区服 参数错误 " % timestat)
                    return u"更新区服 参数错误"
            else:
                syslog("[%s]:       版本参数和版本信息不匹配 或者 版本内容为空 " % timestat)
                return u"版本参数和版本信息不匹配 或者 版本内容为空"
        else:
            return u"此机器为空闲机器"
# 更新游戏区服代码和sql文件,针对停服更新,过滤已开启的区服
def update_engine_sql(version=0,spid=0,zone=0):
    quitList = quit_engine_list()
    syslog("[%s]:   模块[update_engine]更新日志记录： " % timestat)
    print "[%s]:   模块[update_engine]更新日志记录： " % timestat
    str = ""
    sql_str = ''
    status = []
    ok = "update_ok"
    fail = "update_fail"
    sql_ok = "sql_ok"
    sql_fail = "sql_fail"

    #mysqlPath = r'"D:\Program Files\MySQL\MySQL Server 5.1\bin\mysql"'
    mysqlPath = r"%s\mysql" % mysqlBinPath
    mysqlUpOption = '-uops -pdR23f7Idf78f3'

    if version == 0 or spid == 0 or zone == 0:
        syslog("[%s]:       更新参数错误设置错误 " % timestat)
        return u"更新参数设置错误"
    else:
        if quitList:
            upVersion = r"%s\%s" % (versionPath,version)
            upVersionList = glob.glob(r"%s\*" % upVersion)

            sqlList = glob.glob(r"%s\%s\sql\*.sql" % (upVersion,serviceList[0]))
            print u"本次更新sql文件：%s" % sqlList
            if os.path.exists(upVersion) and len(upVersionList):
                if spid == 'all' and zone == 'all':
                    # 更新全部平台的所有区服
                    syslog("[%s]:       更新参数为:%s 平台的 %s 区服 " % (timestat,spid,zone))
                    print "[%s]:       更新参数为:%s 平台的 %s 区服 " % (timestat,spid,zone)
                    for zone in quitList:
                        if sqlList and len(sqlList) == 1:
                            # sql 更新
                            DBconfigFile = r"%s\DBServer\%s" % (zone,DBconfig)
                            dblist = []
                            if os.path.exists(DBconfigFile):
                                with open(DBconfigFile, 'r') as f:
                                    for line in f.readlines():
                                        if "DBName" in line:
                                            dblist.append(line.split("\"")[1])

                            sqlFile = sqlList[0]
                            if dblist:
                                for db in dblist:
                                    mysqlCmd = '\"%s\" %s %s < %s' % (mysqlPath, mysqlUpOption, db, sqlFile)
                                    print mysqlCmd
                                    cmdStatus = os.system(mysqlCmd)
                                    if cmdStatus == 0:
                                        sql_str += "%s:%s " % (db.split("\\")[-1], sql_ok)
                                        status.append("%s:%s" % (db.split("\\")[-1], sql_ok))
                                        syslog("[%s]:           %s 更新成功 " % (timestat, db.split("\\")[-1]))
                                    else:
                                        sql_str += "%s:%s " % (db.split("\\")[-1], sql_fail)
                                        status.append("%s:%s" % (db.split("\\")[-1], sql_fail))
                                        syslog("[%s]:           %s 更新失败 " % (timestat, db.split("\\")[-1]))
                        # 程序代码更新操作
                        zone_num = r'%s_%s' % (zone.split('\\')[-2],zone.split('\\')[-1])
                        try:
                            copytree('%s\\' % upVersion, zone)
                            str += "%s:%s " % (zone_num, ok)
                            status.append("%s:%s" % (zone_num, ok))
                            syslog("[%s]:           %s 更新成功 " % (timestat, zone_num))
                        except Exception,e:
                            print Exception,":",e
                            str += "%s:%s " % (zone_num, fail)
                            status.append("%s:%s" % (zone_num, fail))
                            syslog("[%s]:           %s 更新失败 ,%s" % (timestat, zone_num,e))
                    status_ok = []
                    status_fail = []
                    for st in status:
                        if "fail" in st:
                            status_fail.append(st)
                        else:
                            status_ok.append(st)
                    if status_fail:
                        syslog("[%s]:       更新失败的程序列表为：%s " % (timestat,status_fail))
                        return status_fail
                    else:
                        syslog("[%s]:       更新成功的程序列表为：%s " % (timestat,status_ok))
                        status_ok.append("ALL engine update ok")
                        return status_ok

                elif spid != 'all' and zone == 'all':
                    # 更新某个平台的所有区服
                    syslog("[%s]:       更新参数为:%s 平台的 %s 区服 " % (timestat,spid,zone))
                    print "[%s]:       更新参数为:%s 平台的 %s 区服 " % (timestat,spid,zone)

                    quit_spid = []
                    for q in quitList:
                        quit_spid.append(q.split("\\")[-2])
                    if spid not in quit_spid:
                        return u"%s平台的区服未部署在此机器上或者区服正在运行" % spid
                    for zone in quitList:
                        if spid in zone:
                            if sqlList and len(sqlList) == 1:
                                # sql 更新
                                DBconfigFile = r"%s\DBServer\%s" % (zone, DBconfig)
                                dblist = []
                                if os.path.exists(DBconfigFile):
                                    with open(DBconfigFile, 'r') as f:
                                        for line in f.readlines():
                                            if "DBName" in line:
                                                dblist.append(line.split("\"")[1])

                                sqlFile = sqlList[0]
                                if dblist:
                                    for db in dblist:
                                        mysqlCmd = '\"%s\" %s %s < %s' % (mysqlPath, mysqlUpOption, db, sqlFile)
                                        print mysqlCmd
                                        cmdStatus = os.system(mysqlCmd)
                                        if cmdStatus == 0:
                                            sql_str += "%s:%s " % (db.split("\\")[-1], sql_ok)
                                            status.append("%s:%s" % (db.split("\\")[-1], sql_ok))
                                            syslog("[%s]:           %s 更新成功 " % (timestat, db.split("\\")[-1]))
                                        else:
                                            sql_str += "%s:%s " % (db.split("\\")[-1], sql_fail)
                                            status.append("%s:%s" % (db.split("\\")[-1], sql_fail))
                                            syslog("[%s]:           %s 更新失败 " % (timestat, db.split("\\")[-1]))
                            # 程序代码更新操作
                            zone_num = r'%s_%s' % (zone.split('\\')[-2], zone.split('\\')[-1])
                            #print zone_num
                            try:
                                copytree('%s\\' % upVersion, zone)
                                str += "%s:%s " % (zone_num, ok)
                                status.append("%s:%s" % (zone_num, ok))
                                syslog("[%s]:           %s 更新成功 " % (timestat, zone_num))
                            except:
                                str += "%s:%s " % (zone_num, fail)
                                status.append("%s:%s" % (zone_num, fail))
                                syslog("[%s]:           %s 更新失败 " % (timestat, zone_num))

                    status_ok = []
                    status_fail = []
                    if status:
                        for st in status:
                            if "fail" in st:
                                status_fail.append(st)
                            else:
                                status_ok.append(st)

                        if status_fail:
                            syslog("[%s]:       更新失败的程序列表为：%s " % (timestat, status_fail))
                            return status_fail
                        else:
                            syslog("[%s]:       更新成功的程序列表为：%s " % (timestat, status_ok))
                            status_ok.append("ALL engine update ok")
                            return status_ok
                    else:
                        return u"%s平台的区服正在运行" % spid
                elif spid != 'all' and zone != 'all':
                    #
                    syslog("[%s]:       更新参数为指定[%s_%s]区服更新 " % (timestat,spid,zone))
                    print "[%s]:       更新参数为指定[%s_%s]区服更新 " % (timestat, spid, zone)
                    zone_num = r'%s\%s' % (spid,zone)
                    if os.path.exists(r'%s\%s' % (gamePath,zone_num)):
                        for z in quitList:
                            spid_zone = z.split('\\')[-2]+'_'+z.split('\\')[-1]
                            run_spid_zone = spid + '_' + zone
                            if spid_zone == run_spid_zone:
                                if sqlList and len(sqlList) == 1:
                                    # sql 更新
                                    DBconfigFile = r"%s\DBServer\%s" % (z, DBconfig)
                                    dblist = []
                                    if os.path.exists(DBconfigFile):
                                        with open(DBconfigFile, 'r') as f:
                                            for line in f.readlines():
                                                if "DBName" in line:
                                                    dblist.append(line.split("\"")[1])

                                    sqlFile = sqlList[0]
                                    if dblist:
                                        for db in dblist:
                                            mysqlCmd = '\"%s\" %s %s < %s' % (mysqlPath, mysqlUpOption, db, sqlFile)
                                            print mysqlCmd
                                            cmdStatus = os.system(mysqlCmd)
                                            if cmdStatus == 0:
                                                sql_str += "%s:%s " % (db.split("\\")[-1], sql_ok)
                                                status.append("%s:%s" % (db.split("\\")[-1], sql_ok))
                                                syslog("[%s]:           %s 更新成功 " % (timestat, db.split("\\")[-1]))
                                            else:
                                                sql_str += "%s:%s " % (db.split("\\")[-1], sql_fail)
                                                status.append("%s:%s" % (db.split("\\")[-1], sql_fail))
                                                syslog("[%s]:           %s 更新失败 " % (timestat, db.split("\\")[-1]))
                                # 程序代码更新操作
                                try:
                                    copytree('%s\\' % upVersion, z)
                                    str += "%s_%s:%s " % (spid,zone,ok)
                                    status.append("%s_%s:%s " % (spid,zone,ok))
                                    syslog("[%s]:           %s_%s 更新成功 " % (timestat, spid,zone))
                                except:
                                    str += "%s_s%s:%s " % (spid,zone,fail)
                                    status.append("%s_s%s:%s " % (spid,zone,fail))
                                    syslog("[%s]:           %s_%s 更新失败 " % (timestat, spid,zone))
                    else:
                        return u"%s平台的%s_%s区服未部署在这台机器上，请检查参数设置" % (spid,spid,zone)
                    status_ok = []
                    status_fail = []
                    if status:
                        for st in status:
                            if "fail" in st:
                                status_fail.append(st)
                            else:
                                status_ok.append(st)

                        if status_fail:
                            syslog("[%s]:       更新失败的程序列表为：%s " % (timestat, status_fail))
                            return status_fail
                        else:
                            syslog("[%s]:       更新成功的程序列表为：%s " % (timestat, status_ok))
                            status_ok.append("ALL engine update ok")
                            return status_ok
                    else:
                        return u"%s平台的%s_%s区服正在运行" % (spid,spid,zone)
                else:
                    syslog("[%s]:       更新区服 参数错误 " % timestat)
                    return u"更新区服 参数错误"
            else:
                syslog("[%s]:       版本参数和版本信息不匹配 或者 版本内容为空 " % timestat)
                return u"版本参数和版本信息不匹配 或者 版本内容为空"
        else:
            return u"此机器为空闲机器"
# 更新游戏区服代码,针对线上热更新，不管游戏是否开启
def update_files(version=0,spid=0,zone=0):
    syslog("[%s]:   模块[update_files]更新日志记录： " % timestat)
    print "[%s]:   模块[update_files]更新日志记录： " % timestat
    if version == 0 or spid == 0 or zone == 0:
        syslog("[%s]:       更新参数错误：参数个数为0 " % timestat)
        return u"更新 参数错误"
    else:
        upVersion = r"%s\%s" % (versionPath,version)
        upVersionList = glob.glob(r"%s\*" % upVersion)
        sp,games = get_game_info()
        spids = []
        for sid in sp:
            spids.append(sid.split("\\")[-1])
        if games:
            if os.path.exists(upVersion) and len(upVersionList):
                str = ""
                status = []
                ok = "update_ok"
                fail = "update_fail"
                if spid == 'all' and zone == 'all':
                    # 更新全部平台的所有区服
                    syslog("[%s]:       更新参数为:%s 平台的 %s 区服 " % (timestat, spid, zone))
                    print "[%s]:       更新参数为:%s 平台的 %s 区服 " % (timestat, spid, zone)
                    for z in games:
                        # 程序代码更新操作
                        zone_num = r'%s_%s' % (z.split('\\')[-2], z.split('\\')[-1])
                        try:
                            copytree('%s' % upVersion, z)
                            str += "%s:%s " % (zone_num, ok)
                            status.append("%s:%s" % (zone_num, ok))
                            syslog("[%s]:           %s 更新成功 " % (timestat, zone_num))
                        except:
                            str += "%s:%s " % (zone_num, fail)
                            status.append("%s:%s" % (zone_num, fail))
                            syslog("[%s]:           %s 更新失败 " % (timestat, zone_num))
                    status_ok = []
                    status_fail = []
                    for st in status:
                        if "fail" in st:
                            status_fail.append(st)
                        else:
                            status_ok.append(st)
                    if status_fail:
                        syslog("[%s]:       更新失败的程序列表为：%s " % (timestat, status_fail))
                        return status_fail
                    else:
                        syslog("[%s]:       更新成功的程序列表为：%s " % (timestat, status_ok))
                        status_ok.append("ALL engine update ok")
                        return status_ok
                elif spid != 'all' and zone == 'all':
                    # 更新某个平台的所有区服
                    syslog("[%s]:       更新参数为:%s 平台的 %s 区服 " % (timestat, spid, zone))
                    print "[%s]:       更新参数为:%s 平台的 %s 区服 " % (timestat, spid, zone)
                    if spid not in spids:
                        return u"%s平台的区服未部署在此机器上" % spid
                    for z in games:
                        if spid in z:
                            # 程序代码更新操作
                            zone_num = r'%s_%s' % (z.split('\\')[-2], z.split('\\')[-1])
                            #print zone_num
                            try:
                                copytree('%s\\' % upVersion, z)
                                str += "%s:%s " % (zone_num, ok)
                                status.append("%s:%s" % (zone_num, ok))
                                syslog("[%s]:           %s 更新成功 " % (timestat, zone_num))
                            except:
                                str += "%s:%s " % (zone_num, fail)
                                status.append("%s:%s" % (zone_num, fail))
                                syslog("[%s]:           %s 更新失败 " % (timestat, zone_num))

                    status_ok = []
                    status_fail = []
                    if status:
                        for st in status:
                            if "fail" in st:
                                status_fail.append(st)
                            else:
                                status_ok.append(st)

                        if status_fail:
                            syslog("[%s]:       更新失败的程序列表为：%s " % (timestat, status_fail))
                            return status_fail
                        else:
                            syslog("[%s]:       更新成功的程序列表为：%s " % (timestat, status_ok))
                            status_ok.append("ALL engine update ok")
                            return status_ok
                    else:
                        return u"%s平台的区服正在运行" % spid
                elif spid != 'all' and zone != 'all':
                    #
                    syslog("[%s]:       更新参数为指定[%s_%s]区服更新 " % (timestat, spid, zone))
                    print "[%s]:       更新参数为指定[%s_%s]区服更新 " % (timestat, spid, zone)
                    zone_num = r'%s\%s' % (spid, zone)
                    if os.path.exists(r'%s\%s' % (gamePath, zone_num)):
                        for z in games:
                            spid_zone = z.split('\\')[-2]+'_'+z.split('\\')[-1]
                            run_spid_zone = spid + '_' + zone
                            if spid_zone == run_spid_zone:
                                # 程序代码更新操作
                                try:
                                    copytree('%s\\' % upVersion, z)
                                    str += "%s_%s:%s " % (spid, zone, ok)
                                    status.append("%s_%s:%s " % (spid, zone, ok))
                                    syslog("[%s]:           %s_%s 更新成功 " % (timestat, spid, zone))
                                except:
                                    str += "%s_%s:%s " % (spid, zone, fail)
                                    status.append("%s_%s:%s " % (spid, zone, fail))
                                    syslog("[%s]:           %s_%s 更新失败 " % (timestat, spid, zone))
                    else:
                        return u"%s平台的%s_%s区服未部署在这台机器上，请检查参数设置" % (spid, spid, zone)
                    status_ok = []
                    status_fail = []
                    if status:
                        for st in status:
                            if "fail" in st:
                                status_fail.append(st)
                            else:
                                status_ok.append(st)

                        if status_fail:
                            syslog("[%s]:       更新失败的程序列表为：%s " % (timestat, status_fail))
                            return status_fail
                        else:
                            syslog("[%s]:       更新成功的程序列表为：%s " % (timestat, status_ok))
                            status_ok.append("ALL engine update ok")
                            return status_ok
                    else:
                        return u"%s平台的%s_%s区服正在运行" % (spid, spid, zone)
                else:
                    syslog("[%s]:       更新区服 参数错误 " % timestat)
                    return u"更新区服 参数错误"
            else:
                syslog("[%s]:       版本参数和版本信息不匹配 或者 版本内容为空 " % timestat)
                return u"版本参数和版本信息不匹配 或者 版本内容为空"
        else:
            return u"此机器为空闲机器"
# 开启游戏区服
def start_engine():
    quitZoneList = quit_engine_list()
    syslog("[%s]:   模块[start_engine]更新日志记录： " % timestat)
    print "[%s]:   模块[start_engine]更新日志记录： " % timestat
    status = []
    start_ok = "start_ok"
    start_fail = "start_fail"
    status_ok = []
    status_fail = []
    startEngineBat = 'StartServer.bat'

    # 开启已关闭的游戏区服
    syslog("[%s]:       启动游戏区服程序，需要启动的列表为：%s " % (timestat,quitZoneList))
    print "[%s]:       启动游戏区服程序，需要启动的列表为：%s " % (timestat,quitZoneList)
    for quitZone in quitZoneList:
        z_num = r'%s_%s' % (quitZone.split('\\')[-2],quitZone.split('\\')[-1])
        os.chdir(quitZone)
        try:
            subprocess.Popen("cmd /c start /min %s " % startEngineBat)
            status.append("%s:%s" % (z_num,start_ok))
            syslog("[%s]:           %s 启动成功" % (timestat,z_num))
            print "[%s]:           %s 启动成功" % (timestat,z_num)
        except Exception, e:
            status.append("%s:%s" % (z_num,start_fail))
            syslog("[%s]:           %s 启动失败" % (timestat,z_num))
            print "[%s]:           %s 启动失败" % (timestat,z_num)
            print Exception,":", e
            print u"启动出错，请检查程序是否存在"


    for st in status:
        if "fail" in st:
            status_fail.append(st)
        else:
            status_ok.append(st)
    if status_fail:
        syslog("[%s]:       启动程序失败列表为：%s " % (timestat,status_fail))
        return status_fail
    else:
        syslog("[%s]:       启动程序成功列表为：%s " % (timestat,status_fail))
        return status_ok
# 开启网关和本地日志程序
def start_gateserver():
    spid,games = get_game_info()
    syslog("[%s]:   模块[start_gateserver]更新日志记录： " % timestat)
    print "[%s]:   模块[start_gateserver]更新日志记录： " % timestat
    status = []
    start_ok = "s_gate_ok"
    start_fail = "s_gate_fail"
    status_ok = []
    status_fail = []
    startEngineBat = 'StartGate.bat'

    # 开启已关闭的游戏区服
    syslog("[%s]:       启动游戏区服网关程序，需要启动的列表为：%s " % (timestat, games))
    print "[%s]:       启动游戏区服网关程序，需要启动的列表为：%s " % (timestat, games)
    for quitZone in games:
        z_num = r'%s_%s' % (quitZone.split('\\')[-2], quitZone.split('\\')[-1])
        os.chdir(quitZone)
        try:
            subprocess.Popen("cmd /c start /min %s " % startEngineBat)
            status.append("%s:%s" % (z_num, start_ok))
            syslog("[%s]:           %s 启动成功" % (timestat, z_num))
            print "[%s]:           %s 启动成功" % (timestat, z_num)
        except Exception, e:
            status.append("%s:%s" % (z_num, start_fail))
            syslog("[%s]:           %s 启动失败" % (timestat, z_num))
            print "[%s]:           %s 启动失败" % (timestat, z_num)
            print Exception, ":", e
            print u"启动出错，请检查程序是否存在"

    # 开启 LocalLogServer
    syslog("[%s]:       启动LocalLogServer程序，需要启动的列表为：%s " % (timestat, localLogPath))
    print "[%s]:       启动LocalLogServer程序，需要启动的列表为：%s " % (timestat, localLogPath)
    os.chdir(r"%s\x64" % localLogPath)
    try:
        subprocess.Popen("cmd /c start /min %s " % locallogExe)
        status.append("%s:%s" % (localLogPath.split("\\")[-1], start_ok))
        syslog("[%s]:           %s 启动成功" % (timestat, localLogPath.split("\\")[-1]))
        print "[%s]:           %s 启动成功" % (timestat, localLogPath.split("\\")[-1])
    except Exception, e:
        status.append("%s:%s" % (localLogPath.split("\\")[-1], start_fail))
        syslog("[%s]:           %s 启动失败" % (timestat, localLogPath.split("\\")[-1]))
        print "[%s]:           %s 启动失败" % (timestat, localLogPath.split("\\")[-1])
        print Exception, ":", e
        print u"启动出错，请检查程序是否存在"

    for st in status:
        if "fail" in st:
            status_fail.append(st)
        else:
            status_ok.append(st)
    if status_fail:
        syslog("[%s]:       启动程序失败列表为：%s " % (timestat, status_fail))
        return status_fail
    else:
        syslog("[%s]:       启动程序成功列表为：%s " % (timestat, status_fail))
        return status_ok
# 通过配置文件获取数据库名称
def get_db_list():
    spids,games = get_game_info()
    dblist = []
    for z in games:
        DBconfigFile =  r"%s\DBServer\%s" % (z,DBconfig)
        if os.path.exists(DBconfigFile):
            with open(DBconfigFile,'r') as f:
                for line in f.readlines():
                    if "DBName" in line:
                        dblist.append(line.split("\"")[1])
    return dblist
# 更新sql脚本
def update_sql(version=0):
    syslog("[%s]:   模块[update_sql]更新日志记录： " % timestat)
    print "[%s]:   模块[update_sql]更新日志记录： " % timestat
    sql_str = ''
    status = []
    sql_ok = "sql_ok"
    sql_fail = "sql_fail"
    #mysqlbin = r"D:\Program Files\MySQL\MySQL Server 5.5\bin"
    if version == 0:
        syslog("[%s]:       更新参数错误设置错误 " % timestat)
        return u"更新参数设置错误"
    #if os.path.exists(mysqlDataPath):
    if True:
        sqlList = glob.glob(r'%s\%s\DBServer\sql\*.sql' % (versionPath,version))
        if os.path.exists(r'%s\%s\DBServer\sql' % (versionPath,version)) and len(sqlList) == 1:
            sqlFile = sqlList[0]
            print sqlList
            mysqlUpOption = '-uops -pdR23f7Idf78f3'
            #mysqlUpOption = '-uroot -ptmldsa'
            os.chdir(mysqlDataPath)
            #actorList = glob.glob(r'*%s*' % actor)
            actorList = get_db_list()
            print actorList
            #os.chdir(mysqlbin)
            for actorid in actorList:
                mysqlCmd = "\"%s\\mysql.exe\" %s %s < %s" % (mysqlBinPath,mysqlUpOption, actorid, sqlFile)
                print mysqlCmd
                cmdStatus = os.system(r"%s" % mysqlCmd)
                if cmdStatus == 0:
                    sql_str += "%s:%s " % (actorid, sql_ok)
                    status.append("%s:%s" % (actorid, sql_ok))
                    syslog("[%s]:           %s sql更新成功 " % (timestat, actorid))
                else:
                    sql_str += "%s:%s " % (actorid, sql_fail)
                    status.append("%s:%s" % (actorid, sql_fail))
                    syslog("[%s]:           %s sql更新失败 " % (timestat, actorid))
        else:
            return u"sql文件未同步到位或者存在多个sql文件"
    else:
        return u"mysqldata 目录不是统一格式：[%s],更新sql失败" % mysqlDataPath

    status_ok = []
    status_fail = []
    for st in status:
        if "fail" in st:
            status_fail.append(st)
        else:
            status_ok.append(st)
    if status_fail:
        syslog("[%s]:       更新失败的程序列表为：%s " % (timestat, status_fail))
        return status_fail
    else:
        syslog("[%s]:       更新成功的程序列表为：%s " % (timestat, status_ok))
        status_ok.append("ALL actor update ok")
        return status_ok
