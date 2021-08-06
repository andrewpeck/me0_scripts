from rw_reg_lpgbt import *
from time import time, sleep
import sys
import os
import argparse
from lpgbt_vtrx import i2cmaster_write, i2cmaster_read
from lpgbt_rssi_monitor import rssi_current_conversion, read_adc, init_adc, powerdown_adc
import matplotlib.pyplot as plt
import datetime

vtrx_slave_addr = 0x50

# VTRX+ registers
TX_reg = {}
TX_reg["TX1"] = {"biascur_reg": 0x03, "modcur_reg": 0x04, "empamp_reg": 0x05}
TX_reg["TX2"] = {"biascur_reg": 0x06, "modcur_reg": 0x07, "empamp_reg": 0x08}
TX_reg["TX3"] = {"biascur_reg": 0x09, "modcur_reg": 0x0A, "empamp_reg": 0x0B}
TX_reg["TX4"] = {"biascur_reg": 0x0C, "modcur_reg": 0x0D, "empamp_reg": 0x0E}

enable_reg = 0x00
TX_enable_bit = {}
TX_enable_bit["TX1"] = 0
TX_enable_bit["TX2"] = 1
TX_enable_bit["TX3"] = 2
TX_enable_bit["TX4"] = 3

i2c_master_timeout = 1  # 1s

def main(system, boss, channel, name, reg, upper, lower, gain):
    if not boss:
        print(
            Colors.RED + "ERROR: VTRX+ control only for boss since I2C master of boss connected to VTRX+" + Colors.ENDC)
        return

    print("Enabling channel: " + channel)
    # Enabling TX Channel
    if channel is not None:
        if system != "backend":
            enable_status = i2cmaster_read(system, enable_reg)
        else:
            enable_status = 0x00

        en = 0
        en = 1
        enable_channel_bit = TX_enable_bit[channel]
        enable_mask = (1 << enable_channel_bit)
        enable_data = (enable_status & (~enable_mask)) | (en << enable_channel_bit)
        enable_status = enable_data
        i2cmaster_write(system, enable_reg, enable_data)
        if system != "backend":
            enable_status = i2cmaster_read(system, enable_reg)
        else:
            enable_status = 0x00
        print("")

    # Reading Initial Bias value
    print ("Initial register value:")
    initial_bias = i2cmaster_read(system, reg)
    print ("")

    # Starting bias scan
    init_adc()
    rssi_array, bias_array = [], []
    
    if not os.path.exists("bias_rssi_scan"):
        os.makedirs("bias_rssi_scan")
    now = str(datetime.datetime.now())[:16]
    now = now.replace(":", "_")
    now = now.replace(" ", "_")
    foldername = "bias_rssi_scan/"
    filename = foldername + "bias_rssi_scan_" + now + ".txt"
    out_file = open(filename,"w+")
    out_file.write("# %s  RSSI\n" %(name))
    
    print ("Starting bias scan for channel %s for register %s: \n" %(channel, name))
    for i in range(lower, upper+1):

        if name=="modcur_reg":
            i |= 0x80 # to include the enable

        # Writing bias registers
        i2cmaster_write(system, reg, i)

        # Reading RSSI
        rssi = read_adc(7, gain, system) # RSSI - ADC channel 7
        rssi_current = rssi_current_conversion(rssi, gain) * 1e6 # in uA

        rssi_array.append(rssi_current)
        bias_array.append(i)
        print ("%s=0x%02X: RSSI=%f (uA)\n" %(name, i, rssi_current))
        out_file.write("0x%02X  %f\n" %(i, rssi_current))

    powerdown_adc()
    out_file.close()
    
    #fig, ax = plt.subplots()
    #ax.set_xlabel("Hex")
    #ax.set_ylabel("RSSI")
    #plt.plot(data_array, rssi_array)
    #plt.show()

    # Setting back the bias to the initial value
    print ("Setting back initial register value:")
    i2cmaster_write(system, reg, initial_bias)
    print ("")

if __name__ == "__main__":
    # Parsing arguments
    parser = argparse.ArgumentParser(description="LPGBT VTRX+ CONTROL")
    parser.add_argument("-s", "--system", action="store", dest="system",
                        help="system = chc or backend or dongle or dryrun")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = only boss allowed")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1 (only needed for backend)")
    parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0-7 (only needed for backend)")
    parser.add_argument("-c", "--channel", action="store", dest="channel", help="channel = TX1, TX2, TX3, TX4")
    parser.add_argument("-n", "--name", action="store", dest="name", help="name = biascur_reg, modcur_reg")
    parser.add_argument("-ll", "--lower_limit", action="store", dest="lower_limit", help="lower limit, enter in 0x (hex) format")
    parser.add_argument("-ul", "--upper_limit", action="store", dest="upper_limit", help="upper limit, enter in 0x (hex) format")
    parser.add_argument("-a", "--gain", action="store", dest="gain", default = "2", help="gain = Gain for RSSI ADC: 2, 8, 16, 32")
    args = parser.parse_args()

    if args.system == "chc":
        print("Using Rpi CHeeseCake for checking configuration")
    elif args.system == "backend":
        #print("Using Backend for checking configuration")
        print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        # sys.exit()
    elif args.system == "dongle":
        # print ("Using USB Dongle for checking configuration")
        print(Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun supported at the moment" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print("Dry Run - not actually running on lpGBT")
    else:
        print(Colors.YELLOW + "Only valid options: chc, backend, dongle, dryrun" + Colors.ENDC)
        sys.exit()

    boss = None
    if args.lpgbt is None:
        print(Colors.YELLOW + "Please select boss" + Colors.ENDC)
        sys.exit()
    elif (args.lpgbt == "boss"):
        print("VTRX+ control for boss")
        boss = 1
    elif (args.lpgbt == "sub"):
        print(Colors.YELLOW + "VTRX+ control only for boss since I2C master of boss connected to VTRX+" + Colors.ENDC)
        boss = 0
        sys.exit()
    else:
        print(Colors.YELLOW + "Please select boss" + Colors.ENDC)
        sys.exit()
    if boss is None:
        sys.exit()

    if args.system == "backend":
        if args.ohid is None:
            print(Colors.YELLOW + "Need OHID for backend" + Colors.ENDC)
            sys.exit()
        if args.gbtid is None:
            print(Colors.YELLOW + "Need GBTID for backend" + Colors.ENDC)
            sys.exit()
        if int(args.ohid) > 1:
            print(Colors.YELLOW + "Only OHID 0-1 allowed" + Colors.ENDC)
            sys.exit()
        if int(args.gbtid) > 7:
            print(Colors.YELLOW + "Only GBTID 0-7 allowed" + Colors.ENDC)
            sys.exit()
    else:
        if args.ohid is not None or args.gbtid is not None:
            print(Colors.YELLOW + "OHID and GBTID only needed for backend" + Colors.ENDC)
            sys.exit()

    if args.channel == None:
        print(Colors.YELLOW + "Enter channel" + Colors.ENDC)
        sys.exit()
    if args.channel not in ["TX1", "TX2", "TX3", "TX4"]:
        print(Colors.YELLOW + "Only allowed channels: TX1, TX2, TX3, TX4" + Colors.ENDC)
        sys.exit()
    if args.name not in ["biascur_reg", "modcur_reg"]:
        print(Colors.YELLOW + "Invalid register name" + Colors.ENDC)
        sys.exit()
    reg = TX_reg[args.channel][args.name]
    
    if args.upper_limit is None:
        print(Colors.YELLOW + "Enter upper limit for scan" + Colors.ENDC)
        sys.exit()
    if args.lower_limit is None:
        print(Colors.YELLOW + "Enter lower limit for scan" + Colors.ENDC)
        sys.exit()
        
    ul = int(args.upper_limit, 16)
    ll = int(args.lower_limit, 16)
    if ul > 127:
        print(Colors.YELLOW + "Upper limit value can only be 7 bit" + Colors.ENDC)
        sys.exit() 
    if ll > 127:
        print(Colors.YELLOW + "Lower limit value can only be 7 bit" + Colors.ENDC)
        sys.exit()   
    if ll>ul:
        print(Colors.YELLOW + "Upper limit has to be larger tha lower limit" + Colors.ENDC)
        sys.exit() 

    if args.gain not in ["2", "8", "16", "32"]:
        print(Colors.YELLOW + "Allowed values of gain = 2, 8, 16, 32" + Colors.ENDC)
        sys.exit()
    gain = int(args.gain)

    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML()
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system, boss, args.ohid, args.gbtid)
    print("Initialization Done\n")

    # Readback rom register to make sure communication is OK
    if args.system != "dryrun" and args.system != "backend":
        check_rom_readback()

    # Check if lpGBT link is READY if running through backend
    # if args.system=="backend":
    #    check_lpgbt_link_ready(args.ohid, args.gbtid)

    try:
        main(args.system, boss, args.channel, args.name, reg, ul, ll, gain)
    except KeyboardInterrupt:
        print(Colors.RED + "\nKeyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print(Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()

