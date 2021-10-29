from rw_reg_lpgbt import *
from time import sleep, time
import sys
import argparse

def main(system, boss, reset, invert_rx, invert_clk, invert_tx, ecphase):

    if boss:
        print ("Initialize boss lpGBT\n")
    else:
        print ("Initialize sub lpGBT\n")

    if reset=="pll_reset":
        if system=="backend":
            mpoke(0x12C, 0x80)
            sleep(2)
            mpoke(0x12C, 0x00)
        else:
            writeReg(getNode("LPGBT.RW.RESET.RSTPLLDIGITAL"), 0x01, 0)
            sleep(2)
            writeReg(getNode("LPGBT.RW.RESET.RSTPLLDIGITAL"), 0x00, 0)
        print ("Reset Done\n")
    elif reset=="full_reset":
        if system=="backend":
            mpoke(0x130, 0xA3)
            mpoke(0x12F, 0x80)
        else:
            writeReg(getNode("LPGBT.RW.POWERUP.PUSMFORCEMAGIC"), 0xA3, 0)
            writeReg(getNode("LPGBT.RW.POWERUP.PUSMFORCESTATE"), 0x01, 0)
            writeReg(getNode("LPGBT.RW.POWERUP.PUSMSTATEFORCED"), 0x00, 0)
        print ("Reset Done\n")

    if ecphase:
        if system=="backend":
            mpoke(0x0CB, 0x02)
        else:
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRXECTRACKMODE"), 0x2, readback)
        print ("Continuous phase tracking set for EC link\n")

    if invert_rx:
        invert_eprx(boss, 0)
        print ("EPRX inversion Done\n")

    if invert_clk:
        invert_epclk(boss, 0)
        print ("EPCLK inversion Done\n")

    if invert_tx:
        invert_eptx(boss, 0)
        print ("EPTX inversion Done\n")

    print ("Initialization Done\n")

def invert_eprx(boss, readback):
    if (boss):
        if system=="backend":
            mpoke(0x0D5, 0x0A)
            mpoke(0x0D0, 0x0A)
            mpoke(0x0CE, 0x0A)
            mpoke(0x0CC, 0x0A)
            mpoke(0x0DF, 0x0A)
            mpoke(0x0DD, 0x0A)
            mpoke(0x0DE, 0x0A)
            mpoke(0x0E0, 0x0A)
            mpoke(0x0E2, 0x0A)
            mpoke(0x0E4, 0x0A)
            mpoke(0x0E6, 0x0A)
            mpoke(0x0E5, 0x0A)
        else:
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX9INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX4INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX2INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX0INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX19INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX17INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX18INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX20INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX22INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX24INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX26INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX25INVERT"), 0x1, readback)
    else:
        if system=="backend":
            mpoke(0x0E1, 0x0A)
            mpoke(0x0E3, 0x0A)
            mpoke(0x0E7, 0x0A)
            mpoke(0x0E5, 0x0A)
            mpoke(0x0E4, 0x0A)
            mpoke(0x0D5, 0x0A)
            mpoke(0x0D6, 0x0A)
            mpoke(0x0CF, 0x0A)
            mpoke(0x0D1, 0x0A)
            mpoke(0x0CD, 0x0A)
            mpoke(0x0D8, 0x0A)
        else:
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX21INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX23INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX27INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX24INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX25INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX9INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX10INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX3INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX5INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX1INVERT"), 0x1, readback)
            writeReg(getNode("LPGBT.RWF.EPORTRX.EPRX_CHN_CONTROL.EPRX12INVERT"), 0x1, readback)

def invert_epclk(boss, readback):
    if (boss):
        if system=="backend":
            mpoke(0x07A, 0x5C)
        else:
            writeReg(getNode("LPGBT.RWF.EPORTCLK.EPCLK7INVERT"), 0x1, readback)

def invert_eptx(boss, readback):
    if (boss):
        if system=="backend":
            mpoke(0x0BE, 0x08)
            mpoke(0x0C1, 0x80)
        else:
            writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX10INVERT"), 0x1, readback) #boss 4
            writeReg(getNode("LPGBT.RWF.EPORTTX.EPTX23INVERT"), 0x1, readback) #boss 11


if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="lpGBT Initialization")
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle or dryrun")
    parser.add_argument("-y", "--oh_v", action="store", dest="oh_v", default="1", help="oh_v = 1 or 2")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1 (only needed for backend)")
    parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0-7 (only needed for backend)")
    parser.add_argument("-r", "--reset", action="store", dest="reset", help="reset = pll_reset or full_reset")
    parser.add_argument("-e", "--ecphase", action="store", dest="ecphase", help="ecphase = to set continuous phase tracking for EC link")
    parser.add_argument("-irx", "--invert_rx", action="store_true", dest="invert_rx", help="invert_rx = to invert eprx")
    parser.add_argument("-iclk", "--invert_clk", action="store_true", dest="invert_clk", help="invert_clk = to invert epclk")
    parser.add_argument("-itx", "--invert_tx", action="store_true", dest="invert_tx", help="invert_tx = to invert eptx")
    args = parser.parse_args()

    if args.system == "chc":
        print ("Using Rpi CHeeseCake for initialization")
    elif args.system == "backend":
        print ("Using Backend for initialization")
    elif args.system == "dongle":
        #print ("Using USB Dongle for reset")
        print (Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun supported at the moment" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually initializing lpGBT")
    else:
        print (Colors.YELLOW + "Only valid options: chc, backend, dongle, dryrun" + Colors.ENDC)
        sys.exit()

    if args.oh_v == "1":
        print("Using OH v1")
        oh_v = 1
    elif args.oh_v == "2":
        print("Using OH v2")
        oh_v = 2
    else:
        print(Colors.YELLOW + "Please select either OH v1 or v2" + Colors.ENDC)
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

    if args.reset is not None:
        if args.reset not in ["pll_reset", "full_reset"]:
            print (Colors.YELLOW + "Valid options for type = pll_reset, full_reset" + Colors.ENDC)
            sys.exit()

    if not boss:
        if args.invert_clk:
            print (Colors.YELLOW + "EPCLK inversion only for boss" + Colors.ENDC)
            sys.exit()
        if args.invert_tx:
            print (Colors.YELLOW + "EPTX inversion only for boss" + Colors.ENDC)
            sys.exit()

    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML(oh_v)
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system, oh_v, boss, args.ohid, args.gbtid)
    print("Initialization Done\n")
    
    # Readback rom register to make sure communication is OK
    if args.system!="dryrun" and args.system!="backend":
        check_rom_readback()

    # Check if lpGBT is READY if running through backend
    #if args.system=="backend":
    #    check_lpgbt_link_ready(args.ohid, args.gbtid)

    # Configuring LPGBT
    try:
        main(args.system, boss, args.reset, args.invert_rx, args.invert_clk, args.invert_tx, args.ecphase)
    except KeyboardInterrupt:
        print (Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()
