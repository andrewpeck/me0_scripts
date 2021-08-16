from rw_reg_lpgbt import *
from time import sleep, time
import sys
import argparse

def main(system, boss, reg_list, data_list):

    for i in range(0, len(reg_list)):
        r = reg_list[i]
        if r>0x1CE:
            print (Colors.YELLOW + "Register address out of range" + Colors.ENDC)
            rw_terminate()
        if system!="backend":
            data_read = mpeek(r)
            print ("Register: " + hex(r) + ", Initial data: " + hex(data_read))

        if len(data_list)==0:
            print ("")
            continue
        
        d = data_list[i]
        
        if r>0x13C:
            print (Colors.YELLOW + "Register is Read-only" + Colors.ENDC)
            rw_terminate()
        mpoke(r, d)
        print ("Register: " + hex(r) + ", Data written: " + hex(d))

        if system!="backend":
            data_written = mpeek(r)
            if data_written == d:
                print (Colors.GREEN + "Register: " + hex(r) + ", Data read: " + hex(data_written) + Colors.ENDC)
            else:
                print (Colors.RED + "Register: " + hex(r) + ", Data read: " + hex(data_written) + Colors.ENDC)
    
        print ("")
    
if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="LpGBT R/W Registers")
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle or dryrun")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1 (only needed for backend)")
    parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0-7 (only needed for backend)")
    parser.add_argument("-r", "--reg", action="store", nargs="+", dest="reg", help="reg = register to read or write (in 0x format)")
    parser.add_argument("-d", "--data", action="store", nargs="+", dest="data", help="data = data to write to registers (in 0x format)") 
    args = parser.parse_args()

    if args.system == "chc":
        print ("Using Rpi CHeeseCake for configuration")
    elif args.system == "backend":
        print ("Using Backend for configuration")
        #print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        #sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for configuration")
        print (Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun supported at the moment" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually configuring lpGBT")
    else:
        print (Colors.YELLOW + "Only valid options: chc, backend, dongle, dryrun" + Colors.ENDC)
        sys.exit()

    boss = None
    if args.lpgbt is None:
        print (Colors.YELLOW + "Please select boss or sub" + Colors.ENDC)
        sys.exit()
    elif (args.lpgbt=="boss"):
        print ("Using boss LPGBT")
        boss=1
    elif (args.lpgbt=="sub"):
        print ("Using sub LPGBT")
        boss=0
    else:
        print (Colors.YELLOW + "Please select boss or sub" + Colors.ENDC)
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
        if int(args.ohid) > 1:
            print(Colors.YELLOW + "Only OHID 0-1 allowed" + Colors.ENDC)
            sys.exit()
        if int(args.gbtid) > 7:
            print(Colors.YELLOW + "Only GBTID 0-7 allowed" + Colors.ENDC)
            sys.exit()
    else:
        if args.ohid is not None or args.gbtid is not None:
            print (Colors.YELLOW + "OHID and GBTID only needed for backend" + Colors.ENDC)
            sys.exit()
    
    reg_list = []
    data_list = []
    if args.reg is None:
        print (Colors.YELLOW + "Enter registers to read/write" + Colors.ENDC)
        sys.exit()
    for r in args.reg:
        if "0x" not in r:
            print (Colors.YELLOW + "Only hex format allowed" + Colors.ENDC)
            sys.exit()
        r_val = int(r,16)
        if r_val>(2**16-1):
            print (Colors.YELLOW + "Only 16 bit register addresses allowed" + Colors.ENDC)
            sys.exit()
        reg_list.append(r_val)
    if args.data is not None:
        for d in args.data:
            if "0x" not in d:
                print (Colors.YELLOW + "Only hex format allowed" + Colors.ENDC)
                sys.exit()
            d_val = int(d,16)
            if d_val>(2**8-1):
                print (Colors.YELLOW + "Only 8 bit register values allowed" + Colors.ENDC)
                sys.exit()
            data_list.append(d_val)
    if len(data_list)!=0 and (len(reg_list) != len(data_list)):
        print (Colors.YELLOW + "Number of data values must equal the number of registers" + Colors.ENDC)
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

    # Check if lpGBT is READY if running through backend
    #if args.system=="backend":
    #    check_lpgbt_link_ready(args.ohid, args.gbtid)

    # Configuring LPGBT
    try:
        main(args.system, boss, reg_list, data_list)
    except KeyboardInterrupt:
        print (Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()
