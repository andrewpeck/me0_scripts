from rw_reg_lpgbt import *
from time import sleep, time
import sys
import argparse

def main(system, boss, action, oh_select, gbt_select):
    print ("")
    if boss:
        print ("Performing action for boss lpGBT\n")
    else:
        print ("Performing action for sub lpGBT\n")

    if action=="reset":
        print ("Reset lpGBT\n")
        mpoke(0x12C, 0x80)

        check_ready = 0
        t0 = time()
        while not check_ready:
            check_ready = read_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH_LINKS.OH%s.GBT%s_READY" % (oh_select, gbt_select)))
        print ("Time taken for lpGBT to get back to READY state: %.4f sec"%(time()-t0))

    elif action=="enable":
        #if boss:
        #    print ("Enabling EC channel\n")
        #    mpoke(0xA8, 0x1F)
        
        print ("Enabling WatchDog\n")
        mpoke(0xED, 0x03)
    elif action=="disable":
        #if boss:
        #    print ("Disabling EC channel\n")
        #    mpoke(0xA8, 0x0F)
        
        print ("Disabling WatchDog\n")
        mpoke(0xED, 0x63)

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="LpGBT Reset, Disable/Enable Watchdog")
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle or dryrun")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1 (only needed for backend)")
    parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0-7 (only needed for backend)")
    parser.add_argument("-a", "--action", action="store", dest="action", help="action = reset, enable, disable")
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
        print ("For boss LPGBT")
        boss=1
    elif (args.lpgbt=="sub"):
        print ("For sub LPGBT")
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
        if int(args.ohid)>1:
            print (Colors.YELLOW + "Only OHID 0-1 allowed" + Colors.ENDC)
            sys.exit()
        if int(args.gbtid)>7:
            print (Colors.YELLOW + "Only GBTID 0-7 allowed" + Colors.ENDC)
            sys.exit() 
    else:
        if args.ohid is not None or args.gbtid is not None:
            print (Colors.YELLOW + "OHID and GBTID only needed for backend" + Colors.ENDC)
            sys.exit()
    
    if args.action not in ["reset", "enable", "disable"]:
        print (Colors.YELLOW + "Valid option only reset, enable or disable" + Colors.ENDC)
        sys.exit()
    elif args.action == "reset":
        print ("Reset lpGBT")
    elif args.action == "disable":
        print ("Disabling Watchdog")
    elif args.action == "enable":
        print ("Enabling Watchdog")

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
        main(args.system, boss, args.action, args.ohid, args.gbtid)
    except KeyboardInterrupt:
        print (Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()
