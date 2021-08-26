from rw_reg_lpgbt import *
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib import cm
import numpy as np
import os, sys, glob
import argparse

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="Plotting VFAT Register Scan")
    parser.add_argument("-f", "--filename", action="store", dest="filename", help="Register Scan result filename")
    parser.add_argument("-c", "--channels", action="store", nargs="+", dest="channels", help="Channels to plot for each VFAT")
    parser.add_argument("-d", "--dac", action="store", dest="dac", help="Register to plot")
    args = parser.parse_args()

    if args.dac is None:
        print(Colors.YELLOW + "Need Register to plot" + Colors.ENDC)
        sys.exit()
    dac = args.dac

    directoryName        = args.filename.split(".txt")[0]
    plot_filename_prefix = (directoryName.split("/"))[2]
    oh = plot_filename_prefix.split("_vfat")[0]
    file = open(args.filename)

    try:
        os.makedirs(directoryName) # create directory for scurve analysis results
    except FileExistsError: # skip if directory already exists
        pass
        
    dac_result = {}
    for line in file.readlines():
        if "vfat" in line:
            continue
        vfat = int(line.split()[0])
        channel = int(line.split()[1])
        reg = int(line.split()[2])
        fired = int(line.split()[3])
        events = int(line.split()[4])
        if vfat not in dac_result:
            dac_result[vfat] = {}
        if channel not in dac_result[vfat]:
            dac_result[vfat][channel] = {}
        if fired == -9999 or events == -9999 or events == 0:
            dac_result[vfat][channel][reg] = 0
        else:
            dac_result[vfat][channel][reg] = float(fired)/float(events)
    file.close()

    numVfats = len(scurve_result.keys())
    if numVfats <= 3:
        fig1, ax1 = plt.subplots(1, numVfats, figsize=(numVfats*10,10))
        plot1 = 0
        cbar1 = 0
    elif numVfats <= 6:
        fig1, ax1 = plt.subplots(2, 3, figsize=(30,20))
        plot1 ={}
        cbar1 ={}
    elif numVfats <= 12:
        fig1, ax1 = plt.subplots(2, 6, figsize=(60,20))
        plot1 ={}
        cbar1 ={}
    elif numVfats <= 18:
        fig1, ax1 = plt.subplots(3, 6, figsize=(60,30))
        plot1 ={}
        cbar1 ={}
    elif numVfats <= 24:
        fig1, ax1 = plt.subplots(4, 6, figsize=(60,40))
        plot1 ={}
        cbar1 ={}

    for vfat in dac_result:
        fig, axs = plt.subplots()
        axs.xlabel("Channel Number")
        axs.ylabel(dac + " (DAC)")
        #axs.xlim(0,128)
        #axs.ylim(0,256)

        plot_data = []
        for reg in range(0,256):
            data = []
            for channel in range(0,128):
                if channel not in dac_result[vfat]:
                    data.append(0)
                elif reg not in dac_result[vfat][channel]:
                    data.append(0)
                else:
                    data.append(dac_result[vfat][channel][reg])
            plot_data.append(data)
        channelNum = np.arange(0, 128, 1)
        dacVals = np.arange(0, 256, 1)
        plot = axs.imshow(plot_data, extent=[min(channelNum), max(channelNum), min(dacVals), max(dacVals)], origin="lower",  cmap=cm.ocean_r,interpolation="nearest", aspect="auto")
        cbar = fig.colorbar(plot, ax=axs, pad=0.01)
        cbar.set_label("Fired Events / Total Events")
        axs.set_title("VFAT# %02d"%vfat)
        fig.savefig((plot_filename_prefix+"_map_VFAT%02d.pdf")%vfat)

        if numVfats == 1:
            ax1.xlabel("Channel Number")
            ax1.ylabel(dac + " (DAC)")
            ax1.set_title("VFAT# %02d"%vfat)
            plot1 = ax1.imshow(plot_data, extent=[min(channelNum), max(channelNum), min(dacVals), max(dacVals)], origin="lower",  cmap=cm.ocean_r,interpolation="nearest", aspect="auto")
            cbar1 = fig1.colorbar(plot1, ax=ax1, pad=0.01)
            cbar1.set_label("Fired Events / Total Events")
        elif numVfats <= 3:
            ax1[vfatCnt0].xlabel("Channel Number")
            ax1[vfatCnt0].ylabel(dac + " (DAC)")
            ax1[vfatCnt0].set_title("VFAT# %02d"%vfat)
            plot1[vfatCnt0] = ax1[vfatCnt0].imshow(plot_data, extent=[min(channelNum), max(channelNum), min(dacVals), max(dacVals)], origin="lower",  cmap=cm.ocean_r,interpolation="nearest", aspect="auto")
            cbar1[vfatCnt0] = fig1[vfatCnt0].colorbar(plot1[vfatCnt0], ax=ax1[vfatCnt0], pad=0.01)
            cbar1[vfatCnt0].set_label("Fired Events / Total Events")
        elif numVfats <= 6:
            ax1[int(vfatCnt0/3), vfatCnt0%3].xlabel("Channel Number")
            ax1[int(vfatCnt0/3), vfatCnt0%3].ylabel(dac + " (DAC)")
            ax1[int(vfatCnt0/3), vfatCnt0%3].set_title("VFAT# %02d"%vfat)
            plot1[int(vfatCnt0/3), vfatCnt0%3] = ax1[int(vfatCnt0/3), vfatCnt0%3].imshow(plot_data, extent=[min(channelNum), max(channelNum), min(dacVals), max(dacVals)], origin="lower",  cmap=cm.ocean_r,interpolation="nearest", aspect="auto")
            cbar1[int(vfatCnt0/3), vfatCnt0%3] = fig1[int(vfatCnt0/3), vfatCnt0%3].colorbar(plot1[int(vfatCnt0/3), vfatCnt0%3], ax=ax1[int(vfatCnt0/3), vfatCnt0%3], pad=0.01)
            cbar1[int(vfatCnt0/3), vfatCnt0%3].set_label("Fired Events / Total Events")
        else:
            ax1[int(vfatCnt0/6), vfatCnt0%6].xlabel("Channel Number")
            ax1[int(vfatCnt0/6), vfatCnt0%6].ylabel(dac + " (DAC)")
            ax1[int(vfatCnt0/6), vfatCnt0%6].set_title("VFAT# %02d"%vfat)
            plot1[int(vfatCnt0/6), vfatCnt0%6] = ax1[int(vfatCnt0/6), vfatCnt0%6].imshow(plot_data, extent=[min(channelNum), max(channelNum), min(dacVals), max(dacVals)], origin="lower",  cmap=cm.ocean_r,interpolation="nearest", aspect="auto")
            cbar1[int(vfatCnt0/6), vfatCnt0%6] = fig1[int(vfatCnt0/6), vfatCnt0%6].colorbar(plot1[int(vfatCnt0/6), vfatCnt0%6], ax=ax1[int(vfatCnt0/6), vfatCnt0%6], pad=0.01)
            cbar1[int(vfatCnt0/6), vfatCnt0%6].set_label("Fired Events / Total Events")

            vfatCnt0+=1

    fig1.tight_layout()
    fig1.savefig((plot_filename_prefix+"_map.pdf"))

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
    for vfat in dac_result:
        fig, ax = plt.subplots()
        ax.xlabel(dac)
        ax.ylabel("# Fired Events / # Total Events")
        ax.ylim(-0.1,1.1)
        for channel in args.channels:
            channel = int(channel)
            if channel not in dac_result[vfat]:
                print (Colors.YELLOW + "Channel %d not in Register scan"%channel + Colors.ENDC)
                continue
            reg = range(0,256)
            reg_plot = []
            frac = []
            for r in reg:
                if r in dac_result[vfat][channel]:
                    reg_plot.append(r)
                    frac.append(dac_result[vfat][channel][r])
            ax.plot(reg_plot, frac, "o", label="Channel %d"%channel)
            if numVfats == 1:
                ax2.plot(reg_plot, frac, "o", label="Channel %d"%channel)
            elif numVfats <= 3:
                ax2[vfatCnt0].plot(reg_plot, frac, "o", label="Channel %d"%channel)
            elif numVfats <= 6:
                ax2[int(vfatCnt0/3), vfatCnt0%3].plot(reg_plot, frac, "o", label="Channel %d"%channel)
            else:
                ax2[int(vfatCnt0/6), vfatCnt0%6].plot(reg_plot, frac, "o", label="Channel %d"%channel)
        leg = ax.legend(loc="center right", ncol=2)
        ax.set_title("VFAT# %02d"%vfat)
        fig.savefig((directoryName+"/register_"+oh+"_VFAT%02d.pdf")%vfat)

        if numVfats == 1:
            ax2.xlabel("dac")
            ax2.ylabel("Fired Events / Total Events")
            ax2.set_title("VFAT# %02d"%vfat)
            ax2.ylim(-0.1,1.1)
            leg2 = ax2.legend(loc="center right", ncol=2)
        elif numVfats <= 3:
            ax2[vfatCnt0].xlabel("dac")
            ax2[vfatCnt0].ylabel("Fired Events / Total Events")
            ax2[vfatCnt0].set_title("VFAT# %02d"%vfat)
            ax2[vfatCnt0].ylim(-0.1,1.1)
            leg2[vfatCnt0] = ax2[vfatCnt0].legend(loc="center right", ncol=2)
        elif numVfats <= 6:
            ax2[int(vfatCnt0/3), vfatCnt0%3].xlabel("dac")
            ax2[int(vfatCnt0/3), vfatCnt0%3].ylabel("Fired Events / Total Events")
            ax2[int(vfatCnt0/3), vfatCnt0%3].set_title("VFAT# %02d"%vfat)
            ax2[int(vfatCnt0/3), vfatCnt0%3].ylim(-0.1,1.1)
            leg2[int(vfatCnt0/3), vfatCnt0%3] = ax2[int(vfatCnt0/3), vfatCnt0%3].legend(loc="center right", ncol=2)
        else:
            ax2[int(vfatCnt0/6), vfatCnt0%6].xlabel("dac")
            ax2[int(vfatCnt0/6), vfatCnt0%6].ylabel("Fired Events / Total Events")
            ax2[int(vfatCnt0/6), vfatCnt0%6].set_title("VFAT# %02d"%vfat)
            ax2[int(vfatCnt0/6), vfatCnt0%6].ylim(-0.1,1.1)
            leg2[int(vfatCnt0/6), vfatCnt0%6] = ax2[int(vfatCnt0/6), vfatCnt0%6].legend(loc="center right", ncol=2)

        vfatCnt0+=1

    fig2.tight_layout()
    fig2.savefig((directoryName+"/register_"+oh+".pdf"))

