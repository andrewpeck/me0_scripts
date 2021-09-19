from rw_reg_lpgbt import *
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib import cm
import numpy as np
import os, sys, glob
import argparse
import pandas as pd

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="Plotting VFAT Sbit Noise Rate")
    parser.add_argument("-f", "--filename", action="store", dest="filename", help="Noise rate result filename")
    parser.add_argument("-r", "--use_dac_scan_results", action="store_true", dest="use_dac_scan_results", help="use_dac_scan_results = to use latest DAC scan results for converting threshold to fC")
    args = parser.parse_args()

    directoryName        = args.filename.split(".txt")[0]
    plot_filename_prefix = (directoryName.split("/"))[2]
    oh = plot_filename_prefix.split("_vfat")[0]
    file = open(args.filename)

    plt.rcParams.update({'font.size': 22})
    plt.grid()

    try:
        os.makedirs(directoryName) # create directory for scurve noise rate results
    except FileExistsError: # skip if directory already exists
        pass
        
    noise_result = {}
    time = 0
    for line in file.readlines():
        if "vfat" in line:
            continue
        vfat = int(line.split()[0])
        sbit = int(line.split()[1])
        thr = int(line.split()[2])
        fired = int(line.split()[3])
        time = float(line.split()[4])
        if vfat not in noise_result:
            noise_result[vfat] = {}
        if sbit not in noise_result[vfat]:
            noise_result[vfat][sbit] = {}
        if fired == -9999:
            noise_result[vfat][sbit][thr] = 0
        else:
            noise_result[vfat][sbit][thr] = fired
    file.close()

    numVfats = len(noise_result.keys())
    if numVfats <= 3:
        fig1, ax1 = plt.subplots(1, numVfats, figsize=(numVfats*10,10))
    elif numVfats <= 6:
        fig1, ax1 = plt.subplots(2, 3, figsize=(30,20))
    elif numVfats <= 12:
        fig1, ax1 = plt.subplots(2, 6, figsize=(60,20))
    elif numVfats <= 18:
        fig1, ax1 = plt.subplots(3, 6, figsize=(60,30))
    elif numVfats <= 24:
        fig1, ax1 = plt.subplots(4, 6, figsize=(60,40))

    vfatCnt0 = 0
    for vfat in noise_result:
        print ("Creating plots for VFAT %02d"%vfat)

        threshold = []
        noise_rate = []

        for sbit in noise_result[vfat]:
            for thr in noise_result[vfat][sbit]:
                threshold.append(thr)
                noise_rate.append(0)
            break
        for sbit in noise_result[vfat]:
            for i in range(0,len(threshold)):
                thr = threshold[i]
                noise_rate[i] += noise_result[vfat][sbit][thr]/time

        if numVfats == 1:
            ax1.set_xlabel("Threshold (DAC)")
            ax1.set_ylabel("SBit Rate (Hz)")
            ax1.set_yscale("log")
            ax1.set_title("VFAT# %02d"%vfat)
            ax1.plot(threshold, noise_rate, "o", markersize=12)
        elif numVfats <= 3:
            ax1[vfatCnt0].set_xlabel("Threshold (DAC)")
            ax1[vfatCnt0].set_ylabel("SBit Rate (Hz)")
            ax1[vfatCnt0].set_yscale("log")
            ax1[vfatCnt0].set_title("VFAT# %02d"%vfat)
            ax1[vfatCnt0].plot(threshold, noise_rate, "o", markersize=12)
        elif numVfats <= 6:
            ax1[int(vfatCnt0/3), vfatCnt0%3].set_xlabel("Threshold (DAC)")
            ax1[int(vfatCnt0/3), vfatCnt0%3].set_ylabel("SBit Rate (Hz)")
            ax1[int(vfatCnt0/3), vfatCnt0%3].set_yscale("log")
            ax1[int(vfatCnt0/3), vfatCnt0%3].set_title("VFAT# %02d"%vfat)
            ax1[int(vfatCnt0/3), vfatCnt0%3].plot(threshold, noise_rate, "o", markersize=12)
        else:
            ax1[int(vfatCnt0/6), vfatCnt0%6].set_xlabel("Threshold (DAC)")
            ax1[int(vfatCnt0/6), vfatCnt0%6].set_ylabel("SBit Rate (Hz)")
            ax1[int(vfatCnt0/6), vfatCnt0%6].set_yscale("log")
            ax1[int(vfatCnt0/6), vfatCnt0%6].set_title("VFAT# %02d"%vfat)
            ax1[int(vfatCnt0/6), vfatCnt0%6].plot(threshold, noise_rate, "o", markersize=12)

        fig2, ax2 = plt.subplots(8, 8, figsize=(80,80))
        for sbit in noise_result[vfat]:
            noise_rate_sbit = []
            for thr in range(0,len(threshold)):
                noise_rate_sbit.append(noise_result[vfat][sbit][thr]/time)
            ax2[int(sbit/8), sbit%8].set_xlabel("Threshold (DAC)")
            ax2[int(sbit/8), sbit%8].set_ylabel("SBit Rate (Hz)")
            ax2[int(sbit/8), sbit%8].set_yscale("log")
            ax2[int(sbit/8), sbit%8].plot(threshold, noise_rate_sbit, "o", markersize=12)
            #leg = ax.legend(loc="center right", ncol=2)
            ax2[int(sbit/8), sbit%8].set_title("VFAT# %02d, S-Bit# %02d"%(vfat, sbit))
        fig2.tight_layout()
        fig2.savefig((directoryName+"/sbit_noise_rate_channels_"+oh+"_VFAT%02d.pdf")%vfat)
        plt.close(fig2)

        vfatCnt0+=1

    fig1.tight_layout()
    fig1.savefig((directoryName+"/sbit_noise_rate_"+oh+".pdf"))
    plt.close(fig1)







