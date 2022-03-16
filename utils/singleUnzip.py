import os
import tarfile

# 解压缩原始文件
def untar(fname, dirs):
    # print("文件路径",fname)
    try:
        t = tarfile.open(fname)
    except Exception as e:
        print("文件%s打开失败" % fname)
    t.extractall(path=dirs)

'''
用于单个影像的解压
'''
def itemUnzip(gzpath):
    FileName = os.path.basename(gzpath)
    filename_split = FileName.split("_")    
    GFType = filename_split[0]
    CameraType = filename_split[1]
    InputFilePath = os.path.dirname(gzpath)
    ungzFileName = FileName[:-7]
    ungzFullName = os.path.join(InputFilePath,ungzFileName) 
    print("file "+FileName + " unziping>>>")
    try:
        untar(gzpath, ungzFullName)
    except Exception as e:
        print('解压出错!')
        return -1
    itemimfor = {}
    itemimfor['OrginPath'] = gzpath
    itemimfor['GFType'] = GFType
    itemimfor['CameraType'] = CameraType
    itemimfor['FileName'] = FileName
    itemimfor['UnZipPath'] = ungzFullName
    return itemimfor

    
        
if __name__ == '__main__':
    inpath = r'E:\GFDATA1\test\GF6_PMS_E98.6_N33.6_20200826_L1A1120056020.tar.gz'
    x = itemUnzip(inpath)
    print(x)
        
        