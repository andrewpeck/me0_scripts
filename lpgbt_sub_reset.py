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

def lpgbt_vfat_reset(system, oh_select):
    print("SUB RESET\n")

    gpio_dirH_addr = 0x053
    gpio_outH_addr = 0x055
    gpio_dirH_node = getNode("LPGBT.RWF.PIO.PIODIRH")
    gpio_outH_node = getNode("LPGBT.RWF.PIO.PIOOUTH")

    gpio = 9
    boss = 1

    if system == "backend":
        check_lpgbt_link_ready(oh_select, gbt_select)
        select_ic_link(oh_select, gbt_select)
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

    # Link reset after VFAT reset
    # vfat_oh_link_reset()
    sleep(0.1)


if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="lpGBT VFAT RESET")
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc, backend or dryrun")
    parser.add_argument("-y", "--oh_v", action="store", dest="oh_v", default="1", help="oh_v = 1 or 2")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1")
    
    args = parser.parse_args()

    if args.system == "chc":
        print("Using Rpi CHeeseCake for VFAT reset")
    elif args.system == "backend":
        print("Using Backend for VFAT reset")
        # print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        # sys.exit()
    elif args.system == "dongle":
        # print ("Using USB Dongle for VFAT reset")
        print(Colors.YELLOW + "Only Backend or dryrun supported" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print("Dry Run - not actually running vfat bert")
    else:
        print(Colors.YELLOW + "Only valid options: backend, dryrun" + Colors.ENDC)
        sys.exit()

    if args.oh_v == "2":
        print("Using OH v2")
        oh_v = 2
    else:
        print(Colors.YELLOW + "Reset line connected for oh_v2 only" + Colors.ENDC)
        sys.exit()

    if args.ohid is None:
        print(Colors.YELLOW + "Need OHID" + Colors.ENDC)
        sys.exit()
    if int(args.ohid) > 1:
        print(Colors.YELLOW + "Only OHID 0-1 allowed" + Colors.ENDC)
        sys.exit()

    # Parsing Registers XML Files
    print("Parsing xml file...")
    parseXML(oh_v)
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system)
    print("Initialization Done\n")

    # Running Phase Scan
    try:
        lpgbt_vfat_reset(args.system, int(args.ohid), vfat_list)
    except KeyboardInterrupt:
        print(Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print(Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()