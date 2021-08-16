from rw_reg_lpgbt import *
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import os, sys, glob
import argparse

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="Plotting VFAT Cross Talk")
    parser.add_argument("-f", "--filename", action="store", dest="filename", help="Cross talk result filename")
    args = parser.parse_args()

    directoryName        = args.filename.split(".txt")[0]
    plot_filename_prefix = (directoryName.split("/"))[2]
    oh = plot_filename_prefix.split("_vfat")[0]
    file = open(args.filename)

    try:
        os.makedirs(directoryName) # create directory for scurve analysis results
    except FileExistsError: # skip if directory already exists
        pass
        
    hitmap_result = {}
    for line in file.readlines():
        if "vfat" in line:
            continue
        vfat = int(line.split()[0])
        channel_inj = int(line.split()[1])
        channel_read = int(line.split()[2])
        fired = int(line.split()[3])
        events = int(line.split()[4])
        if vfat not in hitmap_result:
            hitmap_result[vfat] = {}
        if channel_inj not in hitmap_result[vfat]:
            hitmap_result[vfat][channel_inj] = {}
        hitmap_result[vfat][channel_inj][channel_read] = {}
        if fired == -9999 or events == -9999 or events == 0:
            hitmap_result[vfat][channel_inj][channel_read] = 0
        else:
            hitmap_result[vfat][channel_inj][channel_read] = float(fired)/float(events)
    file.close()

    for vfat in hitmap_result:
        plot_data = []
        for x in range(0,128):
            data = []
            for y in range(0,128):
                data.append(hitmap_result[vfat][y][x])
            plot_data.append(data)

        fig, axs = plt.subplots()
        plt.xlabel("Channel Injected")
        plt.ylabel("Channel Read")
        plt.xlim(0,128)
        plt.ylim(0,128)
        plot = axs.imshow(plot_data, cmap="jet")
        fig.colorbar(plot, ax=axs)
        plt.title("VFAT# %02d"%vfat)
        plt.savefig((directoryName+"/crosstalk_"+oh+"_VFAT%02d.pdf")%vfat)





