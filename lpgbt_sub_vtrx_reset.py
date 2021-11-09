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

    gpio = 0
    if reset == "vtrx":
        print("VTRx+ RESET\n")
        gpio  = 13
    elif reset == "sub":
        print("SUB RESET\n")
        gpio = 9

    dir_enable = convert_gpio_reg(gpio)
    dir_disable = 0x00
    data_enable = convert_gpio_reg(gpio)
    data_disable = 0x00
    gpio_dir_addr = 0
    gpio_dir_node = ""
    gpio_out_addr = 0
    gpio_out_node = ""

    # These 2 resets are only for OH-v2
    if gpio <= 7:
        gpio_dir_addr = gpio_dirL_addr
        gpio_dir_node = gpio_dirL_node
        gpio_out_addr = gpio_outL_addr
        gpio_out_node = gpio_outL_node
        if boss:
            dir_enable |= 0x20  # To keep GPIO LED on ASIAGO output enabled
            dir_disable |= 0x20  # To keep GPIO LED on ASIAGO output enabled
            #data_enable |= 0x20  # To keep GPIO LED on ASIAGO ON
            data_disable |= 0x20  # To keep GPIO LED on ASIAGO ON
        else:
            dir_enable |= 0x01 | 0x02 | 0x08  # To keep GPIO LED on ASIAGO output enabled
            dir_disable |= 0x01 | 0x02 | 0x08  # To keep GPIO LED on ASIAGO output enabled
            #data_enable |= 0x00
            data_disable |= 0x00
    else:
        gpio_dir_addr = gpio_dirH_addr
        gpio_dir_node = gpio_dirH_node
        gpio_out_addr = gpio_outH_addr
        gpio_out_node = gpio_outH_node
        if not boss:
            dir_enable |= 0x01 | 0x20  # To keep GPIO LED on ASIAGO output enabled
            dir_disable |= 0x01 | 0x20  # To keep GPIO LED on ASIAGO output enabled
            #data_enable |= 0x00
            data_disable |= 0x00

    # Enable GPIO as output
    if system == "backend":
        mpoke(gpio_dir_addr, dir_enable)
    else:
        writeReg(gpio_dir_node, dir_enable, 0)
    print("Enable GPIO %d as output"%gpio)
    sleep(0.000001)

    # Set GPIO to 0 for reset
    if system == "backend":
        mpoke(gpio_out_addr, data_disable)
    else:
        writeReg(gpio_out_node, data_disable, 0)
    print("Set GPIO %d to 0 for reset"%gpio)
    sleep(0.1)

    # Disable GPIO as output
    if system == "backend":
        mpoke(gpio_dir_addr, dir_disable)
    else:
        writeReg(gpio_dir_node, dir_disable, 0)
    print("Disable GPIO %d as output"%gpio)
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
