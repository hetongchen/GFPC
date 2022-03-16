# -*- coding:utf-8 -*-
import argparse
import json
from configparser import ConfigParser
import os
from glob import glob,iglob
from multiprocessing import Pool
import time
from GFScheduler import SingleScheduler
from utils import global_var
import threading


def main():
    # 配置文件读取

    ini_file = r'./config.ini'
    cfg = ConfigParser()
    cfg.read(ini_file,encoding='utf-8')
    satparams = cfg.get('rad_cal_coef','satparamspath')
    with open(satparams,'r') as f:
        SATPARAMS = json.load(f)       

    
    #  命令行解译
    parser = argparse.ArgumentParser(description="GF satellite batch process.")
    parser.add_argument('-I','--Input_dir',type=str,help='Input dir of the GF zip.gz.',default=cfg.get('personal','Input_dir'))
    parser.add_argument('-O','--Output_dir',type=str,help='Output dir of the process image file.',default=cfg.get('personal','Output_dir'))
    parser.add_argument('-r','--isdeleteUnzip',type=bool,help='Is delete unzip file?',default=eval(cfg.get('personal','isdeleteUnzip')))
    parser.add_argument('-p','--isAtmosCorrPan',type=bool,help='Is pan image need atmosphere corr?',default= eval(cfg.get('personal','isAtmosCorrPan')))
    parser.add_argument('-A','--isatcmode',type=bool,help='atc file?',default=eval(cfg.get('personal','isatcmode')))
    parser.add_argument('-g','--isgeocmode',type=bool,help='geo file?',default=eval(cfg.get('personal','isgeocmode')))
    parser.add_argument('-a','--isatcgeocmode',type=bool,help='atc and geo file?',default=eval(cfg.get('personal','isatcgeocmode')))
    parser.add_argument('-c','--core_number',type=int,help='multprocess use the number of the cpu',default=cfg.get('personal','core_number'))
    # parser.add_argument('-d','--meanDEM',type=int,help='An average elevation of study Area. ',default=cfg.get('personal','meanDEM'))
    parser.add_argument('-D','--isDEMDownload',type=bool,help='Is auto Download DEM file for corr?',default=eval(cfg.get('personal','isDEMDownload')))    
    args = parser.parse_args()
    print('Input Dir is: ',cfg.get('personal','Input_dir'),'>>>')
    
    
    global_var._init()
    global_var.set_value('Input_dir',args.Input_dir)
    global_var.set_value('Output_dir',args.Output_dir)
    # global_var.set_value('meanDEM',args.meanDEM)
    global_var.set_value('isdeleteUnZip',args.isdeleteUnzip)
    global_var.set_value('isAtmosCorrPan',args.isAtmosCorrPan)
    global_var.set_value('isatcmode',args.isatcmode)
    global_var.set_value('isgeocmode',args.isgeocmode)
    global_var.set_value('isatcgeocmode',args.isatcgeocmode)
    global_var.set_value('isDEMDownload',args.isDEMDownload)
    global_var.set_value('core_number',args.core_number)  
    
    # gz文件提取
    if  not os.path.isdir(args.Input_dir):
        print("Input_dir is not a usable dir.\n")
        return -1
    if  not os.path.isdir(args.Output_dir):
        os.makedirs(args.Output_dir)
        print("Output_dir is created successful.\n")
    print('Output Dir is: ',cfg.get('personal','Output_dir'),'>>>')
    # primaryFilelist = os.listdir(args.Input_dir)
    primaryFilelist = iglob(os.path.join(args.Input_dir,"GF*L1*[1-9]"))
    gzFilelist = glob(os.path.join(args.Input_dir,"GF*L1*.gz"))
    for item in primaryFilelist:
        if os.path.isdir(item):
            gzpath = glob(os.path.join(args.Input_dir,item,"GF*L1*.gz"))
            if len(gzpath)==1:
                gzFilelist.append(gzpath[0])
            else:
                continue
        else:
            continue
    
    
    a = time.time()
    if global_var.get_value("core_number") == 1:
    # 单进程
        for gzitem in gzFilelist:
            SingleScheduler(gzitem,SATPARAMS)
    elif global_var.get_value("core_number") >1:
    # 多进程    
        processPool = Pool(args.core_number)
        for gzitem in gzFilelist:
            processPool.apply_async(SingleScheduler,args=(gzitem,args.Output_dir,SATPARAMS,False,global_var._global_dict))
        print('Waiting for all subprocesses done...')    
        processPool.close()
        processPool.join()
    # 多线程
    elif global_var.get_value("multProcessCore") <0:
        sem = threading.Semaphore(abs(args.core_number))
        def multThread(func):
            def wrapper(*args, **kwargs):
                sem.acquire()
                func(*args, **kwargs)
                sem.release()
            return wrapper
        
        @multThread
        def multSingleScheduler(gzpath,atcfilepath,satparams):
            SingleScheduler(gzpath,atcfilepath,satparams)
        
        thread_list = []
        for gzitem in gzFilelist:
            t = threading.Thread(target=multSingleScheduler,args=(gzitem,args.Output_dir,SATPARAMS))
            thread_list.append(t)
        for t in thread_list:
            t.start()      
        for t in thread_list:
            t.join()
            
            
            
    b=time.time()
    print("consume time:",b-a)
 
 
#  1、线程的创建开销小、由于GIL的存在，无法真正并行，适合GUI、网络通信、文件读写等IO密集型场景；
# 2、进程的创建开销大，可以充分利用多个CPU实现并行，适合计算量比较大（比如单个函数执行需要几分钟、几十分钟以上），且无需IO（简单地说就是数据已经在内存中，不需要读取磁盘、不需要网络通信）的场景。
# 3、多线程、多进程都不适合的场景：基本不涉及IO或只读取一次文件这种，且计算量不大，单线程短时间就能结束（一两秒左右）的情况下，单进程单线程是最好的。   
    
if __name__ == "__main__":
    main()

