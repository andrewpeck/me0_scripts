from rw_reg_lpgbt import *
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib import cm
import numpy as np
import os, sys, glob
import argparse

def getCalData(calib_path):
    slope_adc = {}
    intercept_adc = {}

    if os.path.isfile(calib_path):
        calib_file = open(calib_path)
        for line in calib_file.readlines():
            vfat = int(line.split(";")[0])
            slope_adc[vfat] = float(line.split(";")[2])
            intercept_adc[vfat] = float(line.split(";")[3])
        calib_file.close()

    return slope_adc, intercept_adc

def DACToCharge(dac, slope_adc, intercept_adc, vfat, mode):
    """
    Slope and intercept for all VFATs from the CAL_DAC cal file.
    If cal file not present, use default values here are a rough average of cal data.
    """

    slope = -9999
    intercept = -9999

    if vfat in slope_adc:
        if slope_adc[vfat]!=-9999 and intercept_adc[vfat]!=-9999:
            if mode=="voltage":
                slope = slope_adc[vfat]
                intercept = intercept_adc[vfat]
            elif mode=="current":
                slope = abs(slope_adc[vfat])
                intercept = 0
    if slope==-9999 or intercept==-9999: # use average values
        print (Colors.YELLOW + "ADC Cal data not present for VFAT%d, using avergae values"%vfat + Colors.ENDC)
        if mode=="voltage":
            slope = -0.22 # fC/DAC
            intercept = 56.1 # fC
        elif mode=="current":
            slope = 0.22 # fC/DAC
            intercept = 0
    charge = (dac * slope) + intercept
    return charge

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="Plotting VFAT SCurve")
    parser.add_argument("-f", "--filename", action="store", dest="filename", help="SCurve result filename")
    #parser.add_argument("-t", "--type", action="store", dest="type", help="type = daq or sbit")
    parser.add_argument("-m", "--mode", action="store", dest="mode", help="mode = voltage or current")
    parser.add_argument("-c", "--channels", action="store", nargs="+", dest="channels", help="Channels to plot for each VFAT")
    args = parser.parse_args()

    if args.channels is None:
        print(Colors.YELLOW + "Enter channel list to plot SCurves" + Colors.ENDC)
        sys.exit()

    if args.mode not in ["voltage", "current"]:
        print(Colors.YELLOW + "Mode can only be voltage or current" + Colors.ENDC)
        sys.exit()

    #if args.type not in ["daq", "sbit"]:
    #    print(Colors.YELLOW + "Type can only be daq or sbit" + Colors.ENDC)
    #    sys.exit()

    directoryName        = args.filename.split(".txt")[0]
    plot_filename_prefix = (directoryName.split("/"))[2]
    oh = plot_filename_prefix.split("_vfat")[0]
    file = open(args.filename)

    try:
        os.makedirs(directoryName) # create directory for scurve analysis results
    except FileExistsError: # skip if directory already exists
        pass

    calib_path = "vfat_data/vfat_calib_data/"+oh+"_vfat_calib_info_calDac.txt"
    slope_adc, intercept_adc = getCalData(calib_path)

    scurve_result = {}
    for line in file.readlines():
        if "vfat" in line:
            continue

        vfat    = int(line.split()[0])
        channel = int(line.split()[1])
        charge  = int(line.split()[2])
        fired   = int(line.split()[3])
        events  = int(line.split()[4])

        #if args.mode == "voltage":
        #    charge = 255 - charge
        charge = DACToCharge(charge, slope_adc, intercept_adc, vfat, args.mode) # convert to fC

        if vfat not in scurve_result:
            scurve_result[vfat] = {}
        if channel not in scurve_result[vfat]:
            scurve_result[vfat][channel] = {}
        if fired == -9999 or events == -9999 or events == 0:
            scurve_result[vfat][channel][charge] = 0
        else:
            scurve_result[vfat][channel][charge] = float(fired)/float(events)
    file.close()

    channelNum = np.arange(0, 128, 1)
    chargeVals = np.arange(0, 256, 1)
    for vfat in scurve_result:
        fig, axs = plt.subplots()
        plt.xlabel("Channel Number")
        plt.ylabel("Injected Charge (fC)")
        #plt.xlim(0,128)
        #plt.ylim(0,256)

        plot_data = []
        for dac in range(0,256):
            charge = DACToCharge(dac, slope_adc, intercept_adc, vfat, args.mode)
            data = []
            for channel in range(0,128):
                if channel not in scurve_result[vfat]:
                    data.append(0)
                elif charge not in scurve_result[vfat][channel]:
                    data.append(0)
                else:
                    data.append(scurve_result[vfat][channel][charge])
            plot_data.append(data)

        chargeVals_mod = chargeVals
        for i in range(0,len(chargeVals_mod)):
            chargeVals_mod[i] = DACToCharge(chargeVals_mod[i], slope_adc, intercept_adc, vfat, args.mode)
        plot = axs.imshow(plot_data, extent=[min(channelNum), max(channelNum), min(chargeVals_mod), max(chargeVals_mod)], origin="lower",  cmap=cm.ocean_r,interpolation="nearest", aspect="auto")
        cbar = fig.colorbar(plot, ax=axs, pad=0.01)
        cbar.set_label("Fired Events / Total Events")
        plt.title("VFAT# %02d"%vfat)
        plt.savefig((directoryName+"/_scurve2Dhist_"+oh+"_VFAT%02d.pdf")%vfat)

    for vfat in scurve_result:
        fig, ax = plt.subplots()
        plt.xlabel("Injected Charge (fC)")
        plt.ylabel("Fired Events / Total Events")
        #if args.type == "daq":
        #    plt.ylim(-0.1,1.1)
        #else:
        #    plt.ylim(-0.1,2.1)
        for channel in args.channels:
            channel = int(channel)
            if channel not in scurve_result[vfat]:
                print (Colors.YELLOW + "Channel %d not in SCurve scan"%channel + Colors.ENDC)
                continue
            dac = range(0,256)
            charge_plot = []
            frac = []
            for d in dac:
                c = DACToCharge(d, slope_adc, intercept_adc, vfat, args.mode)
                if c in scurve_result[vfat][channel]:
                    charge_plot.append(c)
                    frac.append(scurve_result[vfat][channel][c])
            ax.plot(charge_plot, frac, "o", label="Channel %d"%channel)
        leg = ax.legend(loc="center right", ncol=2)
        plt.title("VFAT# %02d"%vfat)
        plt.savefig((directoryName+"/scurve_"+oh+"_VFAT%02d.pdf")%vfat)










