from rw_reg_lpgbt import *
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import os, sys, glob
import argparse

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="Plotting VFAT HitMap")
    parser.add_argument("-f", "--filename", action="store", dest="filename", help="Hit/Noise map result filename")
    parser.add_argument("-t", "--type", action="store", dest="type", help="type = hit or noise")
    args = parser.parse_args()

    if args.type not in ["hit", "noise"]:
        print (Colors.YELLOW + "Only hit or noise options allowed for type" + Colors.ENDC)
        sys.exit()

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
        channel = int(line.split()[1])
        fired = int(line.split()[2])
        events = int(line.split()[3])
        if vfat not in hitmap_result:
            hitmap_result[vfat] = {}
        if fired == -9999 or events == -9999 or events == 0:
            hitmap_result[vfat][channel] = 0
        else:
            hitmap_result[vfat][channel] = float(fired)/float(events)
    file.close()

    numVfats = len(hitmap_result.keys())
    if numVfats <= 3:
        fig2, ax2 = plt.subplots(1, numVfats, figsize=(numVfats*10,10))
        leg2 = 0
    elif numVfats <= 6:
        fig2, ax2 = plt.subplots(2, 3, figsize=(30,20))
        leg2 ={}
    elif numVfats <= 12:
        fig2, ax2 = plt.subplots(2, 6, figsize=(60,20))
        leg2 ={}
    elif numVfats <= 18:
        fig2, ax2 = plt.subplots(3, 6, figsize=(60,30))
        leg2 ={}
    elif numVfats <= 24:
        fig2, ax2 = plt.subplots(4, 6, figsize=(60,40))
        leg2 ={}

    vfatCnt0 = 0
    for vfat in hitmap_result:
        fig, ax = plt.subplots()
        ax.xlabel("Channel")
        ax.ylabel("# Fired Events / # Total Events")
        ax.ylim(-0.1,1.1)
        channel_plot = range(0,128)
        if args.type == "hit":
            ax.set_title("Channel Hit Map")
        else:
            ax.set_title("Channel Noise Map")

        frac = []
        for channel in channel_plot:
            frac.append(hitmap_result[vfat][channel])
        ax.plot(channel_plot, frac, "o", label="VFAT %d"%vfat)
        leg = ax.legend(loc="center right", ncol=2)
        fig.savefig((directoryName+"/hitmap_"+oh+"_VFAT%02d.pdf")%vfat)

        if numVfats == 1:
            ax2.xlabel("Channel")
            ax2.ylabel("Fired Events / Total Events")
            ax2.ylim(-0.1,1.1)
            if args.type == "hit":
                ax2.set_title("Channel Hit Map")
            else:
                ax2.set_title("Channel Noise Map")
            leg2 = ax2.legend(loc="center right", ncol=2)
            ax2.plot(channel_plot, frac, "o", label="VFAT %d"%vfat)
        elif numVfats <= 3:
            ax2[vfatCnt0].xlabel("Channel")
            ax2[vfatCnt0].ylabel("Fired Events / Total Events")
            ax2[vfatCnt0].ylim(-0.1,1.1)
            if args.type == "hit":
                ax2[vfatCnt0].set_title("Channel Hit Map")
            else:
                ax2[vfatCnt0].set_title("Channel Noise Map")
            leg2[vfatCnt0] = ax2[vfatCnt0].legend(loc="center right", ncol=2)
            ax2[vfatCnt0].plot(channel_plot, frac, "o", label="VFAT %d"%vfat)
        elif numVfats <= 6:
            ax2[int(vfatCnt0/3), vfatCnt0%3].xlabel("Channel")
            ax2[int(vfatCnt0/3), vfatCnt0%3].ylabel("Fired Events / Total Events")
            ax2[int(vfatCnt0/3), vfatCnt0%3].ylim(-0.1,1.1)
            if args.type == "hit":
                ax2[int(vfatCnt0/3), vfatCnt0%3].set_title("Channel Hit Map")
            else:
                ax2[int(vfatCnt0/3), vfatCnt0%3].set_title("Channel Noise Map")
            leg2[int(vfatCnt0/3), vfatCnt0%3] = ax2[int(vfatCnt0/3), vfatCnt0%3].legend(loc="center right", ncol=2)
            ax2[int(vfatCnt0/3), vfatCnt0%3].plot(channel_plot, frac, "o", label="VFAT %d"%vfat)
        else:
            ax2[int(vfatCnt0/6), vfatCnt0%6].xlabel("Channel")
            ax2[int(vfatCnt0/6), vfatCnt0%6].ylabel("Fired Events / Total Events")
            ax2[int(vfatCnt0/6), vfatCnt0%6].ylim(-0.1,1.1)
            if args.type == "hit":
                ax2[int(vfatCnt0/6), vfatCnt0%6].set_title("Channel Hit Map")
            else:
                ax2[int(vfatCnt0/6), vfatCnt0%6].set_title("Channel Noise Map")
            leg2[int(vfatCnt0/6), vfatCnt0%6] = ax2[int(vfatCnt0/6), vfatCnt0%6].legend(loc="center right", ncol=2)
            ax2[int(vfatCnt0/6), vfatCnt0%6].plot(channel_plot, frac, "o", label="VFAT %d"%vfat)

        vfatCnt0+=1

    fig2.tight_layout()
    fig2.savefig((directoryName+"/hitmap_"+oh+".pdf"))
