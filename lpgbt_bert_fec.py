from rw_reg_lpgbt import *
from time import time
import sys
import argparse

def check_fec_errors(system, boss, path, ohid, gbtid, runtime, verbose):

    print ("Checking FEC Errors for: " + path)
    fec_errors = 0

    if path == "uplink": # check FEC errors on backend
        # Reset the error counters
        node = get_rwreg_node('GEM_AMC.GEM_SYSTEM.CTRL.LINK_RESET')
        write_backend_reg(node, 0x001)
        
        fec_node = get_rwreg_node('GEM_AMC.OH%d.GBT%d_FEC_ERR_CNT' % (ohid, gbtid))
        
        # start error counting loop
        start_fec_errors = read_backend_reg(fec_node)
        print ("Start Error Counting for time = %f minutes" % (runtime))
        print ("Starting with number of FEC Errors = %d\n" % (start_fec_errors))
        t0 = time()
        time_prev = t0
        
        while ((time()-t0)/60.0) < runtime:
            time_passed = (time()-time_prev)/60.0
            if time_passed >= 1:
                curr_fec_errors = read_backend_reg(fec_node)
                if verbose:
                    print ("Time passed: %f minutes, number of FEC errors accumulated = %d" % ((time()-t0)/60.0, curr_fec_errors))
                time_prev = time()
        
        end_fec_errors = read_backend_reg(fec_node)
        print ("\nEnd Error Counting with number of FEC Errors = %d\n" %(end_fec_errors))
        fec_errors = end_fec_errors - start_fec_errors
        
    elif path == "downlink": # check FEC errors on lpGBT
        # Enable the counter
        writeReg(getNode("LPGBT.RW.PROCESS_MONITOR.DLDPFECCOUNTERENABLE"), 0x1, 0)
    
        # start error counting loop
        start_fec_errors = lpgbt_fec_error_counter()
        print ("Start Error Counting for time = %f minutes" % (runtime))
        print ("Starting with number of FEC Errors = %d\n" % (start_fec_errors))
        t0 = time()
        time_prev = t0
        
        while ((time()-t0)/60.0) < runtime:
            time_passed = (time()-time_prev)/60.0
            if time_passed >= 1:
                curr_fec_errors = lpgbt_fec_error_counter()
                if verbose:
                    print ("Time passed: %f minutes, number of FEC errors accumulated = %d" % ((time()-t0)/60.0, lpgbt_fec_error_counter()))
                time_prev = time()
        
        end_fec_errors = lpgbt_fec_error_counter()
        print ("\nEnd Error Counting with number of FEC Errors = %d\n" %(end_fec_errors))
        fec_errors = end_fec_errors - start_fec_errors
        
        # Disable the counter
        writeReg(getNode("LPGBT.RW.PROCESS_MONITOR.DLDPFECCOUNTERENABLE"), 0x0, 0)
            
    result_string = ""
    if fec_errors == 0:
        result_string += Colors.GREEN 
    else:
        result_string += Colors.YELLOW 
    result_string += "Number of FEC errors in " + str(runtime) + " minutes: " + str(fec_errors) + Colors.ENDC + "\n"
    print (result_string)
    
    
def lpgbt_fec_error_counter():
    error_counter_h = readReg(getNode("LPGBT.RO.FEC.DLDPFECCORRECTIONCOUNT_H"))
    error_counter_l = readReg(getNode("LPGBT.RO.FEC.DLDPFECCORRECTIONCOUNT_L"))
    error_counter = (error_counter_h << 8) | error_counter_l
    return error_counter   
       
       
if __name__ == '__main__':
    # Parsing arguments
    parser = argparse.ArgumentParser(description='LPGBT Bit Error Rate Test (BERT) using FEC Error Counters')
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle or dryrun")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss/sub")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-7 (only needed for backend)")
    parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0, 1 (only needed for backend)") 
    parser.add_argument("-p", "--path", action="store", dest="path", help="path = uplink, downlink")
    parser.add_argument("-t", "--time", action="store", dest="time", help="TIME = measurement time in minutes")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", help="VERBOSE")
    args = parser.parse_args()

    if args.system == "chc":
        print ("Using Rpi CHeeseCake for BERT")
    elif args.system == "backend":
        print ("Using Backend for BERT")
        #print (Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun supported at the moment" + Colors.ENDC)
        #sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for checking configuration")
        print (Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun supported at the moment" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually running on lpGBT")
    else:
        print (Colors.YELLOW + "Only valid options: chc, backend, dongle, dryrun" + Colors.ENDC)
        sys.exit()

    boss = None
    if args.lpgbt is None:
        print (Colors.YELLOW + "Please select boss/sub" + Colors.ENDC)
        sys.exit()
    elif (args.lpgbt=="boss"):
        print ("BERT for boss LPGBT")
        boss=1
    elif (args.lpgbt=="sub"):
        print ("BERT for sub LPGBT")
        boss=0
    else:
        print (Colors.YELLOW + "Please select boss/sub" + Colors.ENDC)
        sys.exit()
    if boss is None:
        sys.exit()
      
    if args.system == "backend":
        if args.ohid is None:
            print (Colors.YELLOW + "Need OHID for backend" + Colors.ENDC)
            sys.exit()
        if args.gbtid is None:
            print (Colors.YELLOW + "Need GBTID for backend" + Colors.ENDC)
            sys.exit()
        if int(args.ohid)>7:
            print (Colors.YELLOW + "Only OHID 0-7 allowed" + Colors.ENDC)
            sys.exit()
        if int(args.gbtid)>1:
            print (Colors.YELLOW + "Only GBTID 0 and 1 allowed" + Colors.ENDC)
            sys.exit() 
    else:
        if args.ohid is not None or args.gbtid is not None:
            print (Colors.YELLOW + "OHID and GBTID only needed for backend" + Colors.ENDC)
            sys.exit()

    if args.path not in ["uplink", "downlink"]:
        print (Colors.YELLOW + "Enter valid path" + Colors.ENDC)
        sys.exit()

    if args.path == "uplink":
        if args.system == "chc":
            print (Colors.YELLOW + "For uplink, cheesecake not possible" + Colors.ENDC)
            sys.exit()

    if not boss:
        if args.path != "uplink":
            print (Colors.YELLOW + "Only uplink can be checked for sub lpGBT" + Colors.ENDC)
            sys.exit()

    if args.time is None:
        print (Colors.YELLOW + "BERT measurement time required" + Colors.ENDC)
        sys.exit()

    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML()
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system, boss, args.ohid, args.gbtid)
    print("Initialization Done\n")
    
    # Readback rom register to make sure communication is OK
    if args.system!="dryrun" and args.system!="backend":
        check_rom_readback()

    # Check if lpGBT is READY
    if args.system!="dryrun":
        if args.system=="backend":
            check_lpgbt_link_ready(args.ohid, args.gbtid)
        else:
            check_lpgbt_ready()

    try:
        check_fec_errors(args.system, boss, args.path, int(args.ohid), int(args.gbtid), float(args.time), args.verbose)
 
    except KeyboardInterrupt:
        print (Colors.RED + "\nKeyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()