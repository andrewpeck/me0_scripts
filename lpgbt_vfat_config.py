from rw_reg_lpgbt import *
from time import sleep, time
import sys
import argparse
import random
import glob

vfat_register_config = {}
vfat_calib_iref = {}
vfat_calib_vref = {}
vfat_register_dac_scan = {}

def initialize_vfat_config(oh_select, use_dac_scan_results):
    global vfat_register_config
    global vfat_calib_iref
    global vfat_calib_vref
    global vfat_register_dac_scan

    # Generic register list
    vfat_register_config_file_path = "vfat_data/ME0_OH%d_vfatConfig.txt"%oh_select
    if not os.path.isfile(vfat_register_config_file_path):
        print (Colors.YELLOW + "VFAT config text file not present in vfat_data/" + Colors.ENDC)
        sys.exit()
    vfat_register_config_file = open(vfat_register_config_file_path)
    for line in vfat_register_config_file.readlines():
        vfat_register_config[line.split()[0]] = int(line.split()[1])
    vfat_register_config_file.close()

    # IREF from calib
    vfat_calib_iref_path = "vfat_data/vfat_calib_data/ME0_OH%d_vfat_calib_info_iref.txt"%oh_select
    vfat_calib_vref_path = "vfat_data/vfat_calib_data/ME0_OH%d_vfat_calib_info_vref.txt"%oh_select
    if not os.path.isfile(vfat_calib_iref_path):
        print ("IREF calib file for VFATs not present, using default values")
    else:
        vfat_calib_iref_file = open(vfat_calib_iref_path)
        for line in vfat_calib_iref_file.readlines():
            if "vfat" in line:
                continue
            vfat_calib_iref[int(line.split(";")[0])] = int(line.split(";")[2])
        vfat_calib_iref_file.close()

    # VREF from calib
    if not os.path.isfile(vfat_calib_vref_path):
        print ("VREF calib file for VFATs not present, using default values")
    else:
        vfat_calib_vref_file = open(vfat_calib_vref_path)
        for line in vfat_calib_vref_file.readlines():
            if "vfat" in line:
                continue
            vfat_calib_vref[int(line.split(";")[0])] = int(line.split(";")[2])
        vfat_calib_vref_file.close()

    # DAC Scan Results
    if use_dac_scan_results:
        dac_scan_results_base_path = "vfat_data/vfat_dac_scan_results"
        if os.path.isdir(dac_scan_results_base_path):
            list_of_dirs = []
            for d in glob.glob(dac_scan_results_base_path+"/*"):
                if os.path.isdir(d):
                    list_of_dirs.append(d)
            if len(list_of_dirs)>0:
                latest_dir = max(list_of_dirs, key=os.path.getctime)
                dac_scan_results_path = latest_dir
                for f in glob.glob(dac_scan_results_path+"/nominalValues_ME0_OH%d_*.txt"%oh_select):
                    reg = f.split("nominalValues_ME0_OH%d_"%oh_select)[1].split(".txt")[0]
                    vfat_register_dac_scan[reg] = {}
                    file_in = open(f)
                    for line in file_in.readlines():
                        vfat = int(line.split(";")[1])
                        dac = int(line.split(";")[2])
                        vfat_register_dac_scan[reg][vfat] = dac
                    file_in.close()

def setVfatchannelTrim(vfatN, ohN, channel, trim_polarity, trim_amp):
    channel_trim_polarity_node = get_rwreg_node("BEFE.GEM_AMC.OH.OH%d.GEB.VFAT%d.VFAT_CHANNELS.CHANNEL%i.ARM_TRIM_POLARITY"%(ohN, vfatN, channel))
    channel_trim_amp_node = get_rwreg_node("BEFE.GEM_AMC.OH.OH%d.GEB.VFAT%d.VFAT_CHANNELS.CHANNEL%i.ARM_TRIM_AMPLITUDE"%(ohN, vfatN, channel))
    write_backend_reg(channel_trim_polarity_node, trim_polarity)
    write_backend_reg(channel_trim_amp_node, trim_amp)

def enableVfatchannel(vfatN, ohN, channel, mask, enable_cal):
    #channel_node = get_rwreg_node("BEFE.GEM_AMC.OH.OH%d.GEB.VFAT%d.VFAT_CHANNELS.CHANNEL%i"%(ohN, vfatN, channel))
    channel_enable_node = get_rwreg_node("BEFE.GEM_AMC.OH.OH%d.GEB.VFAT%d.VFAT_CHANNELS.CHANNEL%i.CALPULSE_ENABLE"%(ohN, vfatN, channel))
    channel_mask_node = get_rwreg_node("BEFE.GEM_AMC.OH.OH%d.GEB.VFAT%d.VFAT_CHANNELS.CHANNEL%i.MASK"%(ohN, vfatN, channel))
    if mask: # mask and disable calpulsing
        #write_backend_reg(channel_node, 0x4000)
        write_backend_reg(channel_enable_node, 0)
        write_backend_reg(channel_mask_node, 1)
    else:
        if enable_cal: # unmask and enable calpulsing
            #write_backend_reg(channel_node, 0x8000)
            write_backend_reg(channel_enable_node, 1)
            write_backend_reg(channel_mask_node, 0)
        else: # unmask but disable calpulsing
            #write_backend_reg(channel_node, 0x0000)
            write_backend_reg(channel_enable_node, 0)
            write_backend_reg(channel_mask_node, 0)

def configureVfat(configure, vfatN, ohN, low_thresh):

    for i in range(128):
        enableVfatchannel(vfatN, ohN, i, 0, 0) # unmask all channels and disable calpulsing

    if configure:
        #print ("Configuring VFAT")
        register_written = []

        if vfatN in vfat_calib_iref:
            write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%d.GEB.VFAT%d.CFG_IREF"     % (ohN, vfatN)), vfat_calib_iref[vfatN])
            register_written.append("CFG_IREF")
        if vfatN in vfat_calib_vref:
            write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%d.GEB.VFAT%d.CFG_VREF_ADC"     % (ohN, vfatN)), vfat_calib_vref[vfatN])
            register_written.append("CFG_VREF_ADC")
        for reg in vfat_register_dac_scan:
            if vfatN in vfat_register_dac_scan[reg]:
                write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%d.GEB.VFAT%d.%s"     % (ohN, vfatN, reg)), vfat_register_dac_scan[reg][vfatN])
                register_written.append(reg)
        for reg in vfat_register_config:
            if reg in register_written:
                continue
            write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%d.GEB.VFAT%d.%s"     % (ohN, vfatN, reg)), vfat_register_config[reg])
            register_written.append(reg)

        if low_thresh:
            #print ("Set low threshold")
            #write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_THR_ZCC_DAC"     % (ohN, vfatN)) , 0)
            write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%d.GEB.VFAT%d.CFG_THR_ARM_DAC"     % (ohN, vfatN)) , 0)

        write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%d.GEB.VFAT%d.CFG_RUN"%(ohN, vfatN)), 1)

    else:
        #print ("Unconfiguring VFAT")
        write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%d.GEB.VFAT%d.CFG_RUN"%(ohN, vfatN)), 0)


def lpgbt_vfat_config(system, oh_select, vfat_list, low_thresh, configure):
    print ("LPGBT VFAT Configuration\n")
    
    vfat_oh_link_reset()
    sleep(0.1)

    for vfat in vfat_list:
        lpgbt, gbt_select, elink, gpio = vfat_to_gbt_elink_gpio(vfat)
        check_lpgbt_link_ready(oh_select, gbt_select)
        if configure:
            print ("Configuring VFAT#: %02d" %(vfat))
        else:
            print ("Unconfiguring VFAT#: %02d" %(vfat))
        configureVfat(configure, vfat, oh_select, low_thresh)
        print ("")

    print ("\nVFAT configuration done\n")

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="LpGBT VFAT Configuration")
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = backend or dryrun")
    #parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1")
    #parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0-7 (only needed for backend)")
    parser.add_argument("-v", "--vfats", action="store", nargs="+", dest="vfats", help="vfats = list of VFAT numbers (0-23)")
    parser.add_argument("-c", "--config", action="store", dest="config", help="config = 1 for configure, 0 for unconfigure")
    parser.add_argument("-r", "--use_dac_scan_results", action="store_true", dest="use_dac_scan_results", help="use_dac_scan_results = to use previous DAC scan results for configuration")
    parser.add_argument("-lt", "--low_thresh", action="store_true", dest="low_thresh", help="low_thresh = to set low threshold for channels")
    args = parser.parse_args()

    if args.system == "chc":
        #print ("Using Rpi CHeeseCake for S-bit test")
        print (Colors.YELLOW + "Only Backend or dryrun supported" + Colors.ENDC)
        sys.exit()
    elif args.system == "backend":
        print ("Using Backend for S-bit test")
        #print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        #sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for S-bit test")
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

    if args.vfats is None:
        print (Colors.YELLOW + "Enter VFAT numbers" + Colors.ENDC)
        sys.exit()
    vfat_list = []
    for v in args.vfats:
        v_int = int(v)
        if v_int not in range(0,24):
            print (Colors.YELLOW + "Invalid VFAT number, only allowed 0-23" + Colors.ENDC)
            sys.exit()
        vfat_list.append(v_int)

    if args.config not in ["0", "1"]:
        print (Colors.YELLOW + "Only allowed options for configure: 0 and 1" + Colors.ENDC)
        sys.exit()
    configure = int(args.config)

    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML()
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system)
    initialize_vfat_config(int(args.ohid), args.use_dac_scan_results)
    print("Initialization Done\n")
    
    # Running Phase Scan
    try:
        lpgbt_vfat_config(args.system, int(args.ohid), vfat_list, args.low_thresh, configure)
    except KeyboardInterrupt:
        print (Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()




