from GFPCore import GFPCore1
import json

def main():
    xpath = r'E:\GFDATA1\test\GF1_PMS1_E99.0_N30.0_20200103_L1A0004523152\GF1_PMS1_E99.0_N30.0_20200103_L1A0004523152-MSS1.tiff'
    gfobj = GFPCore1(xpath)
    outpath =r'E:\GFDATA1\test\ceshi\gf1ceshi1.tif'
    satparamspath = r'./satparams.json'
    with open(satparamspath,'r') as f:
        SATPARAMS = json.load(f) 
    gfobj.geoCorrection(outpath)

if __name__ == "__main__":
    main()
