# -*- coding:utf-8 -*-
from utils.singleUnzip import itemUnzip
import os,shutil
from utils import global_var
import glob
    


def SingleScheduler(gzpath,satparams,*args, **kwargs):
    itemimfor = itemUnzip(gzpath)
    gzpath = itemimfor['OrginPath'] 
    GFType = itemimfor['GFType'] 
    CameraType = itemimfor['CameraType'] 
    FileName = itemimfor['FileName'] 
    ungzFullName = itemimfor['UnZipPath'] 
    
    # 多进程信息的传递
    if  len(args) !=0:
        global_var._init()
        for key,value in args[0].items():
            global_var.set_value(key,value)
      
    # 创建校正路径
    singleCorrDirname = FileName.replace("L1", "L2")[:-7]
    singleCorrFullpath = os.path.join(global_var.get_value("Output_dir"),singleCorrDirname)
    if not os.path.exists(singleCorrFullpath):
        os.mkdir(singleCorrFullpath)

    input_tif_list = glob.glob(os.path.join(ungzFullName,'*tif*'))
    if not global_var.get_value('isAtmosCorrPan'):
        for st in input_tif_list:
            bn = os.path.basename(st)
            if bn.find('PAN')!=-1:
                input_tif_list.remove(st)
        
    for input_tif_path in input_tif_list:
        print('{} atomscorring>>>\n'.format(singleCorrDirname))
        if   GFType == 'GF1':
            from GFPCore import GFPCore1
            gfprocessor =  GFPCore1(input_tif_path)
        elif GFType == 'GF2':
            from GFPCore import GFPCore2
            gfprocessor =GFPCore2(input_tif_path)        
        
        elif GFType == 'GF3':
            from GFPCore import GFPCore3
            gfprocessor =GFPCore3(input_tif_path)       
        
        elif GFType == 'GF4':
            from GFPCore import GFPCore4
            gfprocessor =GFPCore4(input_tif_path)   
        
        elif GFType == 'GF5':
            from GFPCore import GFPCore5
            gfprocessor =GFPCore5(input_tif_path)        
        
        elif GFType == 'GF6':
            from GFPCore import GFPCore6
            gfprocessor =GFPCore6(input_tif_path)
                    
        elif GFType == 'GF7':
            from GFPCore import GFPCore7
            gfprocessor =GFPCore7(input_tif_path)

        if global_var.get_value('isatcgeocmode'):
            output_tif_path =os.path.join(singleCorrFullpath,'atcgeo_'+os.path.basename(input_tif_path))
            gfprocessor.atmgeoCorrection(output_tif_path,satparams)
        if global_var.get_value('isatcmode'):
            output_tif_path =os.path.join(singleCorrFullpath,'atc_'+os.path.basename(input_tif_path))
            gfprocessor.atmospheriCorrection(output_tif_path,satparams)        
        if global_var.get_value('isgeocmode'):
            output_tif_path =os.path.join(singleCorrFullpath,'geo_'+os.path.basename(input_tif_path))
            gfprocessor.geoCorrection(output_tif_path)    
            
    if  global_var.get_value('isdeleteUnZip'):
        shutil.rmtree(ungzFullName)
        # os.removedirs(ungzFullName)





def main():
    inpathgf1 = r'E:\GFDATA1\GF1PMS2020年\GF1_PMS1_E97.3_N32.8_20200930_L1A0005098928\GF1_PMS1_E97.3_N32.8_20200930_L1A0005098928.tar.gz'
    from configparser import ConfigParser
    import json
    ini_file = r'./config.ini'
    cfg = ConfigParser()
    cfg.read(ini_file,encoding='utf-8')
    satparams = cfg.get('rad_cal_coef','satparamspath')  
    with open(satparams,'r') as f:
        SATPARAMS = json.load(f)       
    SingleScheduler(inpathgf1,SATPARAMS,r'E:\GFDATA1\test\GF1')


if __name__=='__main__':
    main()