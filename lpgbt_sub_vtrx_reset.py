from rw_reg_lpgbt import *
from time import sleep, time
import sys
import argparse

def convert_gpio_reg(gpio):
    reg_data = 0
    if gpio <= 7:
        bit = gpio
    else:
        bit = gpio - 8
    reg_data |= (0x01 << bit)
    return reg_data

def lpgbt_sub_vtrx_reset(system, oh_v, boss, reset):

    gpio_dirH_node = getNode("LPGBT.RWF.PIO.PIODIRH")
    gpio_outH_node = getNode("LPGBT.RWF.PIO.PIOOUTH")
    gpio_dirL_node = getNode("LPGBT.RWF.PIO.PIODIRL")
    gpio_outL_node = getNode("LPGBT.RWF.PIO.PIOOUTL")
    gpio_dirH_addr = gpio_dirH_node.address
    gpio_outH_addr = gpio_outH_node.address
    gpio_dirL_addr = gpio_dirL_node.address
    gpio_outL_addr = gpio_outL_node.address

    # Set GPIO as output
    gpio_dirH_output = 0
    gpio_dirL_output = 0
    if oh_v == 1:
        if (boss):
            gpio_dirH_output = 0x80 | 0x01
            gpio_dirL_output = 0x01 | 0x04 # set as outputs
        else:
            gpio_dirH_output = 0x02 | 0x04 | 0x08 # set as outputs
            gpio_dirL_output = 0x00 # set as outputs
    elif of_v == 2:
        if (boss):
            gpio_dirH_output = 0x01 | 0x02 | 0x20 # set as outputs (8, 9, 13)
            gpio_dirL_output = 0x01 | 0x04 | 0x20 # set as outputs (0, 2, 5)
        else:
            gpio_dirH_output = 0x01 | 0x02 | 0x04 | 0x08 | 0x20 # set as outputs
            gpio_dirL_output = 0x01 | 0x02 | 0x08 # set as outputs

    if system == "backend":
        mpoke(gpio_dirH_addr, gpio_dirH_output)
        mpoke(gpio_dirL_addr, gpio_dirL_output)
    else:
        writeReg(gpio_dirH_node, gpio_dirH_output, 0)
        writeReg(gpio_dirL_node, gpio_dirL_output, 0)

    print("Set GPIO as output (including GPIO 15/5 for boss lpGBT for OH-v1/v2), register: 0x%03X, value: 0x%02X" % (
    gpio_dirH_addr, gpio_dirH_output))
    print("Set GPIO as output, register: 0x%03X, value: 0x%02X" % (gpio_dirL_addr, gpio_dirL_output))
    sleep(0.000001)

    gpio = 0
    if reset == "vtrx":
        print("VTRx+ RESET\n")
        gpio  = 13
    elif reset == "sub":
        print("SUB RESET\n")
        gpio = 9

    data_enable = convert_gpio_reg(gpio)
    data_disable = 0x00

    gpio_out_addr = gpio_outH_addr
    gpio_out_node = gpio_outH_node

    # Reset - 1
    if system == "backend":
        mpoke(gpio_out_addr, data_enable)
    else:
        writeReg(gpio_out_node, data_enable, 0)
    print("Enable GPIO to reset, register: 0x%03X, value: 0x%02X" % (gpio_out_addr, data_enable))
    sleep(0.000001)

    # Reset - 0
    if system == "backend":
        mpoke(gpio_out_addr, data_disable)
    else:
        writeReg(gpio_out_node, data_disable, 0)
    print("Disable GPIO, register: 0x%03X, value: 0x%02X" % (gpio_out_addr, data_disable))
    sleep(0.000001)

    print("")



if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="lpGBT SUB RESET")
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc, backend or dryrun")
    parser.add_argument("-y", "--oh_v", action="store", dest="oh_v", help="oh_v = 2")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = only boss")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1 (only needed for backend)")
    parser.add_argument("-r", "--reset", action="store", dest="reset", help="reset = sub or vtrx")
    parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0-7 (only needed for backend)")
    
    args = parser.parse_args()

    if args.system == "chc":
        print("Using Rpi CHeeseCake for sub reset")
        args.ohid = -9999
    elif args.system == "backend":
        print("Using Backend for sub reset")
    elif args.system == "dongle":
        # print ("Using USB Dongle for VFAT reset")
        print(Colors.YELLOW + "Only Backend or dryrun supported" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print("Dry Run - not actually running")
    else:
        print(Colors.YELLOW + "Only valid options: backend, dryrun" + Colors.ENDC)
        sys.exit()

    if args.oh_v == "2":
        print("Using OH v2")
        oh_v = 2
    else:
        print(Colors.YELLOW + "Reset line connected for oh_v2 only" + Colors.ENDC)
        sys.exit()

    boss = None
    if args.lpgbt is None:
        print (Colors.YELLOW + "Please select boss or sub" + Colors.ENDC)
        sys.exit()
    elif (args.lpgbt=="boss"):
        print ("Configuring LPGBT as boss")
        boss=1
    elif (args.lpgbt=="sub"):
        print ("Only boss lpGBT is allowed")
        boss = 0
        sys.exit()
    else:
        print (Colors.YELLOW + "Please select boss only" + Colors.ENDC)
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

    if args.reset not in ["vtrx", "sub"]:
         print(Colors.YELLOW + "Please choose either sub or vtrx" + Colors.ENDC)
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
        check_lpgbt_mode(boss)

    # Check if lpGBT is READY
    if args.system!="dryrun":
        if args.system=="backend":
            check_lpgbt_link_ready(args.ohid, args.gbtid)
        else:
            check_lpgbt_ready()

    # Running Phase Scan
    try:
        lpgbt_sub_vtrx_reset(args.system, oh_v, boss, args.reset)
    except KeyboardInterrupt:
        print(Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print(Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()
