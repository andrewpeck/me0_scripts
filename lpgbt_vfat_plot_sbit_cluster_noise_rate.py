from rw_reg_lpgbt import *
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib import cm
import numpy as np
import os, sys, glob
import argparse

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="Plotting VFAT Sbit Cluster Noise Rate")
    parser.add_argument("-f", "--filename", action="store", dest="filename", help="Noise rate result filename")
    args = parser.parse_args()

    directoryName        = args.filename.split(".txt")[0]
    plot_filename_prefix = (directoryName.split("/"))[2]
    oh = plot_filename_prefix.split("_vfat")[0]
    file = open(args.filename)

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
        thr = int(line.split()[1])
        fired = int(line.split()[2])
        time = float(line.split()[3])
        if vfat not in noise_result:
            noise_result[vfat] = {}
        if fired == -9999:
            noise_result[vfat][thr] = 0
        else:
            noise_result[vfat][thr] = fired
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
        threshold = []
        noise_rate = []

        for thr in noise_result[vfat]:
            threshold.append(thr)
            noise_rate.append(noise_result[vfat][thr]/time)

        fig, ax = plt.subplots()
        ax.set_xlabel("Threshold (DAC)")
        ax.set_ylabel("SBit Rate (Hz)")
        ax.yscale("log")
        ax.plot(threshold, noise_rate, "o")
        #leg = ax.legend(loc="center right", ncol=2)
        ax.set_title("VFAT# %02d"%vfat)
        fig.tight_layout()
        fig.savefig((directoryName+"/sbit_cluster_noise_rate_"+oh+"_VFAT%02d.pdf")%vfat)
        plt.close(fig)

        if numVfats == 1:
            ax1.set_xlabel("Threshold (DAC)")
            ax1.set_ylabel("SBit Rate (Hz)")
            ax1.yscale("log")
            ax1.set_title("VFAT# %02d"%vfat)
            ax1.plot(threshold, noise_rate, "o")
        elif numVfats <= 3:
            ax1[vfatCnt0].set_xlabel("Threshold (DAC)")
            ax1[vfatCnt0].set_ylabel("SBit Rate (Hz)")
            ax1[vfatCnt0].yscale("log")
            ax1[vfatCnt0].set_title("VFAT# %02d"%vfat)
            ax1[vfatCnt0].plot(threshold, noise_rate, "o")
        elif numVfats <= 6:
            ax1[int(vfatCnt0/3), vfatCnt0%3].set_xlabel("Threshold (DAC)")
            ax1[int(vfatCnt0/3), vfatCnt0%3].set_ylabel("SBit Rate (Hz)")
            ax1[int(vfatCnt0/3), vfatCnt0%3].yscale("log")
            ax1[int(vfatCnt0/3), vfatCnt0%3].set_title("VFAT# %02d"%vfat)
            ax1[int(vfatCnt0/3), vfatCnt0%3].plot(threshold, noise_rate, "o")
        else:
            ax1[int(vfatCnt0/6), vfatCnt0%6].set_xlabel("Threshold (DAC)")
            ax1[int(vfatCnt0/6), vfatCnt0%6].set_ylabel("SBit Rate (Hz)")
            ax1[int(vfatCnt0/6), vfatCnt0%6].yscale("log")
            ax1[int(vfatCnt0/6), vfatCnt0%6].set_title("VFAT# %02d"%vfat)
            ax1[int(vfatCnt0/6), vfatCnt0%6].plot(threshold, noise_rate, "o")

        vfatCnt0+=1

    fig1.tight_layout()
    fig1.savefig((directoryName+"/sbit_cluster_noise_rate_"+oh+".pdf"))
    plt.close(fig1)







