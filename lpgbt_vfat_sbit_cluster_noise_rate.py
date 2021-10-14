from rw_reg_lpgbt import *
from time import sleep, time
import datetime
import sys
import argparse
import random
import glob
import json
from lpgbt_vfat_config import initialize_vfat_config, configureVfat, enableVfatchannel


def lpgbt_vfat_sbit(system, oh_select, vfat_list, sbit_list, step, runtime, s_bit_cluster_mapping):
    if not os.path.exists("vfat_data/vfat_sbit_cluster_noise_results"):
        os.makedirs("vfat_data/vfat_sbit_cluster_noise_results")
    now = str(datetime.datetime.now())[:16]
    now = now.replace(":", "_")
    now = now.replace(" ", "_")
    foldername = "vfat_data/vfat_sbit_cluster_noise_results/"
    filename = foldername + "ME0_OH%d_vfat_sbit_cluster_noise_"%oh_select + now + ".txt"
    file_out = open(filename,"w+")
    file_out.write("vfat    sbit    threshold    fired    time\n")

    vfat_oh_link_reset()
    global_reset()
    sleep(0.1)
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.GEM_SYSTEM.VFAT3.SC_ONLY_MODE"), 1)

    sbit_data = {}
    # Check ready and get nodes
    for vfat in vfat_list:
        lpgbt, gbt_select, elink, gpio = vfat_to_gbt_elink_gpio(vfat)
        check_lpgbt_link_ready(oh_select, gbt_select)

        print("Configuring VFAT %d" % (vfat))
        configureVfat(1, vfat, oh_select, 0)
        for channel in range(0,128):
            enableVfatchannel(vfat, oh_select, channel, 1, 0) # mask all channels and disable calpulsing

        link_good_node = get_rwreg_node("BEFE.GEM_AMC.OH_LINKS.OH%d.VFAT%d.LINK_GOOD" % (oh_select, vfat))
        sync_error_node = get_rwreg_node("BEFE.GEM_AMC.OH_LINKS.OH%d.VFAT%d.SYNC_ERR_CNT" % (oh_select, vfat))
        link_good = read_backend_reg(link_good_node)
        sync_err = read_backend_reg(sync_error_node)
        if system!="dryrun" and (link_good == 0 or sync_err > 0):
            print (Colors.RED + "Link is bad for VFAT# %02d"%(vfat) + Colors.ENDC)
            rw_terminate()

        sbit_data[vfat] = {}
        for sbit in sbit_list:
            sbit_data[vfat][sbit] = {}
            for thr in range(0,256,step):
                sbit_data[vfat][sbit][thr] = {}
                sbit_data[vfat][sbit][thr]["time"] = -9999
                sbit_data[vfat][sbit][thr]["fired"] = -9999

    # Nodes for Sbit counters
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TRIGGER.SBIT_MONITOR.OH_SELECT"), oh_select)
    reset_sbit_monitor_node = get_rwreg_node("BEFE.GEM_AMC.TRIGGER.SBIT_MONITOR.RESET")  # To reset S-bit Monitor
    sbit_monitor_nodes = []
    cluster_count_nodes = []
    for i in range(0,8):
        sbit_monitor_nodes.append(get_rwreg_node("BEFE.GEM_AMC.TRIGGER.SBIT_MONITOR.CLUSTER%d"%i))
        cluster_count_nodes.append(get_rwreg_node("BEFE.GEM_AMC.TRIGGER.OH0.CLUSTER_COUNT_%d_CNT"%i))

    dac_node = {}
    dac = "CFG_THR_ARM_DAC"
    for vfat in vfat_list:
        dac_node[vfat] = get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%d.%s"%(oh_select, vfat, dac))

    print ("\nRunning Sbit Noise Scans for VFATs:")
    print (vfat_list)
    print ("")

    # Looping over VFATs
    for vfat in vfat_list:
        print ("VFAT %02d"%(vfat))
        initial_thr = read_backend_reg(dac_node[vfat])

        # Looping over sbits
        for sbit in sbit_list:
            if sbit=="all":
                print ("  VFAT: %02d, Sbit: all"%(vfat))
            else:
                print ("  VFAT: %02d, Sbit: %d"%(vfat, sbit))

            channel_list = []
            if sbit == "all":
                channel_list = range(0,128)
            else:
                for c in s_bit_cluster_mapping[vfat]:
                    if sbit == s_bit_cluster_mapping[vfat][c]["sbit"]:
                        channel_list.append(int(c))
                if len(channel_list)>2:
                    print (Colors.YELLOW + "Skipping S-bit %02d, more than 2 channels"%sbit + Colors.ENDC)
                    continue
                elif len(channel_list)==1:
                    print (Colors.YELLOW + "S-bit %02d has 1 non-working channel"%sbit + Colors.ENDC)
                elif len(channel_list)==0:
                    print (Colors.YELLOW + "Skipping S-bit %02d, missing both channels"%sbit + Colors.ENDC)
                    continue

            # Unmask channels for this vfat
            for channel in channel_list:
                enableVfatchannel(vfat, oh_select, channel, 0, 0) # unmask channels

            # Looping over threshold
            for thr in range(0,256,step):
                #print ("    Threshold: %d"%thr)
                write_backend_reg(dac_node[vfat], thr)
                sleep(1e-3)

                # Count number of clusters for VFATs in given time
                write_backend_reg(reset_sbit_monitor_node, 1)
                global_reset()
                sleep(runtime)

                cluster_counts = []
                for i in range(0,8):
                    cluster_counts.append(read_backend_reg(cluster_count_nodes[i]))
                cluster_addr_mismatch = 0
                sbit_cluster_address_mismatch = -9999
                for i in range(0,8):
                    sbit_monitor_value = read_backend_reg(sbit_monitor_nodes[i])
                    sbit_cluster_address = sbit_monitor_value & 0x7ff
                    sbit_cluster_size = ((sbit_monitor_value >> 11) & 0x7) + 1
                    if sbit_cluster_address!=0x7ff:
                        cluster_addr_match = 0
                        for channel in channel_list:
                            if sbit_cluster_address == s_bit_cluster_mapping[vfat][channel]["cluster_address"]:
                                cluster_addr_match = 1
                                break
                        if cluster_addr_match == 0:
                            sbit_cluster_address_mismatch = sbit_cluster_address
                            cluster_addr_mismatch = 1
                            break
                if cluster_addr_mismatch == 1:
                    if sbit=="all":
                        print (Colors.YELLOW + "Cluster (address = %d) detected not belonging to VFAT %02d for CFG_THR_ARM_DAC = %d"%(sbit_cluster_address_mismatch, vfat, thr) + Colors.ENDC)
                    else:
                        print (Colors.YELLOW + "Cluster (address = %d) detected not belonging to VFAT %02d Sbit %02d for CFG_THR_ARM_DAC = %d"%(sbit_cluster_address_mismatch, vfat, sbit, thr) + Colors.ENDC)
                    continue

                n_total_clusters = 0
                for i in range (1,8):
                    n_total_clusters += i*cluster_counts[i]

                sbit_data[vfat][sbit][thr]["fired"] = n_total_clusters
                sbit_data[vfat][sbit][thr]["time"] = runtime
                # End of charge loop

            # Mask channels again for this vfat
            for channel in channel_list:
                enableVfatchannel(vfat, oh_select, channel, 1, 0) # mask channels

        # End of sbits loop
        write_backend_reg(dac_node[vfat], initial_thr)
        sleep(1e-3)
        print ("")
    # End of VFAT loop
    print ("")

    # Disable channels on VFATs
    for vfat in vfat_list:
        print("Unconfiguring VFAT %d" % (vfat))
        for channel in range(0,128):
            enableVfatchannel(vfat, oh_select, channel, 0, 0) # unmask all channels
        configureVfat(0, vfat, oh_select, 0)
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.GEM_SYSTEM.VFAT3.SC_ONLY_MODE"), 0)

    # Writing Results
    for vfat in vfat_list:
        for sbit in sbit_list:
            for thr in range(0,256,1):
                if thr not in sbit_data[vfat][sbit]:
                    continue
                if sbit == "all":
                    file_out.write("%d    %s    %d    %d    %f\n"%(vfat, sbit, thr, sbit_data[vfat][sbit][thr]["fired"], sbit_data[vfat][sbit][thr]["time"]))
                else:
                    file_out.write("%d    %d    %d    %d    %f\n"%(vfat, sbit, thr, sbit_data[vfat][sbit][thr]["fired"], sbit_data[vfat][sbit][thr]["time"]))

    print ("")
    file_out.close()


if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="LpGBT VFAT S-Bit Cluster Noise Rate")
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = backend or dryrun")
    parser.add_argument("-y", "--oh_v", action="store", dest="oh_v", default="1", help="oh_v = 1 or 2")
    #parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1")
    #parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0-7 (only needed for backend)")
    parser.add_argument("-v", "--vfats", action="store", dest="vfats", nargs="+", help="vfats = VFAT number (0-23)")
    parser.add_argument("-r", "--use_dac_scan_results", action="store_true", dest="use_dac_scan_results", help="use_dac_scan_results = to use previous DAC scan results for configuration")
    parser.add_argument("-u", "--use_channel_trimming", action="store", dest="use_channel_trimming", help="use_channel_trimming = to use latest trimming results for either options - daq or sbit (default = None)")
    parser.add_argument("-t", "--step", action="store", dest="step", default="1", help="step = Step size for threshold scan (default=1)")
    parser.add_argument("-m", "--time", action="store", dest="time", default="0.001", help="time = time for each elink in sec (default = 0.001 s or 1 ms)")
    args = parser.parse_args()

    if args.system == "chc":
        #print ("Using Rpi CHeeseCake for S-bit test")
        print (Colors.YELLOW + "Only Backend or dryrun supported" + Colors.ENDC)
        sys.exit()
    elif args.system == "backend":
        print ("Using Backend for S-bit test")
        #print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        #sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for S-bit test")
        print (Colors.YELLOW + "Only Backend or dryrun supported" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually running vfat noise rate test")
    else:
        print (Colors.YELLOW + "Only valid options: backend, dryrun" + Colors.ENDC)
        sys.exit()

    if args.oh_v == "1":
        print("Using OH v1")
        oh_v = 1
    elif args.oh_v == "2":
        print("Using OH v2")
        oh_v = 2
    else:
        print(Colors.YELLOW + "Please select either OH v1 or v2" + Colors.ENDC)
        sys.exit()

    if args.ohid is None:
        print(Colors.YELLOW + "Need OHID" + Colors.ENDC)
        sys.exit()
    if int(args.ohid) > 1:
        print(Colors.YELLOW + "Only OHID 0-1 allowed" + Colors.ENDC)
        sys.exit()

    if args.vfats is None:
        print (Colors.YELLOW + "Enter VFAT numbers" + Colors.ENDC)
        sys.exit()
    vfat_list = []
    for v in args.vfats:
        v_int = int(v)
        if v_int not in range(0,24):
            print (Colors.YELLOW + "Invalid VFAT number, only allowed 0-23" + Colors.ENDC)
            sys.exit()
        vfat_list.append(v_int)

    step = int(args.step)
    if step not in range(1,257):
        print (Colors.YELLOW + "Step size can only be between 1 and 256" + Colors.ENDC)
        sys.exit()

    if args.use_channel_trimming is not None:
        if args.use_channel_trimming not in ["daq", "sbit"]:
            print (Colors.YELLOW + "Only allowed options for use_channel_trimming: daq or sbit" + Colors.ENDC)
            sys.exit()

    sbit_list = []
    for s in range(0,64):
        sbit_list.append(s)
    sbit_list = ["all"] + sbit_list
    s_bit_cluster_mapping = {}
    print ("")
    if not os.path.isdir("vfat_data/vfat_sbit_monitor_cluster_mapping_results"):
        print (Colors.YELLOW + "Run the S-bit cluster mapping first" + Colors.ENDC)
        sys.exit()
    list_of_files = glob.glob("vfat_data/vfat_sbit_monitor_cluster_mapping_results/*.txt")
    if len(list_of_files)==0:
        print (Colors.YELLOW + "Run the S-bit cluster mapping first" + Colors.ENDC)
        sys.exit()
    elif len(list_of_files)>1:
        print ("Mutliple S-bit cluster mapping results found, using latest file")
    latest_file = max(list_of_files, key=os.path.getctime)
    print ("Using S-bit cluster mapping file: %s\n"%(latest_file.split("vfat_data/vfat_sbit_monitor_cluster_mapping_results/")[1]))
    file_in = open(latest_file)
    for line in file_in.readlines():
        if "VFAT" in line:
            continue
        if len(line.split())==0:
            continue
        vfat = int(line.split()[0])
        channel = int(line.split()[1])
        sbit = int(line.split()[2])
        cluster_count = line.split()[3]
        cluster_size = int(line.split()[4].split(",")[0])
        cluster_address = int(line.split()[4].split(",")[1])
        if cluster_address == 2047:
            cluster_address = -9999
        if vfat not in s_bit_cluster_mapping:
            s_bit_cluster_mapping[vfat] = {}
        s_bit_cluster_mapping[vfat][channel] = {}
        s_bit_cluster_mapping[vfat][channel]["sbit"] = sbit
        s_bit_cluster_mapping[vfat][channel]["cluster_address"] = cluster_address
    file_in.close()

    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML(oh_v)
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system)
    initialize_vfat_config(int(args.ohid), args.use_dac_scan_results, args.use_channel_trimming)
    print("Initialization Done\n")

    # Running Sbit Noise Rate
    try:
        lpgbt_vfat_sbit(args.system, int(args.ohid), vfat_list, sbit_list, step, float(args.time), s_bit_cluster_mapping)
    except KeyboardInterrupt:
        print (Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()




