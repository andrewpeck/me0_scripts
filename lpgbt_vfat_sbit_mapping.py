from rw_reg_lpgbt import *
from time import sleep, time
import datetime
import sys
import argparse
import random
import json
from lpgbt_vfat_config import initialize_vfat_config, configureVfat, enableVfatchannel


def lpgbt_vfat_sbit(system, oh_select, vfat_list, nl1a, l1a_bxgap, set_cal_mode, cal_dac):
    print ("LPGBT VFAT S-Bit Mapping\n")

    vfat_oh_link_reset()
    global_reset()
    sleep(0.1)
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.GEM_SYSTEM.VFAT3.SC_ONLY_MODE"), 1)

    # Configure TTC generator
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.RESET"), 1)
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.ENABLE"), 1)
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.CYCLIC_L1A_GAP"), l1a_bxgap)
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.CYCLIC_L1A_COUNT"), nl1a)
    if l1a_bxgap >= 40:
        write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.CYCLIC_CALPULSE_TO_L1A_GAP"), 25)
    else:
        write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.CYCLIC_CALPULSE_TO_L1A_GAP"), 2)

    # Reading S-bit counter
    cyclic_running_node = get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.CYCLIC_RUNNING")
    l1a_node = get_rwreg_node("BEFE.GEM_AMC.TTC.CMD_COUNTERS.L1A")
    calpulse_node = get_rwreg_node("BEFE.GEM_AMC.TTC.CMD_COUNTERS.CALPULSE")

    elink_sbit_select_node = get_rwreg_node("BEFE.GEM_AMC.SBIT_ME0.TEST_SEL_ELINK_SBIT_ME0") # Node for selecting Elink to count
    channel_sbit_select_node = get_rwreg_node("BEFE.GEM_AMC.SBIT_ME0.TEST_SEL_SBIT_ME0") # Node for selecting S-bit to count
    elink_sbit_counter_node = get_rwreg_node("BEFE.GEM_AMC.SBIT_ME0.TEST_SBIT0XE_COUNT_ME0") # S-bit counter for elink
    channel_sbit_counter_node = get_rwreg_node("BEFE.GEM_AMC.SBIT_ME0.TEST_SBIT0XS_COUNT_ME0") # S-bit counter for specific channel
    reset_sbit_counter_node = get_rwreg_node("BEFE.GEM_AMC.SBIT_ME0.CTRL.SBIT_TEST_RESET")  # To reset all S-bit counters

    s_bit_channel_mapping = {}

    for vfat in vfat_list:
        print ("Testing VFAT#: %02d" %(vfat))
        print ("")
        lpgbt, gbt_select, elink_daq, gpio = vfat_to_gbt_elink_gpio(vfat)
        check_lpgbt_link_ready(oh_select, gbt_select)

        link_good = read_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH_LINKS.OH%d.VFAT%d.LINK_GOOD" % (oh_select, vfat)))
        sync_err = read_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH_LINKS.OH%d.VFAT%d.SYNC_ERR_CNT" % (oh_select, vfat)))
        if system!="dryrun" and (link_good == 0 or sync_err > 0):
            print (Colors.RED + "Link is bad for VFAT# %02d"%(vfat) + Colors.ENDC)
            rw_terminate()

        write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.SBIT_ME0.TEST_SEL_VFAT_SBIT_ME0"), vfat) # Select VFAT for reading S-bits

        # Configure the pulsing VFAT
        print("Configuring VFAT %02d" % (vfat))
        configureVfat(1, vfat, oh_select, 0)
        if set_cal_mode == "voltage":
            write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_MODE"% (oh_select, vfat)), 1)
            write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_DUR"% (oh_select, vfat)), 200)
        elif set_cal_mode == "current":
            write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_MODE"% (oh_select, vfat)), 2)
            write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_DUR"% (oh_select, vfat)), 0)
        else:
            write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_MODE"% (oh_select, vfat)), 0)
            write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_DUR"% (oh_select, vfat)), 0)
        write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_DAC"% (oh_select, vfat)), cal_dac)
        for i in range(128):
            enableVfatchannel(vfat, oh_select, i, 1, 0) # mask all channels and disable calpulsing
        print ("")

        s_bit_channel_mapping[vfat] = {}
        # Looping over all 8 elinks
        for elink in range(0,8):
            print ("Phase scan for S-bits in ELINK# %02d" %(elink))
            write_backend_reg(elink_sbit_select_node, elink) # Select elink for S-bit counter

            s_bit_channel_mapping[vfat][elink] = {}
            s_bit_matches = {}
            # Looping over all channels in that elink
            for channel in range(elink*16,elink*16+16):
                # Enabling the pulsing channel
                enableVfatchannel(vfat, oh_select, channel, 0, 1) # unmask this channel and enable calpulsing

                channel_sbit_counter_final = {}
                sbit_channel_match = 0
                s_bit_channel_mapping[vfat][elink][channel] = -9999

                # Looping over all s-bits in that elink
                for sbit in range(elink*8,elink*8+8):
                    # Reset L1A, CalPulse and S-bit counters
                    global_reset()
                    write_backend_reg(reset_sbit_counter_node, 1)

                    write_backend_reg(channel_sbit_select_node, sbit) # Select S-bit for S-bit counter
                    s_bit_matches[sbit] = 0

                    # Start the cyclic generator
                    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.CYCLIC_START"), 1)
                    cyclic_running = read_backend_reg(cyclic_running_node)
                    while cyclic_running:
                        cyclic_running = read_backend_reg(cyclic_running_node)

                    # Stop the cyclic generator
                    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.RESET"), 1)

                    elink_sbit_counter_final = read_backend_reg(elink_sbit_counter_node)
                    l1a_counter = read_backend_reg(l1a_node)
                    calpulse_counter = read_backend_reg(calpulse_node)

                    if system!="dryrun" and l1a_counter != nl1a:
                        print (Colors.RED + "ERROR: Number of L1As incorrect" + Colors.ENDC)
                        rw_terminate()
                    if system!="dryrun" and elink_sbit_counter_final == 0:
                        print (Colors.YELLOW + "WARNING: Elink %02d did not register any S-bit for calpulse on channel %02d"%(elink, channel) + Colors.ENDC)
                        s_bit_channel_mapping[vfat][elink][channel] = -9999
                        break
                    channel_sbit_counter_final[sbit] = read_backend_reg(channel_sbit_counter_node)

                    if channel_sbit_counter_final[sbit] > 0:
                        if sbit_channel_match == 1:
                            print (Colors.YELLOW + "WARNING: Multiple S-bits registered hits for calpulse on channel %02d"%(channel) + Colors.ENDC)
                            s_bit_channel_mapping[vfat][elink][channel] = -9999
                            break
                        if s_bit_matches[sbit] >= 2:
                            print (Colors.YELLOW + "WARNING: S-bit %02d already matched to 2 channels"%(sbit) + Colors.ENDC)
                            s_bit_channel_mapping[vfat][elink][channel] = -9999
                            break
                        if s_bit_matches[sbit] == 1:
                            if s_bit_channel_mapping[vfat][elink][channel-1] != sbit:
                                print (Colors.YELLOW + "WARNING: S-bit %02d matched to a different channel than the previous one"%(sbit) + Colors.ENDC)
                                s_bit_channel_mapping[vfat][elink][channel] = -9999
                                break
                            if channel%2==0:
                                print (Colors.YELLOW + "WARNING: S-bit %02d already matched to an earlier odd numbered channel"%(sbit) + Colors.ENDC)
                                s_bit_channel_mapping[vfat][elink][channel] = -9999
                                break
                        s_bit_channel_mapping[vfat][elink][channel] = sbit
                        sbit_channel_match = 1
                        s_bit_matches[sbit] += 1
                # End of S-bit loop for this channel

                # Disabling the pulsing channels
                enableVfatchannel(vfat, oh_select, channel, 1, 0) # mask this channel and disable calpulsing
            # End of Channel loop

            print ("")
        # End of Elink loop

        # Unconfigure the pulsing VFAT
        print("Unconfiguring VFAT %02d" % (vfat))
        configureVfat(0, vfat, oh_select, 0)
        print ("")
        # End of VFAT loop
    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.TTC.GENERATOR.ENABLE"), 0)

    if not os.path.isdir("vfat_data/vfat_sbit_mapping_results"):
        os.mkdir("vfat_data/vfat_sbit_mapping_results")
    now = str(datetime.datetime.now())[:16]
    now = now.replace(":", "_")
    now = now.replace(" ", "_")
    filename = "vfat_data/vfat_sbit_mapping_results/ME0_OH%d_vfat_sbit_mapping_results_"%oh_select+now+".py"
    with open(filename, "w") as file:
        file.write(json.dumps(s_bit_channel_mapping))

    print ("S-bit Mapping Results: \n")
    for vfat in s_bit_channel_mapping:
        print ("VFAT %02d: "%(vfat))
        for elink in s_bit_channel_mapping[vfat]:
            print ("  ELINK %02d: "%(elink))
            for channel in s_bit_channel_mapping[vfat][elink]:
                if s_bit_channel_mapping[vfat][elink][channel] == -9999:
                    print (Colors.RED + "    Channel %02d:  S-bit %02d"%(channel, s_bit_channel_mapping[vfat][elink][channel]) + Colors.ENDC)
                else:
                    print (Colors.GREEN + "    Channel %02d:  S-bit %02d"%(channel, s_bit_channel_mapping[vfat][elink][channel]) + Colors.ENDC)
        print ("")

    write_backend_reg(get_rwreg_node("BEFE.GEM_AMC.GEM_SYSTEM.VFAT3.SC_ONLY_MODE"), 0)
    print ("\nS-bit mapping done\n")

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="LpGBT VFAT S-Bit Mapping")
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = backend or dryrun")
    parser.add_argument("-y", "--oh_v", action="store", dest="oh_v", help="oh_v = 1 or 2")
    #parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1")
    #parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0-7 (only needed for backend)")
    parser.add_argument("-v", "--vfats", action="store", nargs="+", dest="vfats", help="vfats = list of VFAT numbers (0-23)")
    parser.add_argument("-r", "--use_dac_scan_results", action="store_true", dest="use_dac_scan_results", help="use_dac_scan_results = to use previous DAC scan results for configuration")
    parser.add_argument("-u", "--use_channel_trimming", action="store", dest="use_channel_trimming", help="use_channel_trimming = to use latest trimming results for either options - daq or sbit (default = None)")
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

    if args.use_channel_trimming is not None:
        if args.use_channel_trimming not in ["daq", "sbit"]:
            print (Colors.YELLOW + "Only allowed options for use_channel_trimming: daq or sbit" + Colors.ENDC)
            sys.exit()

    nl1a = 100 # Nr. of L1As
    l1a_bxgap = 100 # Gap between 2 L1As in nr. of BXs
    set_cal_mode = "current"
    cal_dac = 150 # should be 50 for voltage pulse mode

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
        lpgbt_vfat_sbit(args.system, int(args.ohid), vfat_list, nl1a, l1a_bxgap, set_cal_mode, cal_dac)
    except KeyboardInterrupt:
        print (Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()




