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

def main(system, boss):

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
                    on = 0x80
                    if j >= b:
                        on = 0x00
                    writeReg(getNode("LPGBT.RWF.PIO.PIOOUTH"), on, 0)

        stop = raw_input(Colors.YELLOW + "Please type \"stop\" to stop the show: " + Colors.ENDC)
        if stop=="stop":
            writeReg(getNode("LPGBT.RWF.PIO.PIOOUTH"), 0x80, 0)
            print ("\nStopping LED show\n")
            break

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
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1 (only needed for backend)")
    parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0-7 (only needed for backend)")
    args = parser.parse_args()

    if args.system == "chc":
        print ("Using Rpi CHeeseCake for LED Show"")
    elif args.system == "backend":
        print ("Using Backend for LED Show"")
        #print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        #sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for LED Show"")
        print (Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun supported at the moment" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually doing the LED Show"")
    else:
        print (Colors.YELLOW + "Only valid options: chc, backend, dongle, dryrun" + Colors.ENDC)
        sys.exit()

    boss = None
    if args.lpgbt is None:
        print (Colors.YELLOW + "Please select boss or sub" + Colors.ENDC)
        sys.exit()
    elif (args.lpgbt=="boss"):
        print ("Configuring LPGBT as boss")
        boss=1
    elif (args.lpgbt=="sub"):
        print ("Configuring LPGBT as sub")
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

    # LPGBT LED Show
    try:
        main(args.system, boss)
    except KeyboardInterrupt:
        print (Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()

