from rw_reg_lpgbt import *
from time import sleep, time
import datetime
import sys
import argparse
import random
from lpgbt_vfat_config import initialize_vfat_config, configureVfat, enableVfatchannel


def lpgbt_vfat_hitmap(system, oh_select, vfat_list, noise, low_thresh, set_cal_mode, cal_dac, nl1a, l1a_bxgap):
    if not os.path.exists("vfat_data/vfat_daq_hitmap_results"):
        os.makedirs("vfat_data/vfat_daq_hitmap_results")
    now = str(datetime.datetime.now())[:16]
    now = now.replace(":", "_")
    now = now.replace(" ", "_")
    foldername = "vfat_data/vfat_daq_hitmap_results/"
    filename = ""
    if not noise:
        filename = foldername + "ME0_OH%d_vfat_hitmap_caldac%d_"%(oh_select,cal_dac) + now + ".txt"
    else:
        filename = foldername + "ME0_OH%d_vfat_noisemap_"%oh_select + now + ".txt"
    file_out = open(filename,"w+")
    file_out.write("vfat    channel    fired    events\n")

    vfat_oh_link_reset()
    global_reset()
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.GEM_SYSTEM.VFAT3.SC_ONLY_MODE"), 0)
    sleep(0.1)

    daq_data = {}
    cal_mode = {}
    channel_list = range(0,128)
    # Check ready and get nodes
    for vfat in vfat_list:
        lpgbt, gbt_select, elink, gpio = vfat_to_gbt_elink_gpio(vfat)
        check_lpgbt_link_ready(oh_select, gbt_select)

        print("Configuring VFAT %d" % (vfat))
        if args.noise and args.low_thresh:
            configureVfat(1, vfat, oh_select, 1)
        else:
            configureVfat(1, vfat, oh_select, 0)
        write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_LATENCY"% (oh_select, vfat)), 18)
        if set_cal_mode == "voltage":
            write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_MODE"% (oh_select, vfat)), 1)
            write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_DUR"% (oh_select, vfat)), 200)
        elif set_cal_mode == "current":
            write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_MODE"% (oh_select, vfat)), 2)
            write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_DUR"% (oh_select, vfat)), 0)
        else:
            write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_MODE"% (oh_select, vfat)), 0)
            write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_DUR"% (oh_select, vfat)), 0)
            
        for channel in channel_list:
            enableVfatchannel(vfat, oh_select, channel, 1, 0) # mask all channels and disable calpulsing
        cal_mode[vfat] = read_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_MODE"% (oh_select, vfat)))

        link_good_node = get_rwreg_node("BEFE.GEM_AMC.OH_LINKS.OH%d.VFAT%d.LINK_GOOD" % (oh_select, vfat))
        sync_error_node = get_rwreg_node("BEFE.GEM_AMC.OH_LINKS.OH%d.VFAT%d.SYNC_ERR_CNT" % (oh_select, vfat))
        link_good = read_backend_reg(link_good_node)
        sync_err = read_backend_reg(sync_error_node)
        if system!="dryrun" and (link_good == 0 or sync_err > 0):
            print (Colors.RED + "Link is bad for VFAT# %02d"%(vfat) + Colors.ENDC)
            rw_terminate()

        daq_data[vfat] = {}
        for channel in channel_list:
            daq_data[vfat][channel] = {}
            daq_data[vfat][channel]["events"] = -9999
            daq_data[vfat][channel]["fired"] = -9999

    # Configure TTC generator
    #write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.SINGLE_HARD_RESET"), 1)
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.RESET"), 1)
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.ENABLE"), 1)
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.CYCLIC_L1A_GAP"), l1a_bxgap)
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.CYCLIC_L1A_COUNT"), nl1a)
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.CYCLIC_CALPULSE_TO_L1A_GAP"), 25)

    # Setup the DAQ monitor
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.ENABLE"), 1)
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.VFAT_CHANNEL_GLOBAL_OR"), 0)
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.OH_SELECT"), oh_select)
    daq_monitor_reset_node = get_rwreg_node("BEFE.GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.RESET")
    daq_monitor_enable_node = get_rwreg_node("BEFE.GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.ENABLE")
    daq_monitor_select_node = get_rwreg_node("BEFE.GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.VFAT_CHANNEL_SELECT")

    dac_node = {}
    daq_monitor_event_count_node = {}
    daq_monitor_fire_count_node = {}
    dac = "CFG_CAL_DAC"
    for vfat in vfat_list:
        if noise:
            if cal_mode[vfat] == 1:
                cal_dac = 255
            else:
                cal_dac = 0
        write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%d.%s"%(oh_select, vfat, dac)), cal_dac)
        daq_monitor_event_count_node[vfat] = get_rwreg_node("BEFE.GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.VFAT%d.GOOD_EVENTS_COUNT"%(vfat))
        daq_monitor_fire_count_node[vfat] = get_rwreg_node("BEFE.GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.VFAT%d.CHANNEL_FIRE_COUNT"%(vfat))

    ttc_reset_node = get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.RESET")
    ttc_cyclic_start_node = get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.CYCLIC_START")
    cyclic_running_node = get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.CYCLIC_RUNNING")

    print ("\nRunning Hit Map Scan for %.2e L1A cycles for VFATs:" % (nl1a))
    print (vfat_list)
    print ("")

    # Looping over channels
    for channel in channel_list:
        print ("Channel: %d"%channel)
        for vfat in vfat_list:
            enableVfatchannel(vfat, oh_select, channel, 0, 1) # unmask channel and enable calpulsing
        write_backend_reg(daq_monitor_select_node, channel)

        write_backend_reg(daq_monitor_reset_node, 1)
        write_backend_reg(daq_monitor_enable_node, 1)

        # Start the cyclic generator
        write_backend_reg(ttc_cyclic_start_node, 1)
        cyclic_running = 1
        while (cyclic_running):
            cyclic_running = read_backend_reg(cyclic_running_node)
        # Stop the cyclic generator
        write_backend_reg(ttc_reset_node, 1)
        write_backend_reg(daq_monitor_enable_node, 0)

        # Looping over VFATs
        for vfat in vfat_list:
            daq_data[vfat][channel]["events"] = read_backend_reg(daq_monitor_event_count_node[vfat])
            daq_data[vfat][channel]["fired"] = read_backend_reg(daq_monitor_fire_count_node[vfat])
        # End of VFAT loop
        
        for vfat in vfat_list:
            enableVfatchannel(vfat, oh_select, channel, 1, 0) # mask channel and disable calpulsing
    # End of channel loop
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.ENABLE"), 0)
    print ("")

    # Disable channels on VFATs
    for vfat in vfat_list:
        enable_channel = 0
        print("Unconfiguring VFAT %d" % (vfat))
        for channel in range(0,128):
            enableVfatchannel(vfat, oh_select, channel, 0, 0) # disable calpulsing on all channels for this VFAT
        configureVfat(0, vfat, oh_select, 0)

    # Writing Results
    for vfat in vfat_list:
        for channel in channel_list:
            file_out.write("%d    %d    %d    %d\n"%(vfat, channel, daq_data[vfat][channel]["fired"], daq_data[vfat][channel]["events"]))

    print ("")
    file_out.close()
if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="LpGBT VFAT Hit Map using DAQ data")
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = backend or dryrun")
    parser.add_argument("-y", "--oh_v", action="store", dest="oh_v", help="oh_v = 1 or 2")
    #parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1")
    #parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0-7 (only needed for backend)")
    parser.add_argument("-v", "--vfats", action="store", nargs="+", dest="vfats", help="vfats = list of VFAT numbers (0-23)")
    parser.add_argument("-z", "--noise", action="store_true", dest="noise", help="if you want noise map instead of hit map")
    parser.add_argument("-l", "--low_thresh", action="store_true", dest="low_thresh", help="if you want 0 thhreshold for VFATs to get noise")
    parser.add_argument("-m", "--cal_mode", action="store", dest="cal_mode", default = "voltage", help="cal_mode = voltage or current (default = voltage)")
    parser.add_argument("-d", "--cal_dac", action="store", dest="cal_dac", help="cal_dac = Value of CAL_DAC register (default = 50 for voltage pulse mode and 150 for current pulse mode)")
    parser.add_argument("-r", "--use_dac_scan_results", action="store_true", dest="use_dac_scan_results", help="use_dac_scan_results = to use previous DAC scan results for configuration")
    parser.add_argument("-u", "--use_channel_trimming", action="store", dest="use_channel_trimming", help="use_channel_trimming = to use latest trimming results for either options - daq or sbit (default = None)")
    parser.add_argument("-n", "--nl1a", action="store", dest="nl1a", help="nl1a = fixed number of L1A cycles")
    parser.add_argument("-b", "--bxgap", action="store", dest="bxgap", default="500", help="bxgap = Nr. of BX between two L1As (default = 500 i.e. 12.5 us)")
    args = parser.parse_args()

    if args.system == "chc":
        #print ("Using Rpi CHeeseCake for configuration")
        print (Colors.YELLOW + "Only Backend or dryrun supported" + Colors.ENDC)
        sys.exit()
    elif args.system == "backend":
        print ("Using Backend for configuration")
        #print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        #sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for configuration")
        print (Colors.YELLOW + "Only Backend or dryrun supported" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually running vfat bert")
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

    if not args.noise and args.low_thresh:
        print (Colors.YELLOW + "VFATs can be configured with 0 threshold only for noise map" + Colors.ENDC)
        sys.exit()

    if args.noise:
        print ("Hitmap without Calpulse, just noise")
        
    cal_mode = args.cal_mode
    if cal_mode not in ["voltage", "current"]:
        print (Colors.YELLOW + "CAL_MODE must be either voltage or current" + Colors.ENDC)
        sys.exit()

    cal_dac = -9999
    if args.cal_dac is None:
        if cal_mode == "voltage":
            cal_dac = 50
        elif cal_mode == "current":
            cal_dac = 150
    else:
        cal_dac = int(args.cal_dac)
        if cal_dac > 255 or cal_dac < 0:
            print (Colors.YELLOW + "CAL_DAC must be between 0 and 255" + Colors.ENDC)
            sys.exit()

    nl1a = 0
    if args.nl1a is not None:
        nl1a = int(args.nl1a)
        if nl1a > (2**32 - 1):
            print (Colors.YELLOW + "Number of L1A cycles can be maximum 4.29e9" + Colors.ENDC)
            sys.exit()
    if nl1a==0:
        print (Colors.YELLOW + "Enter number of L1A cycles" + Colors.ENDC)
        sys.exit()

    l1a_bxgap = int(args.bxgap)
    l1a_timegap = l1a_bxgap * 25 * 0.001 # in microseconds
    if l1a_bxgap<25:
        print (Colors.YELLOW + "Gap between L1As should be at least 25 BX to read out enitre DAQ data packets" + Colors.ENDC)
        sys.exit()
    else:
        print ("Gap between consecutive L1A or CalPulses = %d BX = %.2f us" %(l1a_bxgap, l1a_timegap))

    if args.use_channel_trimming is not None:
        if args.use_channel_trimming not in ["daq", "sbit"]:
            print (Colors.YELLOW + "Only allowed options for use_channel_trimming: daq or sbit" + Colors.ENDC)
            sys.exit()

    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML(oh_v)
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system, oh_v)
    initialize_vfat_config(int(args.ohid), args.use_dac_scan_results, args.use_channel_trimming)
    print("Initialization Done\n")

    # Running Phase Scan
    try:
        lpgbt_vfat_hitmap(args.system, int(args.ohid), vfat_list, args.noise, args.low_thresh, cal_mode, cal_dac, nl1a, l1a_bxgap)
    except KeyboardInterrupt:
        print (Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()




