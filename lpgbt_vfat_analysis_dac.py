from rw_reg_lpgbt import *
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from time import time

plt.rcParams.update({'font.size': 22}) # Increase font size

def poly5(x, a, b, c, d, e, f):
    return (a * np.power(x,5)) + (b * np.power(x,4)) + (c * np.power(x,3)) + (d * np.power(x,2)) + (e * x) + f

def determine_nom(data, nominal_ADC0):
    val1=abs(data['value']-nominal_ADC0).idxmin()
    return (data.iloc[val1].DAC_point)
 
nominalDacValues = {
        "CFG_CAL_DAC":(0,"uA"), # there is no nominal value
        "CFG_BIAS_PRE_I_BIT":(150,"uA"),
        "CFG_BIAS_PRE_I_BLCC":(25,"nA"),
        "CFG_BIAS_PRE_I_BSF":(26,"uA"),
        "CFG_BIAS_SH_I_BFCAS":(26,"uA"),
        "CFG_BIAS_SH_I_BDIFF":(16,"uA"),
        "CFG_BIAS_SD_I_BDIFF":(28,"uA"),
        "CFG_BIAS_SD_I_BFCAS":(27,"uA"),
        "CFG_BIAS_SD_I_BSF":(30,"uA"),
        "CFG_BIAS_CFD_DAC_1":(20,"uA"),
        "CFG_BIAS_CFD_DAC_2":(20,"uA"),
        "CFG_EN_HYST":(100,"nA"),
        "CFG_THR_ARM_DAC":(64,"mV"),
        "CFG_THR_ZCC_DAC":(5.5,"mV"),
        "CFG_BIAS_PRE_VREF":(430,'mV'),
        "CFG_VREF_ADC":(1.0,'V')
}

#: From Tables 12 and 13 from the VFAT3 manual
nominalDacScalingFactors = {
        "CFG_CAL_DAC":10, # Valid only for currentPulse; if voltageStep this is 1
        "CFG_BIAS_PRE_I_BIT":0.2,
        "CFG_BIAS_PRE_I_BLCC":100,
        "CFG_BIAS_PRE_I_BSF":0.25,
        "CFG_BIAS_SH_I_BFCAS":1,
        "CFG_BIAS_SH_I_BDIFF":1,
        "CFG_BIAS_SD_I_BDIFF":1,
        "CFG_BIAS_SD_I_BFCAS":1,
        "CFG_BIAS_SD_I_BSF":0.25,
        "CFG_BIAS_CFD_DAC_1":1,
        "CFG_BIAS_CFD_DAC_2":1,
        "CFG_EN_HYST":5,
        "CFG_THR_ARM_DAC":1,
        "CFG_THR_ZCC_DAC":4,
        "CFG_BIAS_PRE_VREF":1,
        "CFG_ADC_VREF": 1
}


def main(inFile, calFile, fullPath):
	# read in DAC and cal data to dataframe
	dacData = pd.read_csv(inFile, names=["OH", "DAC_reg", "vfat", "DAC_point","value"], sep=";") 
	calData = pd.read_csv(calFile ,names=["vfat", "slope", "intercept"], sep=";")

	numDacs  = dacData['DAC_reg'].nunique() # get number of dacs scanned
	numVfats = dacData['vfat'].nunique() # get number of vfats

	indices = dacData[dacData["DAC_reg"] == "CFG_MON_GAIN"].index
	dacData.drop(indices, inplace=True)

	for DAC_reg in dacData.DAC_reg.unique(): # loop over dacs
	    startTime = time()
	    print(Colors.GREEN + "Working on DAC: %s \n" % DAC_reg + Colors.ENDC)
	    dacFileName = fullPath + "/nominalValues_" + DAC_reg + ".txt"
	    file = open(dacFileName, "w")
	    sel = dacData.DAC_reg == DAC_reg # select rows for specific DAC 
	    datareg = dacData[sel] # slice dataframe for specific DAC
	    vfatCnt0 = 0 # Initialize vfat counter
	    vfatCnt1 = 0 # Initialize vfat counter
	    
	    if numVfats == 6:
	        fig, ax = plt.subplots(2, 3, figsize=(25,15))
	    elif numVfats < 6:
	        temp = 6 - numVfats
	        fig, ax = plt.subplots(1, numVfats, figsize=(25, 15))
	        ax.flatten()
            #print("less than 6 vfats")
    
	    for vfat in datareg.vfat.unique(): # loop over vfats
	        print(Colors.GREEN + 'Working on VFAT: %s\n' % vfat+ Colors.ENDC)
	        sel2 = datareg.vfat == vfat # select rows for the current vfat
	        datavfat = datareg[sel2].reset_index() # reset starting index of sliced dataframe to 0
	        #print('datavfat: \n {}'.format(datavfat))
	        slopeTemp = np.array(calData.loc[calData["vfat"] == vfat].slope) # get slope for VFAT
	        interTemp = np.array(calData.loc[calData["vfat"] == vfat].intercept) # get intercept for VFAT
	        print('VFAT: {}, intercept: {}'.format(vfat, interTemp))
	        print('vfat data: {}'.format(datavfat["value"]))

	        datavfat["value"] = nominalDacScalingFactors[DAC_reg] * ((datavfat["value"] * slopeTemp) + interTemp) # transform data from DAC to uA/mV
	        print('vfat data after transformation: {}'.format(datavfat["value"]))
	        datavfat2 = datavfat
	        
	        # convert data to np arrays for plotting
	        xdata = datavfat['value'].to_numpy()
	        ydata = datavfat['DAC_point'].to_numpy()

	        if numVfats == 6:
	            if vfatCnt0 <= 2:
	                ax[0, vfatCnt0].grid()
	                ax[0, vfatCnt0].plot(datavfat.value, datavfat.DAC_point, 'ko', markersize = 7, fillstyle='none') # plot transformed data
	            elif vfatCnt0 > 2:
	                ax[1, vfatCnt1].grid()
	                ax[1, vfatCnt1].plot(datavfat.value, datavfat.DAC_point, 'ko', markersize = 7, fillstyle='none') # plot transformed data
	        elif numVfats < 6:
	            ax[vfatCnt0].grid()
	            ax[vfatCnt0].plot(datavfat.value, datavfat.DAC_point, 'ko', markersize = 7, fillstyle='none') # plot transformed data

	          
	        fitData = np.polyfit(xdata, ydata, 5) # fit data to 5th degree polynomial
	        
	        datavfat2['DAC_point'] = pd.DataFrame(poly5(xdata, *fitData), columns=['DACpoint']) # adds fitted data to dataframe
	        nml = nominalDacValues[DAC_reg][0] # store nominal DAC value
	        nominal_ADC0 = int(determine_nom(datavfat2, nml)) # find nominal value for specific vfat
	        if nominal_ADC0 > max(datavfat.DAC_point):
	            nominal_ADC0 = max(datavfat.DAC_point)
	        
	        # Plot fit
	        if numVfats == 6:
	            if vfatCnt0 <= 2:
	                ax[0, vfatCnt0].set_xlabel('ADC0 (%s)' % nominalDacValues[DAC_reg][1])
	                ax[0, vfatCnt0].set_ylabel('DAC')
	                ax[0, vfatCnt0].plot(xdata, poly5(xdata, *fitData), 'r-', linewidth=3) # plot fit
	                ax[0, vfatCnt0].set_title('VFAT%02d' % vfat)
	            elif vfatCnt0 > 2:
	                ax[1, vfatCnt1].set_xlabel('ADC0 (%s)' % nominalDacValues[DAC_reg][1])
	                ax[1, vfatCnt1].set_ylabel('DAC')
	                ax[1, vfatCnt1].plot(xdata, poly5(xdata, *fitData), 'r-', linewidth=3) # plot fit
	                ax[1, vfatCnt1].set_title('VFAT%02d' % vfat)
	        elif numVfats < 6:
	            ax[vfatCnt0].set_xlabel('ADC0 (%s)' % nominalDacValues[DAC_reg][1])
	            ax[vfatCnt0].set_ylabel('DAC')
	            ax[vfatCnt0].plot(xdata, poly5(xdata, *fitData), 'r-', linewidth=3) # plot fit
	            ax[vfatCnt0].set_title('VFAT%02d' % vfat)

	        if vfatCnt0 > 2:
	            vfatCnt1 += 1
	        else:
	            pass
	        
	        vfatCnt0 += 1

	        file.write("%s;%i;%i\n" % (DAC_reg, vfat, nominal_ADC0))
	    fig.suptitle(DAC_reg, fontsize=32) # place DAC name for main title
	    fig.subplots_adjust(top=0.88) # adjust main title so that it
	    fig.tight_layout()
	    plt.savefig(fullPath + '/DAC_summaryPlots_%s.pdf' % DAC_reg)
	    file.close()
	    print('Total time to execute: %s s' % str(time() - startTime))   
	    plt.close() 

if __name__ == '__main__':

	# Parsing arguments
    parser = argparse.ArgumentParser(description='LpGBT VFAT Slow Control Error Ratio Test')
    parser.add_argument("-i", "--inFile", action="store", dest="inFile", help="Input file")
    parser.add_argument("-c", "--calFile", action="store", dest="calFile", help="Calibration (ADC0) file, in form (without header)\n vfatNumber;slope;intercept")
    args = parser.parse_args()

    if args.inFile is None or args.calFile is None:
        print(Colors.YELLOW + "Input file and calibration file (ADC0) must be input." + Colors.ENDC)
        sys.exit()

    inFileName = args.inFile.split('/') # get input file name with directory
    dirTemp    = inFileName[1].split('_')[4:7] # store timestamp information
    dirName    = dirTemp[0] + '_' + dirTemp[1] + '_' + dirTemp[2].split('.')[0] # create new directory
    fullPath   = inFileName[0] + "/" + dirName
    print(Colors.GREEN + '\nDAC scan results stored in: %s' % fullPath + Colors.ENDC)

    try:
        os.makedirs(fullPath) # create directory for scurve analysis results
    except FileExistsError: # skip if directory already exists
        pass

    try:
        main(args.inFile, args.calFile, fullPath)
    except KeyboardInterrupt:
        print(Colors.RED + "\nKeyboard Interrupt encountered" + Colors.ENDC)


