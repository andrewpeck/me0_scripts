import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib import cm
import numpy as np
import os, sys, glob
import argparse
from scipy.optimize import curve_fit
from scipy.special import erf
from math import sqrt
from tqdm import tqdm
import warnings

plt.rcParams.update({"font.size": 22}) # Increase font size

def dictToArray(dictionary, vfatNumber, channel):
    """
    Returns (256, 2) ndarray.
    column 0 = injected charge
    column 1 = ratio of fired events / total events
    """
    return np.array(list(dictionary[vfatNumber][channel].items()))

def scurveFunc(injCharge, A, ch_pedestal, mean, sigma):
    """
    Modified error function.
    injCharge = injected charge
    """
    
    pedestal = np.zeros(256)
    if ch_pedestal > 0.0:
        pedestal.fill(ch_pedestal)
        
    maxCharge = np.maximum(pedestal, injCharge)

    return A * erf(np.true_divide((maxCharge - mean), sigma * sqrt(2))) + A

def getCalData(calib_path):
    slope_adc = {}
    intercept_adc = {}

    if os.path.isfile(calib_path):
        calib_file = open(calib_path)
        for line in calib_file.readlines():
            if "vfat" in line:
                continue
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

def fit_scurve(vfatList, scurve_result, oh, directoryName, verbose , channel_list):
    vfatCounter   = 0 
    scurveParams = np.ndarray((len(vfatList), 128, 2))

    for vfat in vfatList:
        print("Fitting data for VFAT%2d" % vfat)
        fitFileName = directoryName + "/fitResults_" + oh + ("_VFAT%02d" % vfat) + ".txt"
        file_out = open(fitFileName, "w+")
        file_out.write("========= Results for VFAT%2d =========\n" % vfat)
        print("========= Processing data for VFAT%2d =========\n" % vfat)
        file_out.write("Channel    Mean    ENC\n")
            
        for channel in tqdm(range(128)):
            scurveData      = dictToArray(scurve_result, vfat, channel) # transfer data from dictionary to array
        
            params, covMatrix = curve_fit(scurveFunc, scurveData[:,0], scurveData[:,1], p0=[1, 0, 60, 0.4], maxfev=100000) # fit data; returns optimized parameters and covariance matrix
            
            file_out.write("%d    %.4f    %.4f \n" % (channel, params[2], params[3]))
            scurveParams[vfatCounter, channel, 0] = params[3] # store channel ENC
            scurveParams[vfatCounter, channel, 1] = params[2] # store channel mean
            
            if verbose == True:
                print("Channel %i Average ENC: %.4f " % (channel, scurveParams[vfatCounter, channel, 0]))
                print("Channel %i Average mean: %.4f " % (channel, scurveParams[vfatCounter, channel, 1]))
            else:
                pass

            try:
                os.makedirs(directoryName+"/scurveFit_"+oh+"_VFAT%d"%(vfat))
            except FileExistsError:
                pass

            if channel in channel_list:
                fig, ax = plt.subplots(figsize = (16,10))
                plt.xlabel("Charge (fC)")
                plt.ylabel("Fired Events / Total Events")
                ax.plot(scurveData[:,0], scurveData[:,1], "o", markersize= 6, label = "Channel %d" % channel) # plot raw data
                ax.plot(scurveData[:,0], scurveFunc(scurveData[:,0], *params), "r-", label="fit")
                props = dict(boxstyle="round", facecolor="white",edgecolor="lightgrey", alpha=1)
                textstr = "\n".join((
                    r"Threshold: $\mu=%.4f$ (fC)" % (params[2], ),
                    r"ENC: $\sigma=%.4f$ (fC)" % (params[3], ),))
                ax.text(0.663, 0.7, textstr, transform=ax.transAxes, fontsize=22, verticalalignment="top", bbox=props)
                ax.set_title("VFAT0%d" % vfat)
                leg = ax.legend(loc="center right", ncol=2)
                plt.grid()
                fig.tight_layout()
                plt.savefig(directoryName + "/scurveFit_"+oh+"_VFAT%d/"%(vfat)+"scurveFit_"+oh+"_VFAT%d_channel%d.pdf" % (vfat, channel))
                plt.close() # clear the plot
            else:
                pass
        
        # average values for all channels    
        avgENC = np.average(scurveParams[vfatCounter, :, 0])
        avgMean = np.average(scurveParams[vfatCounter, :, 1])


        print("========= Summary =========\n")
        print("Average ENC: %.4f (fC)" % avgENC)
        print("Average mean (threshold): %.4f (fC)" % avgMean)

        file_out.write("========= Summary =========\n")
        file_out.write("Average ENC: %.4f (fC)\n" % avgENC)
        file_out.write("Average mean (threshold): %.4f (fC)\n" % avgMean)

        file_out.close()
        print("Results for VFAT%0d saved in %s\n" % (vfat, fitFileName))
        vfatCounter += 1
        
    return scurveParams

def plotENCdistributions(vfatList, scurveParams, oh, directoryName):
    """
    Plots the ENC distribution of all channels for each VFAT.
    """
    fig, ax = plt.subplots(figsize = (12,10))
    ax.set_xlabel("VFAT Number")
    ax.set_ylabel("S-curve ENC (fC)")

    data = []
    for ii in range(len(vfatList)):
        data.append(scurveParams[ii, :, 0])

    ax.boxplot(data, patch_artist=True)
    
    plt.xticks(np.arange(1, len(vfatList) + 1), vfatList) # replace ticks with vfat number
    ax.set_title("ENC Distributions")
    plt.grid()
    fig.tight_layout()
    plt.savefig(directoryName + "/scurveENCdistribution_"+oh+".pdf")
    print("\nENC distribution plot saved at %s" % directoryName + "/scurveENCdistribution_"+oh+".pdf")

def plot2Dhist(vfatList, directoryName, oh, scurve_result, slope_adc, intercept_adc, mode):
    """
    Formats data originally stored in the s-curve dictionary
    and plots the 2D s-curve histogram.
    """
    hist2Ddata  = np.ndarray((len(vfatList), 256, 128))
    vfatCounter = 0
    
    for vfat in vfatList:
        for channel in range(128):
            temp       = dictToArray(scurve_result, vfat, channel) # transfer data from dictionary to array
            hist2Ddata[vfatCounter, :, channel] =  temp[:,1]    
        vfatCounter += 1

    channelNum = np.arange(0, 128, 1)
    chargeVals = np.arange(0, 256, 1)

    vfatCounter = 0
    for vfat in vfatList:
        chargeVals_mod = chargeVals
        for i in range(0,len(chargeVals_mod)):
            chargeVals_mod[i] = DACToCharge(chargeVals_mod[i], slope_adc, intercept_adc, vfat, mode)

        fig, ax = plt.subplots(figsize = (10,10))
        hist = ax.imshow(hist2Ddata[vfatCounter,:,:],
                   extent=[min(channelNum), max(channelNum), min(chargeVals_mod), max(chargeVals_mod)],cmap = cm.ocean_r,
                   origin="lower", interpolation="none", aspect="auto")
        cbar = fig.colorbar(hist, ax=ax, pad=0.01)
        cbar.set_label("Fired Events / Total Events")
        ax.set_xlabel("Channel Number")
        ax.set_ylabel("Injected Charge (DAC)")
        ax.set_title("S-curves for VFAT%d" % vfat)
        fig.tight_layout()
        plt.xticks(np.arange(min(channelNum), max(channelNum)+1, 20))
        fig.savefig(directoryName + "/scurve2Dhist_"+oh+"_VFAT%d.pdf" % vfat, dpi=1000)
        print(("\n2D histogram of scurves for VFAT%d " % vfat )+ ("saved at %s" % directoryName) + "/scurve2Dhist_"+oh+"_VFAT%d.pdf" % vfat)
        
        vfatCounter += 1


if __name__ == "__main__":
    warnings.filterwarnings("ignore") # temporarily disable warnings; infinite covariance matrix is returned when calling scipy.optimize.curve_fit(), but fit is fine

    # Parsing arguments
    parser = argparse.ArgumentParser(description="Plotting VFAT DAQ SCurve")
    parser.add_argument("-f", "--filename", action="store", dest="filename", help="SCurve result filename")
    parser.add_argument("-c", "--channels", action="store", nargs="+", dest="channels", help="Channels to plot for each VFAT")
    parser.add_argument("-m", "--mode", action="store", dest="mode", help="mode = voltage or current")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", help="Increase verbosity")
    args = parser.parse_args()

    channel_list = []
    if args.channels is None:
        channel_list = range(0,128)
    else:
        for channel in args.channels:
            channel_list.append(int(channel))

    if args.mode not in ["voltage", "current"]:
        print(Colors.YELLOW + "Mode can only be voltage or current" + Colors.ENDC)
        sys.exit()

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
    
    vfatList     = list(scurve_result.keys())
    scurveParams = fit_scurve(vfatList, scurve_result, oh, directoryName, args.verbose, channel_list)

    plotENCdistributions(vfatList, scurveParams, oh, directoryName)
    plot2Dhist(vfatList, directoryName, oh, scurve_result, slope_adc, intercept_adc, args.mode)


