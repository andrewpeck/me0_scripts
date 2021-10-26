from rw_reg_lpgbt import *
from time import sleep, time
import sys
import argparse
import csv
import matplotlib.pyplot as plt
import os
import datetime

def main(system, oh_v, boss, device, rate, offset, run_time_min, gain):

    # PT-100 is an RTD (Resistance Temperature Detector) sensor
    # PT (ie platinum) has linear temperature-resistance relationship
    # RTD sensors made of platinum are called PRT (Platinum Resistance Themometer)

    init_adc()

    if system == "dryrun":
        F = 1
    else:
        if oh_v == 2:
            channel = 3 #servant_adc_in3
            F = calculate_F(channel, gain, system)

    if device == "OH":
        channel = 6
        DAC = 50
    else:
        channel = 0
        DAC = 20

    LSB = 3.55e-06
    I = DAC * LSB

    reg_data = convert_adc_reg(channel)
    writeReg(getNode("LPGBT.RWF.VOLTAGE_DAC.CURDACENABLE "), 0x1, 0)  # Enables current DAC.
    writeReg(getNode("LPGBT.RWF.CUR_DAC.CURDACCHNENABLE"), reg_data, 0)
    writeReg(getNode("LPGBT.RWF.CUR_DAC.CURDACSELECT"), convert_adc_reg(DAC),
             0)  # Sets output current for the current DAC.
    sleep(0.01)

    print("Temperature Readings:")

    if not os.path.exists("lpgbt_data/lpgbt_temp_data"):
        os.makedirs("lpgbt_data/lpgbt_temp_data")

    now = str(datetime.datetime.now())[:16]
    now = now.replace(":", "_")
    now = now.replace(" ", "_")
    foldername = "lpgbt_data/lpgbt_temp_data/"
    filename = foldername + "temp_" + device + "_data" + now + ".txt"

    print(filename)
    open(filename, "w+").close()
    minutes, seconds, T, R = [], [], [], []

    run_time_min = float(run_time_min)

    # Set figure paramete
    fig, ax = plt.subplots()
    ax.set_xlabel('minutes')
    ax.set_ylabel('R (Ohms)')

    start_time = int(time())
    end_time = int(time()) + (60 * run_time_min)

    while int(time()) <= end_time:
        with open(filename, "a") as file:
            V_m = F * read_adc(channel, gain, system)
            R_m = V_m/I

            temp = (R_m-offset)/rate

            second = time() - start_time
            seconds.append(second)
            T.append(temp)
            R.append(R_m)
            minutes.append(second/60)
            live_plot(ax, minutes, R)

            file.write(str(second) + "\t" + str(R_m)+ "\t" + str(temp) + "\n" )
            print("\tch %X: 0x%03X = %f (R (Ohms))" % (channel, V_m, R_m))
            sleep(1)

    figure_name = foldername + "temp_" + device + now + "_plot.pdf"
    fig.savefig(figure_name, bbox_inches="tight")

    writeReg(getNode("LPGBT.RWF.VOLTAGE_DAC.CURDACENABLE"), 0x0, 0)  #Enables current DAC.
    writeReg(getNode("LPGBT.RWF.CUR_DAC.CURDACSELECT"), 0x0, 0)  #Sets output current for the current DAC.
    writeReg(getNode("LPGBT.RWF.CUR_DAC.CURDACCHNENABLE"), 0x0, 0)
    sleep(0.01)

    powerdown_adc()

def convert_adc_reg(gpio):
    reg_data = 0
    if gpio <= 7:
        bit = gpio
    else:
        bit = gpio - 8
    reg_data |= (0x01 << bit)
    return reg_data

def calculate_F(channel, gain, system):

    R= 1e-03
    LSB = 3.55e-06
    DAC = 150

    I = DAC * LSB
    V = I * R

    reg_data = convert_adc_reg(channel)

    writeReg(getNode("LPGBT.RWF.VOLTAGE_DAC.CURDACENABLE "), 0x1, 0)  #Enables current DAC.
    writeReg(getNode("LPGBT.RWF.CUR_DAC.CURDACSELECT"), convert_adc_reg(DAC), 0)  #Sets output current for the current DAC.
    writeReg(getNode("LPGBT.RWF.CUR_DAC.CURDACCHNENABLE"), reg_data, 0)
    sleep(0.01)

    V_m = read_adc(channel, gain, system)
    F = V/V_m

    writeReg(getNode("LPGBT.RWF.VOLTAGE_DAC.CURDACENABLE "), 0x0, 0)  #Enables current DAC.
    writeReg(getNode("LPGBT.RWF.CUR_DAC.CURDACSELECT"), 0x0, 0)  #Sets output current for the current DAC.
    writeReg(getNode("LPGBT.RWF.CUR_DAC.CURDACCHNENABLE"), 0x0, 0)
    sleep(0.01)

    return F

def live_plot(ax, x, y):
    ax.plot(x, y, "turquoise")
    plt.draw()
    plt.pause(0.01)

def init_adc(): ########## Not sure which ones are unnecesary, so I left them all here
    writeReg(getNode("LPGBT.RW.ADC.ADCENABLE"), 0x1, 0)  # enable ADC
    writeReg(getNode("LPGBT.RW.ADC.TEMPSENSRESET"), 0x1, 0)  # resets temp sensor
    writeReg(getNode("LPGBT.RW.ADC.VDDMONENA"), 0x1, 0)  # enable dividers
    writeReg(getNode("LPGBT.RW.ADC.VDDTXMONENA"), 0x1, 0)  # enable dividers
    writeReg(getNode("LPGBT.RW.ADC.VDDRXMONENA"), 0x1, 0)  # enable dividers
    writeReg(getNode("LPGBT.RW.ADC.VDDANMONENA"), 0x1, 0)  # enable dividers
    writeReg(getNode("LPGBT.RWF.CALIBRATION.VREFENABLE"), 0x1, 0)  # vref enable
    writeReg(getNode("LPGBT.RWF.CALIBRATION.VREFTUNE"), 0x63, 0) # vref tune
    sleep(0.01)

def powerdown_adc():    ######## Same here
    writeReg(getNode("LPGBT.RW.ADC.ADCENABLE"), 0x0, 0)  # disable ADC
    writeReg(getNode("LPGBT.RW.ADC.TEMPSENSRESET"), 0x0, 0)  # disable temp sensor
    writeReg(getNode("LPGBT.RW.ADC.VDDMONENA"), 0x0, 0)  # disable dividers
    writeReg(getNode("LPGBT.RW.ADC.VDDTXMONENA"), 0x0, 0)  # disable dividers
    writeReg(getNode("LPGBT.RW.ADC.VDDRXMONENA"), 0x0, 0)  # disable dividers
    writeReg(getNode("LPGBT.RW.ADC.VDDANMONENA"), 0x0, 0)  # disable dividers
    writeReg(getNode("LPGBT.RWF.CALIBRATION.VREFENABLE"), 0x0, 0)  # vref disable
    writeReg(getNode("LPGBT.RWF.CALIBRATION.VREFTUNE"), 0x0, 0) # vref tune

def read_adc(channel, gain, system):

    writeReg(getNode("LPGBT.RW.ADC.ADCINPSELECT"), channel, 0)
    writeReg(getNode("LPGBT.RW.ADC.ADCINNSELECT"), 0xf, 0)

    gain_settings = {
        2: 0x00,
        8: 0x01,
        16: 0x10,
        32: 0x11
    }
    writeReg(getNode("LPGBT.RW.ADC.ADCGAINSELECT"), gain_settings[gain], 0)
    writeReg(getNode("LPGBT.RW.ADC.ADCCONVERT"), 0x1, 0)

    done = 0
    while (done == 0):
        if system != "dryrun":
            done = readReg(getNode("LPGBT.RO.ADC.ADCDONE"))
        else:
            done = 1

    val = readReg(getNode("LPGBT.RO.ADC.ADCVALUEL"))
    val |= (readReg(getNode("LPGBT.RO.ADC.ADCVALUEH")) << 8)

    writeReg(getNode("LPGBT.RW.ADC.ADCCONVERT"), 0x0, 0)
    writeReg(getNode("LPGBT.RW.ADC.ADCGAINSELECT"), 0x0, 0)
    writeReg(getNode("LPGBT.RW.ADC.ADCINPSELECT"), 0x0, 0)
    writeReg(getNode("LPGBT.RW.ADC.ADCINNSELECT"), 0x0, 0)

    return val

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="ADC Precision Calibration Scan for ME0 Optohybrid")
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle or dryrun")
    parser.add_argument("-y", "--oh_v", action="store", dest="oh_v", default="2", help="oh_v = 2 (no precision calibration for oh_v1)")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = sub")
    parser.add_argument("-t", "--temp", action="store", dest="temp", help="temp = OH or VTRX")
    parser.add_argument("-r", "--rate", action="store", dest="rate", default="0.385", help="rate = rate of change of R w.r.t T")
    parser.add_argument("-b", "--b", action="store", dest="b", default="100", help="b = temperature offset at 0C")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1 (only needed for backend)")
    parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 1, 3, 5 or 7 (only needed for backend)")
    parser.add_argument("-m", "--minutes", action="store", dest="minutes", help="minutes = int. # of minutes you want to run")  
    parser.add_argument("-a", "--gain", action="store", dest="gain", default = "2", help="gain = Gain for RSSI ADC: 2, 8, 16, 32")
    args = parser.parse_args()

    if args.system == "chc":
        print("Using Rpi CHeeseCake to scan the precision calibration constant")
    elif args.system == "backend":
        # print ("Using Backend for rssi monitoring")
        print(Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun supported at the moment" + Colors.ENDC)
        sys.exit()
    elif args.system == "dongle":
        # print ("Using USB Dongle for rssi monitoring")
        print(Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun supported at the moment" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print("Dry Run - not actually running rssi monitoring")
    else:
        print(Colors.YELLOW + "Only valid options: chc, backend, dongle, dryrun" + Colors.ENDC)
        sys.exit()

    boss = None
    if args.oh_v == "2":
        print("Using OH v2")
        oh_v = 2
        if args.lpgbt is None:
            print (Colors.YELLOW + "Please select sub" + Colors.ENDC)
            sys.exit()
        elif (args.lpgbt=="boss"):
            print ("Only sub has a temperature sensor")
            sys.exit()
        elif (args.lpgbt=="sub"):
            print ("Using sub LpGBT")
            boss=0
        else:
            print(Colors.YELLOW + "Please select sub" + Colors.ENDC)
            sys.exit()
    elif args.oh_v == "1":
            print (Colors.YELLOW + "No temperature sensor in OH v1" + Colors.ENDC)
            sys.exit()
    else:
        print(Colors.YELLOW + "Please select OH v2" + Colors.ENDC)
        sys.exit
    if boss is None:
        sys.exit()

    if args.temp is None:
        print(Colors.YELLOW + "Please select OH or VTRX" + Colors.ENDC)
        sys.exit()
    elif args.temp != "OH" and args.temp != "VTRX":
        print(Colors.YELLOW + "Please select OH or VTRX" + Colors.ENDC)
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

    if args.gain not in ["2", "8", "16", "32"]:
        print(Colors.YELLOW + "Allowed values of gain = 2, 8, 16, 32" + Colors.ENDC)
        sys.exit()
    gain = int(args.gain)

    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML(oh_v)
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system, boss, args.ohid, args.gbtid)
    print("Initialization Done\n")

    # Readback rom register to make sure communication is OK
    if args.system != "dryrun" and args.system != "backend":
        check_rom_readback()

    # Check if lpGBT is READY if running through backend
    if args.system=="backend":
        check_lpgbt_link_ready(args.ohid, args.gbtid)
    else:
        check_lpgbt_ready()

    try:
        main(args.system, oh_v, boss, args.temp, float(args.rate), float(args.b), args.minutes, gain)
    except KeyboardInterrupt:
        print(Colors.RED + "\nKeyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print(Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()
