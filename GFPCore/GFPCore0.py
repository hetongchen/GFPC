
from abc import ABC
from abc import abstractmethod


class GFPCore(ABC):
    
    @staticmethod
    def parse_rpc_file(rpc_file):
    # rpc_file:.rpc文件的绝对路径
    # rpc_dict：符号RPC域下的16个关键字的字典
    # 参考网址：http://geotiff.maptools.org/rpc_prop.html；
    # https://www.osgeo.cn/gdal/development/rfc/rfc22_rpc.html

        rpc_dict = {}
        with open(rpc_file) as f:
            text = f.read()

        # .rpc文件中的RPC关键词
        words = ['errBias', 'errRand', 'lineOffset', 'sampOffset', 'latOffset',
                'longOffset', 'heightOffset', 'lineScale', 'sampScale', 'latScale',
                'longScale', 'heightScale', 'lineNumCoef', 'lineDenCoef','sampNumCoef', 'sampDenCoef',]

        # GDAL库对应的RPC关键词
        keys = ['ERR_BIAS', 'ERR_RAND', 'LINE_OFF', 'SAMP_OFF', 'LAT_OFF', 'LONG_OFF',
                'HEIGHT_OFF', 'LINE_SCALE', 'SAMP_SCALE', 'LAT_SCALE',
                'LONG_SCALE', 'HEIGHT_SCALE', 'LINE_NUM_COEFF', 'LINE_DEN_COEFF',
                'SAMP_NUM_COEFF', 'SAMP_DEN_COEFF']

        for old, new in zip(words, keys):
            text = text.replace(old, new)
        # 以‘;\n’作为分隔符
        text_list = text.split(';\n')
        # 删掉无用的行
        text_list = text_list[3:-2]
        #
        text_list[0] = text_list[0].split('\n')[1]
        # 去掉制表符、换行符、空格
        text_list = [item.strip('\t').replace('\n', '').replace(' ', '') for item in text_list]

        for item in text_list:
            # 去掉‘=’
            key, value = item.split('=')
            # 去掉多余的括号‘(’，‘)’
            if '(' in value:
                value = value.replace('(', '').replace(')', '')
            rpc_dict[key] = value
        for key in keys[:12]:
            # 为正数添加符号‘+’
            if not rpc_dict[key].startswith('-'):
                rpc_dict[key] = '+' + rpc_dict[key]
            # 为归一化项和误差标志添加单位
            if key in ['LAT_OFF', 'LONG_OFF', 'LAT_SCALE', 'LONG_SCALE']:
                rpc_dict[key] = rpc_dict[key] + ' degrees'
            if key in ['LINE_OFF', 'SAMP_OFF', 'LINE_SCALE', 'SAMP_SCALE']:
                rpc_dict[key] = rpc_dict[key] + ' pixels'
            if key in ['ERR_BIAS', 'ERR_RAND', 'HEIGHT_OFF', 'HEIGHT_SCALE']:
                rpc_dict[key] = rpc_dict[key] + ' meters'

        # 处理有理函数项
        for key in keys[-4:]:
            values = []
            for item in rpc_dict[key].split(','):
                #print(item)
                if not item.startswith('-'):
                    values.append('+'+item)
                else:
                    values.append(item)
                rpc_dict[key] = ' '.join(values)
        return rpc_dict    
    
    @abstractmethod
    def acquireGainBais():
        """
        获取定标参数
        """
    @abstractmethod
    def radiometricCalibration(self,*args, **kwargs):
        """
        辐射定标
        """
        
    @abstractmethod
    def atmospheriCorrection(self,*args, **kwargs):
        """
        大气校正
        """
    
    @abstractmethod    
    def geoCorrection(self,*args, **kwargs):
        """
        几何校正
        """
    
    @abstractmethod
    def atmgeoCorrection(self,*args, **kwargs):
        """
        大气校正和几何校正
        """
    