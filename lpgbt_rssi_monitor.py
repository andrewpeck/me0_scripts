from rw_reg_lpgbt import *
from time import sleep, time
import sys
import argparse
import csv
import matplotlib.pyplot as plt
import os
import datetime

def main(system, boss, run_time_min, gain, voltage, oh_v):

    init_adc()

    if oh_v == 2:
        F = calculate_F(gain, system)
    else:
        F = 1
    
    print("ADC Readings:")

    if not os.path.exists("lpgbt_data/lpgbt_vtrx+_rssi_data"):
        os.makedirs("lpgbt_data/lpgbt_vtrx+_rssi_data")

    now = str(datetime.datetime.now())[:16]
    now = now.replace(":", "_")
    now = now.replace(" ", "_")
    foldername = "lpgbt_data/lpgbt_vtrx+_rssi_data/"
    filename = foldername + "rssi_data_" + now + ".txt"

    print(filename)
    open(filename, "w+").close()
    minutes, seconds, rssi = [], [], []

    run_time_min = float(run_time_min)

    fig, ax = plt.subplots()
    ax.set_xlabel("minutes")
    ax.set_ylabel("RSSI (uA)")
    #ax.set_xticks(range(0,run_time_min+1))
    #ax.set_xlim([0,run_time_min])

    start_time = int(time())
    end_time = int(time()) + (60 * run_time_min)

    while int(time()) <= end_time:
        with open(filename, "a") as file:
            if oh_v == 1:
                value = read_adc(7, gain, system)
            if oh_v == 2:
                value = read_adc(5, gain, system)
            rssi_current = rssi_current_conversion(value, gain, voltage, oh_v) * 1e6 # in uA
            second = time() - start_time
            seconds.append(second)
            rssi.append(rssi_current)
            minutes.append(second/60)
            live_plot(ax, minutes, rssi)

            file.write(str(second) + "\t" + str(rssi_current) + "\n" )
            print("\tch %X: 0x%03X = %f (RSSI (uA))" % (7, value, rssi_current))

            sleep(1)

    figure_name = foldername + "rssi_data_" + now + "_plot.pdf"
    fig.savefig(figure_name, bbox_inches="tight")

    powerdown_adc()

def calculate_F_from_DAC_range(gain, system):

    # For sub: adc channel = 3
    R_111 = 1e-03

    XX = 3.55e-06
    DAC_range = range(50, 200, 5)
    
    writeReg(getNode("LPGBT.RWF.VOLTAGE_DAC.CURDACENABLE "), 0x1, 0)  #Enables current DAC.

    fig_F, ax_F = plt.subplots()
    ax_F.set_xlabel("DAC")
    ax_F.set_ylabel("F=V/V_m")

    F_range = []
    for DAC in DAC_range:
        
        I = DAC * XX
        V = I * R_111

        writeReg(getNode("LPGBT.RWF.CUR_DAC.CURDACSELECT"), hex(DAC), 0)  #Sets output current for the current DAC.
        writeReg(getNode("LPGBT.RWF.CUR_DAC.CURDACCHNENABLE"), 0x80, 0) 
        sleep(0.01)
        
        V_m = read_adc(3, gain, system)
        F = V/V_m
        F_range.append(F)

    live_plot(ax_F, DAC_range, F_range)    

def calculate_F(gain, system):

    # For sub: adc channel = 3
    R_111 = 1e-03

    XX = 3.55e-06
    DAC = 150

    I = DAC * XX
    V = I * R_111

    writeReg(getNode("LPGBT.RWF.VOLTAGE_DAC.CURDACENABLE "), 0x1, 0)  #Enables current DAC.
    writeReg(getNode("LPGBT.RWF.CUR_DAC.CURDACSELECT"), 0x96, 0)  #Sets output current for the current DAC.
    writeReg(getNode("LPGBT.RWF.CUR_DAC.CURDACCHNENABLE"), 0x80, 0)
    sleep(0.01)

    V_m = read_adc(7, gain, system)

    F = V/V_m

    return F


def live_plot(ax, x, y):
    ax.plot(x, y, "turquoise")
    plt.draw()
    plt.pause(0.01)

def init_adc():
    writeReg(getNode("LPGBT.RW.ADC.ADCENABLE"), 0x1, 0)  # enable ADC
    writeReg(getNode("LPGBT.RW.ADC.TEMPSENSRESET"), 0x1, 0)  # resets temp sensor
    writeReg(getNode("LPGBT.RW.ADC.VDDMONENA"), 0x1, 0)  # enable dividers
    writeReg(getNode("LPGBT.RW.ADC.VDDTXMONENA"), 0x1, 0)  # enable dividers
    writeReg(getNode("LPGBT.RW.ADC.VDDRXMONENA"), 0x1, 0)  # enable dividers
    writeReg(getNode("LPGBT.RW.ADC.VDDANMONENA"), 0x1, 0)  # enable dividers
    writeReg(getNode("LPGBT.RWF.CALIBRATION.VREFENABLE"), 0x1, 0)  # vref enable
    writeReg(getNode("LPGBT.RWF.CALIBRATION.VREFTUNE"), 0x63, 0) # vref tune
    sleep(0.01)

def powerdown_adc():
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

def rssi_current_conversion(rssi_adc, gain, input_voltage, oh_v):

    rssi_current = -9999
    rssi_adc_converted = 1.0 * (rssi_adc/1024.0) # 10-bit ADC, range 0-1 V
    #rssi_voltage = rssi_adc_converted/gain # Gain
    rssi_voltage = rssi_adc_converted

    if oh_v == 1:
        # Resistor values
        R1 = 4.7 * 1000 # 4.7 kOhm
        v_r = rssi_voltage
        rssi_current = (input_voltage - v_r)/R1 # rssi current
    elif oh_v == 2:
        # Resistor values
        R1 = 4.7 * 1000 # 4.7 kOhm
        R2 = 1000.0 * 1000 # 1 MOhm
        R3 = 470.0 * 1000 # 470 kOhm
        v_r = rssi_voltage * ((R2+R3)/R3) # voltage divider
        rssi_current = (input_voltage - v_r)/R1 # rssi current

    return rssi_current

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="RSSI Monitor for ME0 Optohybrid")
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle or dryrun")
    parser.add_argument("-y", "--oh_v", action="store", dest="oh_v", default="1", help="oh_v = 1 or 2")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = only boss for oh_v1 and only sub for oh_v2")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1 (only needed for backend)")
    parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0-7 (only needed for backend)")
    parser.add_argument("-v", "--voltage", action="store", dest="voltage", default = "2.5", help="voltage = exact value of the 2.5V input voltage to OH")
    parser.add_argument("-m", "--minutes", action="store", dest="minutes", help="minutes = int. # of minutes you want to run")
    parser.add_argument("-a", "--gain", action="store", dest="gain", default = "2", help="gain = Gain for RSSI ADC: 2, 8, 16, 32")
    args = parser.parse_args()

    if args.system == "chc":
        print("Using Rpi CHeeseCake for rssi monitoring")
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
    if args.oh_v == "1":
        print("Using OH v1")
        oh_v = 1
        if args.lpgbt is None or args.lpgbt != "boss" or args.lpgbt != "sub":
            print(Colors.YELLOW + "Please select boss." + Colors.ENDC)
            sys.exit()
        elif args.lpgbt == "boss":
            print("Using boss LPGBT")
            boss = 1
        elif args.lpgbt == "sub":
            print(Colors.YELLOW + "Only boss allowed oh_v1" + Colors.ENDC)
            sys.exit()
    elif args.oh_v == "2":
        print("Using OH v2")
        oh_v = 2
        if args.lpgbt is None or args.lpgbt != "boss" or args.lpgbt != "sub":
            print(Colors.YELLOW + "Please select sub" + Colors.ENDC)
            sys.exit()
        elif args.lpgbt == "boss":
            print(Colors.YELLOW + "Only sub allowed oh_v2" + Colors.ENDC)
            sys.exit()
        elif args.lpgbt == "sub":
            print("Using sub LPGBT")
            boss = 0
    else:
        print(Colors.YELLOW + "Please select either OH v1 or v2" + Colors.ENDC)
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
        main(args.system, boss, args.minutes, gain, int(args.voltage), oh_v)
    except KeyboardInterrupt:
        print(Colors.RED + "\nKeyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print(Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()
