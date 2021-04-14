from rw_reg_lpgbt import *
from time import sleep, time
import sys
import argparse
import random

# VFAT number: boss/sub, ohid, gbtid, gpio 
# For GE2/1 GEB + Pizza
VFAT_TO_GPIO = {
        0  : ("sub"  , 0, 1, 10),
        1  : ("sub"  , 0, 1, 9),
        2  : ("sub"  , 0, 1, 11),
        3  : ("boss" , 0, 0, 0),
        4  : ("boss" , 0, 0, 2),
        5  : ("boss" , 0, 0, 8),
        6  : ("boss" , 1, 0, 0), 
        7  : ("boss" , 1, 0, 8),
        8  : ("sub"  , 1, 1, 9), 
        9  : ("boss" , 1, 0, 2), 
        10 : ("sub"  , 1, 1, 10), 
        11 : ("sub"  , 1, 1, 11) 
}

# For ME0 GEB
#VFAT_TO_GPIO = {
#        0  : ("sub"  , 0, 1, 10),
#        1  : ("sub"  , 0, 1, 0),
#        2  : ("sub"  , 0, 1, 11),
#        3  : ("boss" , 0, 0, 0),
#        4  : ("boss" , 0, 0, 2),
#        5  : ("boss" , 0, 0, 8),
#        6  : ("boss" , 1, 0, 0), 
#        7  : ("boss" , 1, 0, 8),
#        8  : ("sub"  , 1, 1, 0), 
#        9  : ("boss" , 1, 0, 2), 
#        10 : ("sub"  , 1, 1, 10), 
#        11 : ("sub"  , 1, 1, 11) 
#}

def vfat_to_oh_gbt_gpio(vfat):
    lpgbt = VFAT_TO_GPIO[vfat][0]
    ohid  = VFAT_TO_GPIO[vfat][1]
    gbtid = VFAT_TO_GPIO[vfat][2]
    gpio = VFAT_TO_GPIO[vfat][3]
    return lpgbt, ohid, gbtid, gpio
        
def convert_gpio_reg(gpio):
    reg_data = 0
    if gpio<=7:
        bit = gpio
    else:
        bit = gpio - 8
    reg_data |= (0x01 << bit)
    return reg_data
        
def lpgbt_vfat_reset(system, vfat_list):
    print ("LPGBT VFAT RESET\n")
    
    gpio_dirH_addr = 0x052
    gpio_dirL_addr = 0x053
    gpio_outH_addr = 0x054
    gpio_outL_addr = 0x055
    
    for vfat in vfat_list:
        lpgbt, oh_select, gbt_select, gpio = vfat_to_oh_gbt_gpio(vfat)
        print ("VFAT#: %02d, lpGBT: %s, OH: %d, GBT: %d, GPIO: %d" %(vfat, lpgbt, oh_select, gbt_select, gpio))
        
        boss=0
        if lpgbt=="boss":
            boss=1
        
        if system=="backend":
            check_lpgbt_link_ready(oh_select, gbt_select)
            select_ic_link(oh_select, gbt_select)
        elif system=="chc":
            config_initialize_chc(boss)
            check_lpgbt_ready()
                     
        if system!="dryrun" and system!="backend":
            check_rom_readback()
        
        data_enable = convert_gpio_reg(gpio)
        data_disable = 0x00
        gpio_dir_addr = 0
        gpio_out_addr = 0
        if gpio<=7:
            gpio_dir_addr = gpio_dirL_addr
            gpio_out_addr = gpio_outL_addr
        else:
            gpio_dir_addr = gpio_dirH_addr
            gpio_out_addr = gpio_outH_addr
            if boss:
                data_enable |= 0x80 # To keep GPIO LED on ASIAGO ON
                data_disable |= 0x80 # To keep GPIO LED on ASIAGO ON
        
        mpoke(gpio_dir_addr, data_enable) # Set GPIO as output
        print ("Set GPIO as output (including GPIO 15 for boss lpGBT), register: 0x%03X, value: 0x%02X" %(gpio_dir_addr, data_enable))
        sleep(0.000001) 
            
        mpoke(gpio_out_addr, data_enable) # Reset - 1
        print ("Enable GPIO to reset (including GPIO 15 for boss lpGBT), register: 0x%03X, value: 0x%02X" %(gpio_out_addr, data_enable))
        sleep(0.000001) 
            
        mpoke(gpio_out_addr, data_disable) # Reset - 0
        print ("Disable GPIO (except GPIO 15 for boss lpGBT), register: 0x%03X, value: 0x%02X" %(gpio_out_addr, data_disable))
        sleep(0.000001) 
        
        print ("")
        
    # Link reset after VFAT reset
    vfat_oh_link_reset()
    
    
if __name__ == '__main__':

    # Parsing arguments
    parser = argparse.ArgumentParser(description='lpGBT VFAT RESET')
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc, backend or dryrun")
    #parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-v", "--vfats", action="store", dest="vfats", nargs='+', help="vfats = list of VFATs (0-11)")
    #parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-7 (only needed for backend)")
    #parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0, 1 (only needed for backend)")
    args = parser.parse_args()

    if args.system == "chc":
        print ("Using Rpi CHeeseCake for VFAT reset")
        sys.exit()
    elif args.system == "backend":
        print ("Using Backend for VFAT reset")
        #print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        #sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for VFAT reset")
        print (Colors.YELLOW + "Only Backend or dryrun supported" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually running vfat bert")
    else:
        print (Colors.YELLOW + "Only valid options: backend, dryrun" + Colors.ENDC)
        sys.exit()

    if args.vfats is None:
        print (Colors.YELLOW + "Enter VFAT numbers" + Colors.ENDC)
        sys.exit()
    vfat_list = []
    for v in args.vfats:
        v_int = int(v)
        if v_int not in range(0,12):
            print (Colors.YELLOW + "Invalid VFAT number, only allowed 0-11" + Colors.ENDC)
            sys.exit()
        vfat_list.append(v_int)
       
    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML()
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system)
    print("Initialization Done\n")
    
    # Running Phase Scan
    try:
        lpgbt_vfat_reset(args.system, vfat_list)
    except KeyboardInterrupt:
        print (Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()




