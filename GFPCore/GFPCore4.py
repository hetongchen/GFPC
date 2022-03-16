from GFPCore import GFPCore
import os
from osgeo import gdal
from Py6S import *
class GFPCore4(GFPCore):

    def __init__(self,tifPath) -> None:
        '''
        自动从影像路径获取信息，不能修改原始文件名称
        '''
        # 定义对象所需
        self._tifpath = tifPath
        self._filename = os.path.basename(tifPath)
        self._gftype =  self._filename.split('_')[0]
        self._sensortype =  self._filename.split('_')[1]
        self._year =  self._filename.split('_')[4][:4]
        self._xmlpath = os.path.join(os.path.dirname(self._tifpath),
                 self._filename.replace('tiff', 'xml'))
        self._rpbpath = os.path.join(os.path.dirname(self._tifpath),
                 self._filename.replace('tiff', 'rpb'))
        
        self.xmlParse()
        
        self.__BandRange = {
            '2':[0.45,0.52],
            '3':[0.52,0.59],
            '4':[0.63,0.69],
            '5':[0.77,0.89],
            '1':[0.45,0.90],
        }
        self._bandIntegrTime = self.XML_IntegrationTime.split(',')
        
    def xmlParse(self):
        import xml.etree.cElementTree as ET 
        tree = ET.parse(self._xmlpath)
        root = tree.getroot()
        self.XML_SatelliteID =  root.find("SatelliteID").text
        self.XML_SensorID =  root.find("SensorID").text
        self.XML_Bands =  root.find("Bands").text
        self.XML_CenterTime =  root.find("CenterTime").text
        self.XML_ImageGSD =  root.find("ImageGSD").text
        self.XML_WidthInPixels =  root.find("WidthInPixels").text
        self.XML_HeightInPixels =  root.find("HeightInPixels").text
        self.XML_SolarAzimuth =  root.find("SolarAzimuth").text
        self.XML_SolarZenith =  root.find("SolarZenith").text
        self.XML_SatelliteAzimuth =  root.find("SatelliteAzimuth").text
        self.XML_SatelliteZenith =  root.find("SatelliteZenith").text
        self.XML_IntegrationLevel =  root.find("IntegrationLevel").text
        self.XML_IntegrationTime =  root.find("IntegrationTime").text
        self.XML_TopLeftLatitude =  root.find("TopLeftLatitude").text
        self.XML_TopLeftLongitude =  root.find("TopLeftLongitude").text
        self.XML_TopRightLatitude =  root.find("TopRightLatitude").text
        self.XML_TopRightLongitude =  root.find("TopRightLongitude").text
        self.XML_BottomRightLatitude =  root.find("BottomRightLatitude").text
        self.XML_BottomRightLongitude =  root.find("BottomRightLongitude").text
        self.XML_BottomLeftLatitude =  root.find("BottomLeftLatitude").text
        self.XML_BottomLeftLongitude =  root.find("BottomLeftLongitude").text
         
    @staticmethod
    def acquireGainBais(sensorType,year,bId,intergTime,satparams):
        """获取定标参数

        Args:
            sensorType (str): PMS1 PMS2 etc. sensor type
            year (int): 2022,2021
            bId (int): 1 2 3 4 5; 5 is pan
            satparams (dict): sat params dict
        """
        if sensorType == 'PMS':
            _Gain = satparams["Parameter"]['GF4'][sensorType][year][str(bId)][intergTime][0]
            _Bias = satparams["Parameter"]['GF4'][sensorType][year][str(bId)][intergTime][1]
        elif sensorType == "IRS":
            _Gain = satparams["Parameter"]['GF4'][sensorType][year][str(bId)][intergTime][0]
            _Bias = satparams["Parameter"]['GF4'][sensorType][year][str(bId)][intergTime][1]
        return _Gain,_Bias
    
    def radiometricCalibration(self,outPath,satparams,*args, **kwargs):
        
        import numpy as np
        import math
        from tqdm import tqdm
        # import time
        _IDataSet =  gdal.Open(self._tifpath)
        _Driver = _IDataSet.GetDriver()
        _cols = _IDataSet.RasterXSize
        _rows = _IDataSet.RasterYSize        
        _nbands =  _IDataSet.RasterCount
        # len(self.XML_Bands.split(','))
        # outDataset = _Driver.CreateCopy()
        outDataset = _Driver.Create(outPath,_cols,_rows,_nbands,gdal.GDT_Int32)
        nBlockSize = 2048
        #进度条参数
        XBlockcount = math.ceil(_cols/nBlockSize)
        YBlockcount = math.ceil(_rows/nBlockSize)
        
        # if _nbands==1:
        #     # 情况很多，分类讨论
        #     bId = eval(self.XML_Bands)
        #     _Gain,_Bias = self.acquireGainBais(self._sensortype,self._year,bId,satparams)
        #     ReadBand = _IDataSet.GetRasterBand(1)
        #     outband = outDataset.GetRasterBand(1)  
        #     outband.SetNoDataValue(-9999)    
                       
        # else:
        # 多波段影像    
        for m in range(1,_nbands+1):  
            ReadBand = _IDataSet.GetRasterBand(m)
            outband = outDataset.GetRasterBand(m)  
            outband.SetNoDataValue(-9999)
            bId = eval(self.XML_Bands.split(',')[m-1])
            i = 0
            j = 0
            _Gain,_Bias = self.acquireGainBais(self._sensortype,self._year,bId,self._bandIntegrTime[m-1],satparams)
            # SRF = satparams["SRF"][self._gftype][self._cameratype][str(m)]
            # AtcCofa, AtcCofb, AtcCofc = self._6sradcorr(self.__BandRange[str(m)][0],self.__BandRange[str(m)][1],SRF
            try:
                with tqdm(total=XBlockcount*YBlockcount,iterable='iterable',desc = 'band %i of %s'%(m,self._filename),ncols=150) as pbar:
                # with tqdm(total=XBlockcount*YBlockcount) as pbar:
                    while i<_rows:
                        while j <_cols:
                            #保存分块大小
                            nXBK = nBlockSize
                            nYBK = nBlockSize

                            #最后不够分块的区域，有多少读取多少
                            if i+nBlockSize>_rows:
                                nYBK = _rows - i
                            if j+nBlockSize>_cols:
                                nXBK=_cols - j

                            #分块读取影像
                            Image = ReadBand.ReadAsArray(j,i,nXBK,nYBK)
                            outImage =np.where(Image>0,Image*_Gain + _Bias,-9999)
                            # y = np.where(outImage!=-9999,AtcCofa * outImage - AtcCofb,-9999)
                            # atcImage = np.where(y!=-9999,(y / (1 + y * AtcCofc))*10000,-9999)
                            outband.WriteArray(outImage,j,i)
                            j=j+nXBK
                            # time.sleep(0.1)
                            pbar.update(1)
                        j=0
                        i=i+nYBK
            except KeyboardInterrupt:
                pbar.close()
                raise
            pbar.close()
            
        outDataset.FlushCache()
        del _IDataSet,outDataset            
    
    def acquire6sparams(self,startband,endband,SRF):
        
        s = SixS()
        # 传感器类型 自定义
        s.geometry = Geometry.User()
        s.geometry.solar_z = 90-eval(self.XML_SolarZenith)
        s.geometry.solar_a = eval(self.XML_SolarAzimuth)
        # s.geometry.view_z = float(dom.getElementsByTagName('SatelliteZenith')[0].firstChild.data)
        # s.geometry.view_a = float(dom.getElementsByTagName('SatelliteAzimuth')[0].firstChild.data)
        s.geometry.view_z = 0
        s.geometry.view_a = 0
        
        # 日期
        DateTimeparm = self.XML_CenterTime
        DateTime = DateTimeparm.split(' ')
        Date = DateTime[0].split('-')
        s.geometry.month = int(Date[1])
        s.geometry.day = int(Date[2])
        
        # 中心经纬度 计算大气模式
        ImageCenterLat = eval(self.XML_TopLeftLatitude)+eval(self.XML_TopRightLatitude) +\
        eval(self.XML_BottomLeftLatitude) + eval(self.XML_BottomRightLatitude)
        
        if ImageCenterLat > -15 and ImageCenterLat < 15:
            s.atmos_profile = AtmosProfile.PredefinedType(AtmosProfile.Tropical)

        if ImageCenterLat > 15 and ImageCenterLat < 45:
            if s.geometry.month > 4 and s.geometry.month < 9:
                s.atmos_profile = AtmosProfile.PredefinedType(AtmosProfile.MidlatitudeSummer)
            else:
                s.atmos_profile = AtmosProfile.PredefinedType(AtmosProfile.MidlatitudeWinter)

        if ImageCenterLat > 45 and ImageCenterLat < 60:
            if s.geometry.month > 4 and s.geometry.month < 9:
                s.atmos_profile = AtmosProfile.PredefinedType(AtmosProfile.SubarcticSummer)
            else:
                s.atmos_profile = AtmosProfile.PredefinedType(AtmosProfile.SubarcticWinter)


        # 气溶胶类型大陆
        s.aero_profile = AtmosProfile.PredefinedType(AeroProfile.Continental)
        # 下垫面类型
        s.ground_reflectance = GroundReflectance.HomogeneousLambertian(0.36)
        # 550nm气溶胶光学厚度,对应能见度为40km
        s.aot550 = 0.14497        
        # 通过研究区的范围去求DEM高度
        meanDEM = 1000
        # 研究区海拔、卫星传感器轨道高度
        s.altitudes = Altitudes()
        s.altitudes.set_target_custom_altitude(meanDEM)
        s.altitudes.set_sensor_satellite_level()        
        
        # 校正波段（根据波段名称）
        s.wavelength = Wavelength(startband,endband,SRF)
        
        s.atmos_corr = AtmosCorr.AtmosCorrLambertianFromReflectance(-0.1)
        # 运行6s大气模型
        s.run()
        from numpy import isnan
        
        xa = s.outputs.coef_xa if not isnan(s.outputs.coef_xa) else 0
        xb = s.outputs.coef_xb if not isnan(s.outputs.coef_xb) else 0
        xc = s.outputs.coef_xc if not isnan(s.outputs.coef_xc) else 0
        # x = s.outputs.values  if s.outputs.coef_xa is not None else 0
        return (xa, xb, xc)
    
    def atmospheriCorrection(self,outPath,satparams,*args, **kwargs):
        """
        大气校正
        """
        import numpy as np
        import math
        from tqdm import tqdm
        # import time
        _IDataSet =  gdal.Open(self._tifpath)
        _Driver = _IDataSet.GetDriver()
        _cols = _IDataSet.RasterXSize
        _rows = _IDataSet.RasterYSize        
        _nbands =  _IDataSet.RasterCount
        # len(self.XML_Bands.split(','))
        # outDataset = _Driver.CreateCopy()
        outDataset = _Driver.Create(outPath,_cols,_rows,_nbands,gdal.GDT_Int32)
        nBlockSize = 2048
        #进度条参数
        XBlockcount = math.ceil(_cols/nBlockSize)
        YBlockcount = math.ceil(_rows/nBlockSize)
        
        # if _nbands==1:
        #     # 情况很多，分类讨论
        #     bId = eval(self.XML_Bands)
        #     _Gain,_Bias = self.acquireGainBais(self._sensortype,self._year,bId,satparams)
        #     ReadBand = _IDataSet.GetRasterBand(1)
        #     outband = outDataset.GetRasterBand(1)  
        #     outband.SetNoDataValue(-9999)    
                       
        # else:
        # 多波段影像    
        for m in range(1,_nbands+1):  
            ReadBand = _IDataSet.GetRasterBand(m)
            outband = outDataset.GetRasterBand(m)  
            outband.SetNoDataValue(-9999)
            bId = eval(self.XML_Bands.split(',')[m-1])
            i = 0
            j = 0
            _Gain,_Bias = self.acquireGainBais(self._sensortype,self._year,bId,self._bandIntegrTime[m-1],satparams)
            SRF = satparams["SRF"][self._gftype][self._sensortype][str(m)]
            if self._sensortype == 'IRS':
                AtcCofa, AtcCofb, AtcCofc = self.acquire6sparams(3.5,4.0,SRF)
            else:    
                AtcCofa, AtcCofb, AtcCofc = self.acquire6sparams(self.__BandRange[str(m)][0],self.__BandRange[str(m)][1],SRF)
            try:
                with tqdm(total=XBlockcount*YBlockcount,iterable='iterable',desc = 'band %i of %s'%(m,self._filename),ncols=150) as pbar:
                # with tqdm(total=XBlockcount*YBlockcount) as pbar:
                    while i<_rows:
                        while j <_cols:
                            #保存分块大小
                            nXBK = nBlockSize
                            nYBK = nBlockSize

                            #最后不够分块的区域，有多少读取多少
                            if i+nBlockSize>_rows:
                                nYBK = _rows - i
                            if j+nBlockSize>_cols:
                                nXBK=_cols - j

                            #分块读取影像
                            Image = ReadBand.ReadAsArray(j,i,nXBK,nYBK)
                            outImage =np.where(Image>0,Image*_Gain + _Bias,-9999)
                            y = np.where(outImage!=-9999,AtcCofa * outImage - AtcCofb,-9999)
                            atcImage = np.where(y!=-9999,(y / (1 + y * AtcCofc))*10000,-9999)
                            outband.WriteArray(atcImage,j,i)
                            j=j+nXBK
                            # time.sleep(0.1)
                            pbar.update(1)
                        j=0
                        i=i+nYBK
            except KeyboardInterrupt:
                pbar.close()
                raise
            pbar.close()
            
        outDataset.FlushCache()
        del _IDataSet,outDataset    

    def geoCorrection(self,outPath,dem_tif_file=None,*args, **kwargs):

        '''
        ## 设置rpc校正的参数
        # 原图像和输出影像缺失值设置为0，输出影像坐标系为WGS84(EPSG:4326), 重采样方法为双线性插值（bilinear，还有最邻近‘near’、三次卷积‘cubic’等可选)
        # 注意DEM的覆盖范围要比原影像的范围大，此外，DEM不能有缺失值，有缺失值会报错
        # 通常DEM在水域是没有值的（即缺失值的情况），因此需要将其填充设置为0，否则在RPC校正时会报错
        # 这里使用的DEM是填充0值后的SRTM V4.1 3秒弧度的DEM(分辨率为90m)
        # RPC_DEMINTERPOLATION=bilinear  表示对DEM重采样使用双线性插值算法
        # 如果要修改输出的坐标系，则要修改dstSRS参数值，使用该坐标系统的EPSG代码
        # 可以在网址https://spatialreference.org/ref/epsg/32650/  查询得到EPSG代码
        '''
        os.environ['PROJ_LIB'] = r'./proj'
        _dataset = gdal.Open(self._tifpath,gdal.GA_Update)    
        rpc_dict = self.parse_rpc_file(self._rpbpath)
        for k in rpc_dict.keys():
            _dataset.SetMetadataItem(k, rpc_dict[k], 'RPC')
        _dataset.FlushCache()
        del _dataset
        if dem_tif_file is None:
            wo = gdal.WarpOptions(srcNodata=-9999, dstNodata=-9999, dstSRS='EPSG:4326', resampleAlg='bilinear', 
                            format='Gtiff',rpc=True, warpOptions=["INIT_DEST=NO_DATA"])
            
            wr = gdal.Warp(outPath, self._tifpath, options=wo)
            print("RPC_GEOcorr(NO DEM)>>>")
        else:
            wo = gdal.WarpOptions(srcNodata=-9999, dstNodata=-9999, dstSRS='EPSG:4326', resampleAlg='bilinear', format='ENVI',rpc=True, warpOptions=["INIT_DEST=NO_DATA"],
                    transformerOptions=["RPC_DEM=%s"%(dem_tif_file), "RPC_DEMINTERPOLATION=bilinear"])     
            wr = gdal.Warp(outPath, self._tifpath, options=wo)   
            print("RPC_GEOcorr(YES DEM)>>>")        
        del wr
        
    def atmgeoCorrection(self,outPath,satparams,dem_tif_file=None,*args, **kwargs):
        """
        大气校正
        """
        _geo_tmp_path = os.path.join(os.path.dirname(outPath),'geo_tmp_file.tiff') 
        os.environ['PROJ_LIB'] = r'./proj'
        
        _geo_dataset = gdal.Open(self._tifpath,gdal.GA_Update)    
        rpc_dict = self.parse_rpc_file(self._rpbpath)
        for k in rpc_dict.keys():
            _geo_dataset.SetMetadataItem(k, rpc_dict[k], 'RPC')
        _geo_dataset.FlushCache()
        # del _atc_dataset
        if dem_tif_file is None:
            wo = gdal.WarpOptions(srcNodata=0, dstNodata=0, dstSRS='EPSG:4326', resampleAlg='bilinear', 
                            format='Gtiff',rpc=True, warpOptions=["INIT_DEST=NO_DATA"])
            
            wr = gdal.Warp(_geo_tmp_path, _geo_dataset, options=wo)
            print("RPC_GEOcorr(NO DEM)>>> ")
        else:
            wo = gdal.WarpOptions(srcNodata=0, dstNodata=0, dstSRS='EPSG:4326', resampleAlg='bilinear', format='ENVI',rpc=True, warpOptions=["INIT_DEST=NO_DATA"],
                    transformerOptions=["RPC_DEM=%s"%(dem_tif_file), "RPC_DEMINTERPOLATION=bilinear"])     
            wr = gdal.Warp(_geo_tmp_path, _geo_dataset, options=wo)   
            print("RPC_GEOcorr(YES DEM)>>> ")        
        del wr  

        import numpy as np
        import math
        from tqdm import tqdm
        # import time
        print("ATMcorr>>> ")

        _geo_dataset =  gdal.Open(_geo_tmp_path)
        _Driver = _geo_dataset.GetDriver()
        _cols = _geo_dataset.RasterXSize
        _rows = _geo_dataset.RasterYSize        
        _nbands =  _geo_dataset.RasterCount
        # len(self.XML_Bands.split(','))
        # outDataset = _Driver.CreateCopy()
        outDataset = _Driver.Create(outPath,_cols,_rows,_nbands,gdal.GDT_Int32)
        outDataset.SetGeoTransform(_geo_dataset.GetGeoTransform())
        outDataset.SetProjection(_geo_dataset.GetProjection())
        nBlockSize = 2048
        #进度条参数
        XBlockcount = math.ceil(_cols/nBlockSize)
        YBlockcount = math.ceil(_rows/nBlockSize)
        
        # if _nbands==1:
        #     # 情况很多，分类讨论
        #     bId = eval(self.XML_Bands)
        #     _Gain,_Bias = self.acquireGainBais(self._sensortype,self._year,bId,satparams)
        #     ReadBand = _IDataSet.GetRasterBand(1)
        #     outband = outDataset.GetRasterBand(1)  
        #     outband.SetNoDataValue(-9999)                   
        # else:\\
            
            
        # 多波段影像    
        for m in range(1,_nbands+1):  
            ReadBand = _geo_dataset.GetRasterBand(m)
            outband = outDataset.GetRasterBand(m)  
            outband.SetNoDataValue(-9999)
            bId = eval(self.XML_Bands.split(',')[m-1])
            i = 0
            j = 0
            _Gain,_Bias = self.acquireGainBais(self._sensortype,self._year,bId,self._bandIntegrTime[m-1],satparams)
            SRF = satparams["SRF"][self._gftype][self._sensortype][str(m)]
            if self._sensortype == 'IRS':
                AtcCofa, AtcCofb, AtcCofc = self.acquire6sparams(3.5,4.0,SRF)
            else:    
                AtcCofa, AtcCofb, AtcCofc = self.acquire6sparams(self.__BandRange[str(m)][0],self.__BandRange[str(m)][1],SRF)
            try:
                with tqdm(total=XBlockcount*YBlockcount,iterable='iterable',desc = 'band %i of %s'%(m,self._filename),ncols=150) as pbar:
                # with tqdm(total=XBlockcount*YBlockcount) as pbar:
                    while i<_rows:
                        while j <_cols:
                            #保存分块大小
                            nXBK = nBlockSize
                            nYBK = nBlockSize

                            #最后不够分块的区域，有多少读取多少
                            if i+nBlockSize>_rows:
                                nYBK = _rows - i
                            if j+nBlockSize>_cols:
                                nXBK=_cols - j

                            #分块读取影像
                            Image = ReadBand.ReadAsArray(j,i,nXBK,nYBK)
                            outImage =np.where(Image>0,Image*_Gain + _Bias,-9999)
                            y = np.where(outImage!=-9999,AtcCofa * outImage - AtcCofb,-9999)
                            atcImage = np.where(y!=-9999,(y / (1 + y * AtcCofc))*10000,-9999)
                            outband.WriteArray(atcImage,j,i)
                            j=j+nXBK
                            # time.sleep(0.1)
                            pbar.update(1)
                        j=0
                        i=i+nYBK
            except KeyboardInterrupt:
                pbar.close()
                raise
            pbar.close()    
        outDataset.FlushCache()
        del _geo_dataset,outDataset  
        self.__geo_tmp_path = _geo_tmp_path
       
    def __del__(self):
        try:
            os.remove(self.__geo_tmp_path)
        except:
            pass
        print('{} processing finished.'.format(self._filename))    
        
def main():
    from configparser import ConfigParser
    import json
    ini_file = r'./config.ini'
    cfg = ConfigParser()
    cfg.read(ini_file,encoding='utf-8')
    satparams = cfg.get('rad_cal_coef','satparamspath')
    with open(satparams,'r') as f:
        SATPARAMS = json.load(f)      
    # _tifpath = r'E:\GFDATA1\test\GF1_PMS1_E100.7_N29.7_20201028_L1A0005226696\GF1_PMS1_E100.7_N29.7_20201028_L1A0005226696-MSS1.tiff'
    _tifpath = r'E:\GFDATA1\test\GF4_PMI_E96.4_N35.8_20191224_L1A0000278199\GF4_IRS_E96.4_N35.8_20191224_L1A0000278199.tiff'
    # GFPCore.initDatabase(SATPARAMS)
    gfpc = GFPCore4(_tifpath)
    gfpc.atmospheriCorrection(r'E:\GFDATA1\test\ceshi\ceshi1.tif',SATPARAMS)
    gfpc.atmgeoCorrection(r'E:\GFDATA1\test\ceshi\ceshi2.tif',SATPARAMS)
    gfpc.geoCorrection(r'E:\GFDATA1\test\ceshi\ceshi3.tif')
    
    
if  __name__ == "__main__":
    main()