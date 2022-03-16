import numpy as np
from scipy import interpolate
import xlrd
def computeSRF(startB,endB,FullSRF):
    u = np.arange(400,400+len(FullSRF),1)
    f = interpolate.interp1d(u,np.array(FullSRF),'linear')
    m = np.arange(startB,endB+2.5,2.5)
    return f(m)

def writeJson():
    
    pass
    
            # '1':[0.45,0.52],
            # '2':[0.52,0.59],
            # '3':[0.63,0.69],
            # '4':[0.77,0.89],
            # '5':[0.45,0.90],
    
    
def main():
    _startB = 450 #
    _endB = 520 #
    _startB = 520 #
    _endB = 590 #
    _startB = 630 #
    _endB = 690 #  
    _startB = 770 #
    _endB = 890 # 
    _startB = 450 #
    _endB = 900 #       
    # _startB = 3500 #
    # _endB = 4000 #     
    wb =xlrd.open_workbook(r'./SRF/GF6SRF.xlsx')
    sh = wb.sheet_by_name('PMS')
    _FullSRF = sh.col_values(1,2)
    # print(_FullSRF)
    result = computeSRF(_startB,_endB,_FullSRF)
    for i in result:
        print("%.6f "%i +',')
    
if __name__ == "__main__":
    main()
    
    