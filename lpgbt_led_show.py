from rw_reg_lpgbt import *
import sys
import argparse
from time import *
import array
import struct

DEBUG=False

class Colors:            
    WHITE   = "\033[97m"
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    BLUE    = "\033[94m"
    YELLOW  = "\033[93m"
    GREEN   = "\033[92m"
    RED     = "\033[91m"
    ENDC    = "\033[0m"

def main(system, oh_v, boss, gpio_light, gpio_sound):

    print ("\Starting LED show\n")
    brightnessStart = 0
    while True: # cycle brightness from on to off and off to on approx once per second (assuming 100kHz update rate)
        brightnessEnd = 100
        step = 1
        if brightnessStart == 0:
            brightnessStart = 100
            brightnessEnd = -1
            step = -1
        else:
            brightnessStart = 0
            brightnessEnd = 101
            step = 1

        for b in range(brightnessStart, brightnessEnd, step): # one brightness cycle from on to off or off to on (100 steps per cycle)
            for i in range(10): # generate 10 clocks at a specific brightness
                for j in range(100): # generate a PWM waveform for one clock, setting the duty cycle according to the brightness
                    gpio = gpio_light
                    if j >= b:
                        gpio = 0
                    enable_pioout(gpio)
                    
        stop = raw_input(Colors.YELLOW + "Please type \"stop\" to stop the show: " + Colors.ENDC)
        if stop=="stop":
            writeReg(getNode("LPGBT.RWF.PIO.PIOOUTH"), 0x80, 0)
            print ("\nStopping LED show\n")
            break

def enable_pioout(gpio):
    if gpio in range(0, 8):
        on = hex(gpio)
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTH"), on, 0)
    if gpio in range(8,16):
        gpio = gpio - 8
        on = hex(gpio)
        writeReg(getNode("LPGBT.RWF.PIO.PIOOUTL"), on, 0)

def check_bit(byteval,idx):
    return ((byteval&(1<<idx))!=0);

def debug(string):
    if DEBUG:
        print("DEBUG: " + string)

def debugCyan(string):
    if DEBUG:
        printCyan("DEBUG: " + string)

def heading(string):                                                                    
    print (Colors.BLUE)
    print ("\n>>>>>>> "+str(string).upper()+" <<<<<<<")
    print (Colors.ENDC)
                                                      
def subheading(string):                         
    print (Colors.YELLOW)
    print ("---- "+str(string)+" ----",Colors.ENDC)
                                                                     
def printCyan(string):                                                
    print (Colors.CYAN)
    print (string, Colors.ENDC)
                                                                      
def printRed(string):                                                                                                                       
    print (Colors.RED)
    print (string, Colors.ENDC)

def hex(number):
    if number is None:
        return "None"
    else:
        return "{0:#0x}".format(number)

def binary(number, length):
    if number is None:
        return "None"
    else:
        return "{0:#0{1}b}".format(number, length + 2)

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="LpGBT LED Show")
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle or dryrun")
    parser.add_argument("-y", "--oh_v", action="store", dest="oh_v", default="1", help="oh_v = 1 or 2")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1 (only needed for backend)")
    parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0-7 (only needed for backend)")
    parser.add_argument("-g_l", "--gpio_light", action="store", dest="gpio_light", help="gpio_light = [15 for boss in OHv1] or [5 for boss or {0,1,3,8,13} for sub in OHv2]")
    parser.add_argument("-g_s", "--gpio_sound", action="store", dest="gpio_sound", help="gpio_sound = [{0, 1, 3, 8, 13} for sub in OHv2]")
    args = parser.parse_args()

    if args.system == "chc":
        print ("Using Rpi CHeeseCake for LED Show")
    elif args.system == "backend":
        print ("Using Backend for LED Show")
        #print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        #sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for LED Show"")
        print (Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun supported at the moment" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually doing the LED Show")
    else:
        print (Colors.YELLOW + "Only valid options: chc, backend, dongle, dryrun" + Colors.ENDC)
        sys.exit()

    boss = None
    if args.oh_v == "1":
        print("Using OHv1")
        if args.lpgbt is None or args.lpgbt is not "boss":
            print (Colors.YELLOW + "Please select boss for OH v1" + Colors.ENDC)
            sys.exit()
        else:
            print ("Configuring LPGBT as boss")
            boss = 1
            if args.gpio_light is None or args.gpio_light == "15":
                print("Enabling gpio15 for led")
            elif args.gpio_light != "15":
                print(Colors.YELLOW + "Selected gpio not available for led" + Colors.ENDC)
                sys.exit()
            if args.gpio_sound is not None:
                print(Colors.YELLOW + "Sound not supported for OHv1" + Colors.ENDC)
                sys.exit()
            else:
                args.gpio_sound = "-9999"
    elif args.oh_v == "2"
        print("Using OHv2")
        oh_v = 2
        if args.lpgbt is None:
            print (Colors.YELLOW + "Please select boss or sub for OH v2" + Colors.ENDC)
            sys.exit()
        elif args.lpgbt == "boss":
            print("Configuring LPGBT as boss")
            boss = 1
            if args.gpio_light is None or args.gpio_light == "5":
                print("Enabling gpio5 for led")
            elif args.gpio_light != "5":
                print(Colors.YELLOW + "Selected gpio not available for led" + Colors.ENDC)
                sys.exit()
            if args.gpio_sound is not None:
                print(Colors.YELLOW + "Sound not supported for master in OHv2" + Colors.ENDC)
                sys.exit()
            else:
                args.gpio_sound = "-9999"
        elif args.lpgbt == "sub":
            print ("Configuring LPGBT as sub")
            boss = 0
            if args.gpio_light is None:
                print(Colors.YELLOW + "Please select any of the following: {0, 1, 3, 8, 13}" + Colors.ENDC)
                sys.exit()
            gpio_free_list = [0, 1, 3, 8, 13]
            for gpio_free in gpio_free_list:
                if  int(args.gpio_light) != gpio_free
                    print(Colors.YELLOW + "Invalid gpio, only allowed {0, 1, 3, 8, 13}" + Colors.ENDC)
                    sys.exit()
            if args.gpio_sound is None:
                args.gpio_sound = "-9999"
            if args.gpio_sound == args.gpio_light:
                print(Colors.YELLOW + "Cannot select same gpio as led gpio" + Colors.ENDC)
                sys.exit()
            for gpio_free in gpio_free_list:
                if  int(args.gpio_sound) != gpio_free
                    print(Colors.YELLOW + "Invalid gpio, only allowed {0, 1, 3, 8, 13}" + Colors.ENDC)
                    sys.exit()
    else:
        print(Colors.YELLOW + "Please select either OH v1 or v2" + Colors.ENDC)
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


    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML(oh_v)
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

    # LPGBT LED Show
    try:
        main(args.system, int(args.oh_v), boss, int(args.gpio_light), int(args.gpio_sound))
    except KeyboardInterrupt:
        print (Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()

