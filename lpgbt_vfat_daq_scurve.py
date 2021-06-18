from rw_reg_lpgbt import *
from time import sleep, time
import datetime
import sys
import argparse
import random
from lpgbt_vfat_config import configureVfat, enableVfatchannel
from collections import OrderedDict


def lpgbt_vfat_scurve(system, oh_select, vfat_list, step, nl1a, l1a_bxgap):
    if not os.path.exists("daq_scurve_results"):
        os.makedirs("daq_scurve_results")
    now = str(datetime.datetime.now())[:16]
    now = now.replace(":", "_")
    now = now.replace(" ", "_")
    foldername = "daq_scurve_results/"
    filename = foldername + "vfat_scurve_" + now + ".txt"
    file_out = open(filename,"w+")
    file_out.write("vfatN    ch_inj    charge    fired    events\n")

    vfat_oh_link_reset()
    global_reset()
    sleep(0.1)

    daq_data = {}
    cal_mode = {}
    # Check ready and get nodes
    for vfat in vfat_list:
        lpgbt, gbt_select, elink, gpio = vfat_to_gbt_elink_gpio(vfat)
        check_lpgbt_link_ready(oh_select, gbt_select)

        print("Configuring VFAT %d" % (vfat))
        configureVfat(1, vfat, oh_select, 0)
        for channel in range(0,128):
            enableVfatchannel(vfat, oh_select, channel, 1, 0) # mask all channels and disable calpulsing
        cal_mode[vfat] = read_backend_reg(get_rwreg_node("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_MODE"% (oh_select, vfat)))

        link_good_node = get_rwreg_node("GEM_AMC.OH_LINKS.OH%d.VFAT%d.LINK_GOOD" % (oh_select, vfat))
        sync_error_node = get_rwreg_node("GEM_AMC.OH_LINKS.OH%d.VFAT%d.SYNC_ERR_CNT" % (oh_select, vfat))
        link_good = read_backend_reg(link_good_node)
        sync_err = read_backend_reg(sync_error_node)
        if system!="dryrun" and (link_good == 0 or sync_err > 0):
            print (Colors.RED + "Link is bad for VFAT# %02d"%(vfat) + Colors.ENDC)
            rw_terminate()

        daq_data[vfat] =  OrderedDict()
        for channel in range(0,128):
            daq_data[vfat][channel] = OrderedDict()
            for c in range(0,256,step):
                if cal_mode[vfat] == 1:
                    charge = 255 - c
                else:
                    charge = c
                daq_data[vfat][channel][charge] = OrderedDict()
                daq_data[vfat][channel][charge]["events"] = -9999
                daq_data[vfat][channel][charge]["fired"] = -9999

    # Configure TTC generator
    write_backend_reg(get_rwreg_node("GEM_AMC.TTC.GENERATOR.SINGLE_HARD_RESET"), 1)
    write_backend_reg(get_rwreg_node("GEM_AMC.TTC.GENERATOR.RESET"), 1)
    write_backend_reg(get_rwreg_node("GEM_AMC.TTC.GENERATOR.ENABLE"), 1)
    write_backend_reg(get_rwreg_node("GEM_AMC.TTC.GENERATOR.CYCLIC_L1A_GAP"), l1a_bxgap)
    write_backend_reg(get_rwreg_node("GEM_AMC.TTC.GENERATOR.CYCLIC_L1A_COUNT"), nl1a)
    write_backend_reg(get_rwreg_node("GEM_AMC.TTC.GENERATOR.CYCLIC_CALPULSE_TO_L1A_GAP"), 50) # 50 BX between Calpulse and L1A

    # Setup the DAQ monitor
    write_backend_reg(get_rwreg_node("GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.ENABLE"), 1)
    write_backend_reg(get_rwreg_node("GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.VFAT_CHANNEL_GLOBAL_OR"), 0)

    cyclic_running_node = get_rwreg_node("GEM_AMC.TTC.GENERATOR.CYCLIC_RUNNING")
    l1a_node = get_rwreg_node("GEM_AMC.TTC.CMD_COUNTERS.L1A")
    calpulse_node = get_rwreg_node("GEM_AMC.TTC.CMD_COUNTERS.CALPULSE")

    print ("\nRunning SCurves for %.2e L1A cycles for VFATs:" % (nl1a))
    print (vfat_list)
    print ("")

    # Looping over charge
    for c in range(0,256,step):
        if cal_mode[vfat] == 1:
            charge = 255 - c
        else:
            charge = c
        print ("Injected Charge: %d"%charge)
       	for vfat in vfat_list:
            lpgbt, gbt_select, elink, gpio = vfat_to_gbt_elink_gpio(vfat)
            write_backend_reg(get_rwreg_node("GEM_AMC.OH.OH%i.GEB.VFAT%d.CFG_CAL_DAC"%(oh_select, vfat)), c)

        # Looping over channels
        for channel in range(0, 128):
            for vfat in vfat_list:
                lpgbt, gbt_select, elink, gpio = vfat_to_gbt_elink_gpio(vfat)
                write_backend_reg(get_rwreg_node("GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.OH_SELECT"), oh_select)
                enableVfatchannel(vfat, oh_select, channel, 0, 1) # unmask channel and enable calpulsing

            write_backend_reg(get_rwreg_node("GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.VFAT_CHANNEL_SELECT"), channel)
            write_backend_reg(get_rwreg_node("GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.RESET"), 1)
            write_backend_reg(get_rwreg_node("GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.ENABLE"), 1)

		    # Start the cyclic generator
            l1a_counter_initial = read_backend_reg(l1a_node)
            calpulse_counter_initial = read_backend_reg(calpulse_node)
            write_backend_reg(get_rwreg_node("GEM_AMC.TTC.GENERATOR.ENABLE"), 1)
            write_backend_reg(get_rwreg_node("GEM_AMC.TTC.GENERATOR.CYCLIC_START"), 1)
            cyclic_running = 1
            while (cyclic_running):
                cyclic_running = read_backend_reg(cyclic_running_node)
            # Stop the cyclic generator
            write_backend_reg(get_rwreg_node("GEM_AMC.TTC.GENERATOR.RESET"), 1)
            l1a_counter = read_backend_reg(l1a_node) - l1a_counter_initial
            calpulse_counter = read_backend_reg(calpulse_node) - calpulse_counter_initial
            write_backend_reg(get_rwreg_node("GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.ENABLE"), 0)

            # Looping over VFATs
            for vfat in vfat_list:
                lpgbt, gbt_select, elink, gpio = vfat_to_gbt_elink_gpio(vfat)
                daq_data[vfat][channel][charge]["events"] = read_backend_reg(get_rwreg_node("GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.VFAT%d.GOOD_EVENTS_COUNT"%(vfat)))
                daq_data[vfat][channel][charge]["fired"] = read_backend_reg(get_rwreg_node("GEM_AMC.GEM_TESTS.VFAT_DAQ_MONITOR.VFAT%d.CHANNEL_FIRE_COUNT"%(vfat)))
                enableVfatchannel(vfat, oh_select, channel, 1, 0) # mask channel and disable calpulsing
            # End of VFAT loop
        # End of channel loop
    # End of charge loop
    print ("")

    # Disable channels on VFATs
    for vfat in vfat_list:
        lpgbt, gbt_select, elink, gpio = vfat_to_gbt_elink_gpio(vfat)
        enable_channel = 0
        print("Unconfiguring VFAT %d" % (vfat))
        for channel in range(0,128):
            enableVfatchannel(vfat, oh_select, channel, 0, 0) # disable calpulsing on channel 0 for this VFAT
        configureVfat(0, vfat, oh_select, 0)

    # Writing Results
    for vfat in daq_data:
        for channel in daq_data[vfat]:
            for charge in daq_data[vfat][channel]:
                file_out.write("%d    %d    %d    %d    %d\n"%(vfat, channel, charge, daq_data[vfat][channel][charge]["fired"], daq_data[vfat][channel][charge]["events"]))

    print ("")
    file_out.close()
if __name__ == '__main__':

    # Parsing arguments
    parser = argparse.ArgumentParser(description='LpGBT VFAT SCurve')
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = backend or dryrun")
    #parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1")
    #parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0-7 (only needed for backend)")
    parser.add_argument("-v", "--vfats", action="store", nargs='+', dest="vfats", help="vfats = list of VFAT numbers (0-23)")
    parser.add_argument("-t", "--step", action="store", dest="step", default="1", help="step = Step size for SCurve scan (default=1)")
    parser.add_argument("-n", "--nl1a", action="store", dest="nl1a", help="nl1a = fixed number of L1A cycles")
    parser.add_argument("-b", "--bxgap", action="store", dest="bxgap", default="500", help="bxgap = Nr. of BX between two L1A's (default = 500 i.e. 12.5 us)")
    parser.add_argument("-a", "--addr", action="store", nargs='+', dest="addr", help="addr = list of VFATs to enable HDLC addressing")
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

    nl1a = 0
    if args.nl1a is not None:
        nl1a = int(args.nl1a)
        if nl1a > (2**24 - 1):
            print (Colors.YELLOW + "Number of L1A cycles can be maximum 1.68e7. Using time option for longer tests" + Colors.ENDC)
            sys.exit()
    if nl1a==0:
        print (Colors.YELLOW + "Enter number of L1A cycles" + Colors.ENDC)
        sys.exit()

    l1a_bxgap = int(args.bxgap)
    l1a_timegap = l1a_bxgap * 25 * 0.001 # in microseconds
    if l1a_bxgap<25:
        print (Colors.YELLOW + "Gap between L1A's should be at least 25 BX to read out enitre DAQ data packets" + Colors.ENDC)
        sys.exit()
    else:
        print ("Gap between consecutive L1A or CalPulses = %d BX = %.2f us" %(l1a_bxgap, l1a_timegap))
        
    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML()
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system)
    print("Initialization Done\n")

    if args.addr is not None:
        print ("Enabling VFAT addressing for plugin cards on slots: ")
        print (args.addr)
        addr_list = []
        for a in args.addr:
            a_int = int(a)
            if a_int not in range(0,24):
                print (Colors.YELLOW + "Invalid VFAT number for HDLC addressing, only allowed 0-23" + Colors.ENDC)
                sys.exit()
            addr_list.append(a_int)
        enable_hdlc_addressing(addr_list)
    
    # Running Phase Scan
    try:
        lpgbt_vfat_scurve(args.system, int(args.ohid), vfat_list, step, nl1a, l1a_bxgap)
    except KeyboardInterrupt:
        print (Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()




