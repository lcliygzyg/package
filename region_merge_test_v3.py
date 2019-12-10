#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,sys
import socket
import re
import time
import logging
import socket
import commands
import argparse

def parse_args():
    """Parse the args from main."""
    parser = argparse.ArgumentParser(description=help_desc)
    parser.add_argument("-n", "--table_name",
        help="针对哪个表操作合并region",
        type=str,
        default="ias_scheduler"
    )
    parser.add_argument("-s", "--sum",
        help="两个相邻region大小之和小于当前指定的阀值单位M",
        type=int,
        default=1000
    )
    parser.add_argument("-m", "--min_size",
        help="两个相邻region中但凡出现一个region大小小于当前指定的阀值单位M",
        type=int,
        default=100
    )
    parser.add_argument("-t", "--time_interval",
        help="所要合并的相邻region，它的创建时间戳必须大于当前时间N小时",
        type=int,
        default=2
    )

    return parser.parse_args()

def init_log():
    loger=logging.getLogger()
    loger.setLevel(logging.DEBUG)
    hf=logging.FileHandler("/home/hbase2/merge_region_log",mode='a')
    recordfmt=logging.Formatter('%(asctime)s\t\t%(levelname)s: %(message)s')
    hf.setFormatter(recordfmt)
    loger.addHandler(hf)
    return loger
#此模块用hbase shell抓出要处理的region列表

def generate_file():
    cmd_step1='echo \'list_regions "ias_scheduler"\' | /service/hbase2/bin/hbase shell>/home/hbase2/region_info.txt'
    cmd_step2='cat /home/hbase2/region_info.txt | grep \'|\' |awk -F\'|\' \'{print $2,$5}\' | grep -v \'REGION_NAME\' | sed -n \'5,$p\' |awk -F\',\' \'{print $3}\'>/home/hbase2/region_filter.txt'
    stat1,rt1=commands.getstatusoutput(cmd_step1)
    stat2,rt2=commands.getstatusoutput(cmd_step2)


#将region名和region size分别装入两个列表
def paser_file(scriptpath):
    with open(scriptpath+'/region_filter.txt', 'r') as f:
        for line in f.readlines():
            ns=line.split('    ')
            region_name_list.append(ns[0].strip('.'))
            region_size_list.append(ns[1].strip(' \n'))
#            print region_name_list
#            print region_size_list

#开始执行合并逻辑
def merge_fun(r_size_lt,r_sum_size,r_min_size,t_itl):
    print "--------------------------------------------------------------------"
    print "--------------------------------------------------------------------"
    #遍历这个生成的大列表，做判断来触发merge
    lst = iter(range(len(r_size_lt)-1))
    logger=init_log()
    for i in lst:
        print i,i+1
        if  not all([r_size_lt[i],r_size_lt[i+1]]):
            print ""
            print "--------------------------------------------------------------"
            print '合并size[%d,%d]' % (r_size_lt[i],r_size_lt[i+1])
            region_md5_a=region_name_list[i].split('.')[1]
            region_md5_b=region_name_list[i+1].split('.')[1]
            print region_md5_a,region_md5_b
            try:
                print "merge_region '%s','%s'" % (region_md5_a,region_md5_b)
                cmd_step3="merge_region '%s','%s'" % (region_md5_a,region_md5_b)
                cmd_step4='echo'+' '+'"'+cmd_step3+'"'+'|'+'/service/hbase2/bin/hbase shell'
                stat1,rt1=commands.getstatusoutput(cmd_step4)
                time.sleep(10)
                print "跳过下一个元素"
                print (r_size_lt[next(lst)])
                msg="合并region '%s','%s'完成---有零存在" % (region_md5_a,region_md5_b)
                logger.info(msg)
            except Exception as e:
                msg="合并region %s %s异常" % (region_md5_a,region_md5_b)
                logger.error(msg)
        elif r_size_lt[i]+r_size_lt[i+1]<r_sum_size or not all(map(lambda x:x>r_min_size,[r_size_lt[i],r_size_lt[i+1]])):
            print ""
            print "--------------------------------------------------------------"
            print '合并size[%d,%d]' % (r_size_lt[i],r_size_lt[i+1])
            create_time_a=region_name_list[i].split('.')[0][:10]
            region_md5_a=region_name_list[i].split('.')[1]
            create_time_b=region_name_list[i+1].split('.')[0][:10]
            region_md5_b=region_name_list[i+1].split('.')[1]
            print create_time_a,region_md5_a
            print create_time_b,region_md5_b
            current_time=int(time.time())
            time_chazhi_a=current_time-int(create_time_a)
            time_chazhi_b=current_time-int(create_time_b)
            print '以上两个region的时间戳与当前时间的差值单位秒:%d,%d' % (time_chazhi_a,time_chazhi_b)
            if time_chazhi_a>3600*t_itl and time_chazhi_b>3600*t_itl:
                try:
                     print "merge_region '%s','%s'" % (region_md5_a,region_md5_b)
                     cmd_step3="merge_region '%s','%s'" % (region_md5_a,region_md5_b)
                     cmd_step4='echo'+' '+'"'+cmd_step3+'"'+'|'+'/service/hbase2/bin/hbase shell'
                     stat1,rt1=commands.getstatusoutput(cmd_step4)
                     time.sleep(10)
                     print "跳过下一个元素"
                     print (r_size_lt[next(lst)])
                     msg="merge_region '%s','%s' 完成--非零" % (region_md5_a,region_md5_b)
                     logger.info(msg)
                except Exception as e:
                     msg="merge_region '%s','%s' 异常" % (region_md5_a,region_md5_b)
                     logger.error(msg)
            else:
                print "region的创建时间距当前时间太近不符合合并条件,不做合并操作"
            print "--------------------------------------------------------------"
        else:
            print 'size[%d,%d]不在合并条件内，跳过' % (r_size_lt[i],r_size_lt[i+1])
            continue

def main():
    print args
    print 'sum_region',args.sum
    r_sum_size=args.sum
    print 'minsize=', args.min_size
    r_min_size=args.min_size
    print 'tablename=', args.table_name
    tb_name=args.table_name
    print 'time_interval=', args.time_interval
    t_itl=args.time_interval
    paser_file(scriptpath)
    r_size_lt=map(lambda x:int(x),region_size_list)
    merge_fun(r_size_lt,r_sum_size,r_min_size,t_itl)

if __name__ == '__main__':
    scriptpath=os.path.dirname(os.path.realpath(__file__))
    help_desc='''
    示例：python region_merge_test_v2.py -n ias_scheduler -s 1000 -m 100 -t 3

    如果不传递参数将默认对ias_scheduler进行操作

'''
    region_name_list=[]
    region_size_list=[]
    args=None
    args = parse_args()
    generate_file()
    main()





