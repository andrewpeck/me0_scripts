from rw_reg_lpgbt import *
from time import *
import argparse
import cx_Oracle
import pandas as pd
import os
from collections import OrderedDict

def getVfatList(inFile): # parse input file
    vfatList = OrderedDict()
    with open(inFile) as file:
        vfatList_line = file.readlines()
        vfatList_line = [line.rstrip('\n') for line in vfatList_line]
        for x in vfatList_line:
            vfatList[x.split()[0]] = x.split()[1]
    return vfatList

def checkEnvVars(): # check if environment variables set for DB access
    try:
        name = os.environ["GEM_ONLINE_DB_NAME"]
        conn = os.environ["GEM_ONLINE_DB_CONN"]
    except KeyError:
        print("Please set the following environment variables:\n GEM_ONLINE_DB_NAME\nGEM_ONLINE_DB_CONN")
        sys.exit()
    return name, conn

def main(oh_select, type, write):

    serialN = OrderedDict()
    vfat_oh_link_reset()
    sleep(0.1)

    for vfat in range(0,24):
        register = get_rwreg_node("BEFE.GEM_AMC.OH.OH%d.GEB.VFAT%d.HW_CHIP_ID"%(oh_select, vfat))
        serialN[vfat] = simple_read_backend_reg(register, -9999)
    print("=" * 31)
    print("====== VFAT Chip Numbers ======")
    print("=" * 31)
    print("VFAT\t|\t Chip Number")
    print("-" * 31)
    for vfat in range(0,24):
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

    if type=="hw_id":
        vfatList = serialN
    elif type=="file":
        inFile = "vfat_data/ME0_OH%d_vfatID.txt"%(oh_select)
        if not os.path.isfile(inFile):
            print (Colors.YELLOW + "Missing vfatID file for OH %d"%(oh_select) + Colors.ENDC)
            sys.exit()
        vfatList = getVfatList(inFile) # get list of vfats from input file

    for vfat in vfatList: # format query with vfat chip IDs
        serialNum = vfatList[vfat]
        if serialNum == -9999:
            vfatList.pop(vfat)
            continue
        if vfat == 0:
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
        vfatCalInfo["vfat"] = vfatList # adding VFAT#

        calDataDir = "vfat_data/vfat_cal_data"
        try:
            os.makedirs(calDataDir) # create directory for calibration datas
        except FileExistsError: # skip if directory already exists
            pass
        
        calInfoFile = calDataDir + "/ME0_OH%d_vfat_cal_info_vref.txt"%(oh_select)
        vfatCalInfo.to_csv(calInfoFile, sep = ";", columns = ["vfat", "vfat3_ser_num", "vref_adc"], index = False)

        calInfoFile = calDataDir + "/ME0_OH%d_vfat_cal_info_iref.txt"%(oh_select)
        vfatCalInfo.to_csv(calInfoFile, sep = ";", columns = ["vfat", "vfat3_ser_num", "iref"], index = False)
        
        calInfoFile = calDataDir + "/ME0_OH%d_vfat_cal_info_adc0.txt"%(oh_select)
        vfatCalInfo.to_csv(calInfoFile, sep = ";", columns = ["vfat", "vfat3_ser_num", "adc0m", "adc0b"], index = False)

        calInfoFile = calDataDir + "/ME0_OH%d_vfat_cal_info_calDac.txt"%(oh_select)
        vfatCalInfo.to_csv(calInfoFile, sep = ";", columns = ["vfat", "vfat3_ser_num", "cal_dacm", "cal_dacb"], index = False)
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
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = backend or dryrun")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1 (only needed for backend)")
    parser.add_argument("-w", "--write", action="store_true", dest="write", help="write chip serial numbers to file")
    parser.add_argument("-t", "--type", action="store", dest="type", help="type = hw_id or file")
    #parser.add_argument("-i", "--inFile", action="store", dest="inFile", help="input file with list of VFAT serial numbers")
    args = parser.parse_args()

    if args.system == "chc":
        #print ("Using Rpi CHeeseCake for S-bit test")
        print (Colors.YELLOW + "Only Backend or dryrun supported" + Colors.ENDC)
        sys.exit()
    elif args.system == "backend":
        print ("Using Backend")
        #print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        #sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle")
        print (Colors.YELLOW + "Only Backend or dryrun supported" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually running vfat bert")
    else:
        print (Colors.YELLOW + "Only valid options: backend, dryrun" + Colors.ENDC)
        sys.exit()

    if args.ohid is None:
        print(Colors.YELLOW + "Need OHID" + Colors.ENDC)
        sys.exit()
    if int(args.ohid) > 1:
        print(Colors.YELLOW + "Only OHID 0-1 allowed" + Colors.ENDC)
        sys.exit()

    #if args.type not in ["hw_id", "file"]:
    if args.type != "file":
        print(Colors.YELLOW + "Input type can only file" + Colors.ENDC)
        #print(Colors.YELLOW + "Input type can only be hw_id or file" + Colors.ENDC)
        sys.exit()

    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML()
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system)
    print("Initialization Done\n")

    try: 
        main(int(args.ohid), args.type, args.write)
    except KeyboardInterrupt:
        print(Colors.YELLOW + "\nKeyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    
    rw_terminate()
