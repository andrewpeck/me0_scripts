from rw_reg_lpgbt import *
from time import *
import argparse
import cx_Oracle
import pandas as pd
import os

geb_asiago_vfat_map = { # wide mapping not yet implemented in the firmware - update
    "narrow": {"0": [0, 1, 8, 9, 16, 17], "1": [2, 3, 10, 11, 18, 19]},
    "wide":   {"0": [0, 1, 8, 9, 16, 17], "1": [2, 3, 10, 11, 18, 19]}
}   

def getVfatList(inFile): # parse input file
    with open(inFile) as file:
        vfatList = file.readlines()
        vfatList = [line.rstrip('\n') for line in vfatList] 
        vfatList = [int(x) for x in vfatList] 
    
    return vfatList

def checkEnvVars(): # check if environment variables set for DB access
    try:
        name = os.environ["GEM_ONLINE_DB_NAME"]
        conn = os.environ["GEM_ONLINE_DB_CONN"]
    except KeyError:
        print("Please set the following environment variables:\n GEM_ONLINE_DB_NAME\nGEM_ONLINE_DB_CONN")
        sys.exit()

    return name, conn

def main(geb, asiago, inFile, write):

    serialN  = {}
    vfat_oh_link_reset()
    sleep(0.1)


    for vfat in geb_asiago_vfat_map[geb][asiago]:
        register = get_rwreg_node("GEM_AMC.OH.OH0.GEB.VFAT%d.HW_CHIP_ID" % vfat)
        serialN[vfat] = simple_read_backend_reg(register, -9999)
        #print(data_read)
    	#serialN[vfat] = read_reg('GEM_AMC.OH.OH0.GEB.VFAT%s.HW_CHIP_ID' % vfat)
    print("=" * 31)
    print("====== VFAT Chip Numbers ======")
    print("=" * 31)
    print("VFAT\t|\t Chip Number")
    print("-" * 31)
    for vfat in geb_asiago_vfat_map[geb][asiago]:
        if serialN[vfat] == -9999:
            print(Colors.RED + "%s" % vfat + Colors.ENDC + "\t|\t" + Colors.RED + "Link bad" + Colors.ENDC)
        else:
            print(Colors.GREEN + "%s" % vfat + Colors.ENDC + "\t|\t" + Colors.GREEN + "%s" % hex(serialN[vfat]) + Colors.ENDC)
    print("-" * 31)
    
    #if write:
    #    vfatFile = open("vfatDict.txt", "w")
    #    vfatInfo = str(serialN)
    #    vfatFile.write(vfatInfo)
    #    vfatFile.close()

    #serialN = {key:val for key, val in serialN.items() if val != -9999} # remove vfats with no serial number 
    
    name, conn = checkEnvVars() # get environment variables
    db = cx_Oracle.connect(conn + name) # connect to the database

    vfatQueryString0 = ('SELECT data.* FROM CMS_GEM_MUON_VIEW.GEM_VFAT3_PROD_SUMMARY_V_RH data '
            'INNER JOIN (SELECT vfat3_barcode, MAX(run_number) AS run_number FROM CMS_GEM_MUON_VIEW.GEM_VFAT3_PROD_SUMMARY_V_RH GROUP BY vfat3_barcode) data_select '
            'ON data.vfat3_barcode = data_select.vfat3_barcode AND data.run_number = data_select.run_number') # form query

    vfatQueryString1 = " AND ("
    vfatList = getVfatList(inFile) # get list of vfats from input file
    
    for idx, serialNum in enumerate(vfatList): # format query with vfat chip IDs
        if idx == 0:
            vfatQueryString1 += " data.VFAT3_SER_NUM='0x{:x}'".format(serialNum)
        else:
            vfatQueryString1 += " OR data.VFAT3_SER_NUM='0x{:x}'".format(serialNum)
            pass
        pass

    vfatQueryString1 += " )\n"
    vfatQueryString0 += vfatQueryString1 # add chip IDs to main query
    
    vfatCalInfo = pd.read_sql(vfatQueryString0, db) # read database info
    vfatCalInfo.columns = [str.lower(col) for col in vfatCalInfo.columns] # set column names to lowercase

    pd.set_option('display.max_columns', 500) # show 500 columns
    vfatCalInfo.info() # display dataframe variables, data types, etc.
    print(vfatCalInfo) 
    
    if write: # write data to output files
        vfatCalInfo["vfat3_ser_num"] = vfatCalInfo["vfat3_ser_num"].transform(lambda x: int(x, 0)) # convert hex serial number into decimal
        calDataDir = "vfat_cal_data"
        try:
            os.makedirs(calDataDir) # create directory for calibration datas
        except FileExistsError: # skip if directory already exists
            pass
        
        calInfoFile = calDataDir + "/vfat_cal_info_vref.txt" 
        vfatCalInfo.to_csv(calInfoFile, sep = ";", columns = ["vfat3_ser_num", "vref_adc"], index = False)

        calInfoFile = calDataDir + "/vfat_cal_info_iref.txt"
        vfatCalInfo.to_csv(calInfoFile, sep = ";", columns = ["vfat3_ser_num", "iref"], index = False)
        
        calInfoFile = calDataDir + "/vfat_cal_info_adc0.txt"
        vfatCalInfo.to_csv(calInfoFile, sep = ";", columns = ["vfat3_ser_num", "adc0m", "adc0b"], index = False)

        calInfoFile = calDataDir + "/vfat_cal_info_calDac.txt"
        vfatCalInfo.to_csv(calInfoFile, sep = ";", columns = ["vfat3_ser_num", "cal_dacm", "cal_dacb"], index = False)
        #fileName = calDataDir + "/NominalValues_IREF.txt" 
        #vfatCalInfo.to_csv(
        #        path_or_buf=fileName,
        #        sep=";",
        #        columns=['vfatN','iref'],
        #        header=False,
        #        index=False,
        #        mode='w')
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Retrieve VFAT calibration info from database.')
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle or dryrun (only backend currently supported)")
    parser.add_argument("-l", "--layer", action="store", dest="layer", default = "0", help="ME0 layer (only layer 0 currently supported)")
    parser.add_argument("-g", "--geb", action="store", dest="geb", help="geb = [wide, narrow]")
    parser.add_argument("-a", "--asiago", action="store", dest="asiago", help="ASIAGO number = [0, 1]")
    parser.add_argument("-w", "--write", action="store_true", dest="write", help="write chip serial numbers to file")    
    parser.add_argument("-i", "--inFile", action="store", dest="inFile", help="list of VFAT serial numbers")
    args = parser.parse_args()
    
    parseXML()
    rw_initialize(args.system)

    try: 
        main(args.geb, args.asiago, args.inFile, args.write)
    except KeyboardInterrupt:
        print(Colors.YELLOW + "\nKeyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    
    rw_terminate()
