#!/usr/bin/python
# -*- coding: utf-8 -*-
#__author__ = 'zhengyanguang'
#write by '2019-12-03'
import requests
import re
import MySQLdb
idc_class_list=[]
def db_update_operate(sql):
    db = MySQLdb.connect("x.x.x.x","yw_idcoperate","7cxaXb5sGk4Z","cloudplayer_center_controller_prod",charset='utf8')
    cursor = db.cursor()
    # SQL 更新语句
    sql_phrase = sql
    print sql_phrase
    try:
       # 执行SQL语句
       cursor.execute(sql_phrase)
       print "Rows Changed: %s  Warnings: 0" % cursor.rowcount
       # 提交到数据库执行
       db.commit()
    except:
       # 发生错误时回滚
       db.rollback()
    db.close()
def db_select_operate():
    db = MySQLdb.connect("x.x.x.x","ywreader","hmyw@2016","cloudplayer_center_controller_prod",charset='utf8')
    cursor = db.cursor()
    sql = "select * from interface;"
    cursor.execute(sql)
    data = cursor.fetchall()
    db.close()
    for i in data:
        f_str= "%s-%s-%s" % (i[0],i[13],i[14])
        idc_class_list.append(f_str)
def handle_data(arg1):
    idc_class_dict={}
#    print arg1
    while len(arg1)>0:
        dict_element=[]
        B=arg1.pop(0)
        U=B.split('-')
        C="%s-%s" % (U[1],U[2])
        dict_element.append(U[0])
        for k in arg1:
            L=k.split('-')
            if bool(re.search(C,k)):
                dict_element.append(L[0])
            else:
                pass
        if idc_class_dict.has_key(C):
            pass
        else:
            idc_class_dict[C]=dict_element
    list_idc_num=list(enumerate(idc_class_dict.items()))
    for m in list_idc_num:
        print m[0],m[1][0],'线路id:',"["+",".join(m[1][1])+"]"

    return list_idc_num
#    for m in idc_class_dict:
#        print m,",".join(idc_class_dict[m])
def action_fun():
    print "操作类型二选一:"
    print "online:1"
    print "offline:2"
    at = raw_input('请键入操作类型(填数字):')
    return at
def user_input():
    offline_list=[]
    while True:
        offline_num = raw_input('请您输入要操作idc的序列编号(idc信息的第一列数字,例如0代表【浙江-杭州】),如果要操作多个idc请用逗号分隔:')
        try:
            for n in offline_num.split(','):
                if n.strip()=='':
                    raise Exception("错误：输入了空值，不合法")
                elif not n.isdigit():
                    raise Exception("错误：输入的非数字，不合法")
                else:
                    continue
        except Exception as e:
            print e
            continue
        else:
            break
    offline_n2=offline_num.split(',')
    for n in offline_n2:
        idx_n=int(n)
        offline_list.extend(list_idc_num[idx_n][1][1])
#        offline_list.append(n)
    return offline_list
def update_mysql_offline(num):
    print num
    str_num=','.join(num)
    sql="update location_route set valid=0 where interface_id in (%s)" % (str_num)
    db_update_operate(sql)

def update_mysql_online(num):
    print num
    str_num=','.join(num)
    sql="update location_route set valid=1 where interface_id in (%s)" % (str_num)
    db_update_operate(sql)

def request_api():
    url_list=['http://x.x.x.x:9080/route/refresh/all','http://x.x.x.x:9080/route/refresh/all','http://x.x.x.x:9080/route/refresh/all','http://x.x.x.x:9080/route/refresh/all','http://x.x.x.x:9080/route/location/list']
    headers={'Content-Type':'application/json'}
    for r in url_list:
        res=requests.post(r,headers=headers)
        print res
if __name__ == '__main__':
    db_select_operate()
    print "----------------idc线路信息打印开始-----------------"
    list_idc_num=handle_data(idc_class_list)
    print "----------------idc线路信息打印结束-----------------"
    op_type=action_fun()
#    print op_type
    num=user_input()
    print num
    if op_type=='1':
        print "online process"
        update_mysql_online(num)
    elif op_type=='2':
        print "offline process"
        update_mysql_offline(num)
    else:
        print "输入的操作类型不合法，退出程序"
        exit()
    print "-------调用api接口开始刷新,返回结果为200代表成功------"
    request_api()
    print "-------调用api接口刷新结束------"
