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

def lpgbt_sub_reset(system, oh_select, choice, gbtid):

    gpio_dirH_node = getNode("LPGBT.RWF.PIO.PIODIRH")
    gpio_outH_node = getNode("LPGBT.RWF.PIO.PIOOUTH")

    gpio_dirH_addr = gpio_dirH_node.address
    gpio_outH_addr = gpio_outH_node.address

    gpio_for_sub = 9
    gpio_for_vtrx = 13
    boss = 1

    if choice == "vtrx":
        print("VTRX RESET\n")
        if system == "chc":
            config_initialize_chc(boss)
            check_lpgbt_ready()
        if system != "dryrun" and system != "backend":
            check_rom_readback()

        # Set GPIO as output
        gpio_dirH_output = 0x20

        if system == "backend":
            mpoke(gpio_dirH_addr, gpio_dirH_output)
        else:
            writeReg(gpio_dirH_node, gpio_dirH_output, 0)

        print("Set GPIO as output, register: 0x%03X, value: 0x%02X" % (gpio_dirH_addr, gpio_dirH_output))
        sleep(0.000001)

        data_enable = convert_gpio_reg(gpio_for_vtrx)
        data_disable = 0x00

        gpio_out_addr = gpio_outH_addr
        gpio_out_node = gpio_outH_node

    elif choice == "sub":
        print("SUB RESET\n")
        if system == "backend":
            check_lpgbt_link_ready(oh_select, gbtid)
            select_ic_link(oh_select, gbtid)
        elif system == "chc":
            config_initialize_chc(boss)
            check_lpgbt_ready()

        if system != "dryrun" and system != "backend":
            check_rom_readback()

        # Set GPIO as output
        gpio_dirH_output = 0x02

        if system == "backend":
            mpoke(gpio_dirH_addr, gpio_dirH_output)
        else:
            writeReg(gpio_dirH_node, gpio_dirH_output, 0)

        print("Set GPIO as output, register: 0x%03X, value: 0x%02X" % (gpio_dirH_addr, gpio_dirH_output))
        sleep(0.000001)

        data_enable = convert_gpio_reg(gpio_for_sub)
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

    vfat_oh_link_reset()
    sleep(0.1)


if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="lpGBT SUB RESET")
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc, backend or dryrun")
    parser.add_argument("-y", "--oh_v", action="store", dest="oh_v", help="oh_v = 2")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1")
    parser.add_argument("-c", "--choice", action="store", dest="choice", help="choice = vtrx or sub")
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

    if args.ohid is None and args.system == "backend":
        print(Colors.YELLOW + "Please select ohid = 0-1" + Colors.ENDC)
        sys.exit()
    elif args.ohid is not None and args.system == "chc":
        print(Colors.YELLOW + "Cannot select an ohid when running chc" + Colors.ENDC)
        sys.exit()
    elif args.ohid is None and (args.system == "chc" or args.system == "dryrun"):
        args.ohid  = -9999
    if int(args.ohid) > 1:
        print(Colors.YELLOW + "Only OHID 0-1 allowed" + Colors.ENDC)
        sys.exit()

    if args.choice == "vtrx":
        if args.gbtid is not None:
            print(Colors.YELLOW + "Cannot choose gbtid when resetting vtrx" + Colors.ENDC)
            sys.exit()
        else:
            gbtid = -9999
    elif args.choice == "sub":
        if args.gbtid is None:
            if args.system == "backend":
                print(Colors.YELLOW + "Must choose gbtid" + Colors.ENDC)
                sys.exit()
            if args.system == "backend":
                print(Colors.YELLOW + "Please select gbtid 0-7" + Colors.ENDC)
                sys.exit()
            if args.system == "dryrun":
                gbtid = -9999
        elif args.gbtid is not None:
            if args.system == "chc":
                print(Colors.YELLOW + "Cannot select gbtid when running chc" + Colors.ENDC)
                sys.exit()
            else:
                gbtid = int(args.gbtid)
                if gbtid not in [0,2,4,6]:
                    print(Colors.YELLOW + "Invalid master gbtid. Only 0, 2, 4, 6 allowed" + Colors.ENDC)
                    sys.exit()
    else:
        print(Colors.YELLOW + "Please choose either sub or vtrx" + Colors.ENDC)
        sys.exit()

    # Parsing Registers XML Files
    print("Parsing xml file...")
    parseXML(oh_v)
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system, oh_v)
    print("Initialization Done\n")

    # Running Phase Scan
    try:
        lpgbt_sub_reset(args.system, int(args.ohid), args.choice, gbtid)
    except KeyboardInterrupt:
        print(Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print(Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()
