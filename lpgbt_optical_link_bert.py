from rw_reg_lpgbt import *
from time import sleep
import sys
import argparse

PRBS_generator_serializer = {}
PRBS_generator_serializer["DATA"] = 0x0 # Normal mode of operation
PRBS_generator_serializer["PRBS7"] = 0x1 # PRBS7 test pattern (x7 + x6 + 1)
PRBS_generator_serializer["PRBS15"] = 0x2 # PRBS15 test pattern (x15 + x14 + 1)
PRBS_generator_serializer["PRBS23"] = 0x3 # PRBS23 test pattern (x23 + x18 + 1)
PRBS_generator_serializer["PRBS31"] = 0x4 # PRBS31 test pattern (x31 + x28 + 1)
PRBS_generator_serializer["CLK5G12"] = 0x5 # 5.12 GHz clock pattern (in 5Gbps mode it will produce only 2.56 GHz)
PRBS_generator_serializer["CLK2G56"] = 0x6 # 2.56 GHz clock pattern
PRBS_generator_serializer["CLK1G28"] = 0x7 # 1.28 GHz clock pattern
PRBS_generator_serializer["CLK40M"] = 0x8 # 40 MHz clock pattern
PRBS_generator_serializer["DLFRAME_10G24"] = 0x9 # Loop back, downlink frame repeated 4 times
PRBS_generator_serializer["DLFRAME_5G12"] = 0xa # Loop back, downlink frame repeated 2 times, each bit repeated 2 times
PRBS_generator_serializer["DLFRAME_2G56"] = 0xb # Loop back, downlink frame repeated 1 times, each bit repeated 4 times
PRBS_generator_serializer["CONST_PATTERN"] = 0xc # 8 x DPDataPattern[31:0]
#PRBS_generator_serializer[""] = 0xd # Reserved
#PRBS_generator_serializer[""] = 0xe # Reserved
#PRBS_generator_serializer[""] = 0xf # Reserved

PRBS_generator_uplink = {}
PRBS_generator_uplink["EPORTRX_DATA"] = 0x0 # Normal mode of operation, data from ePortRx
PRBS_generator_uplink["PRBS7"] = 0x1 # PRBS7 test pattern
PRBS_generator_uplink["BIN_CNTR_UP"] = 0x2 # Binary counter counting up
PRBS_generator_uplink["BIN_CNTR_DOWN"] = 0x3 # Binary counter counting down
PRBS_generator_uplink["CONST_PATTERN"] = 0x4 # Constant pattern (DPDataPattern[31:0])
PRBS_generator_uplink["CONST_PATTERN_INV"] = 0x5 # Constant pattern inverted (~DPDataPattern[31:0])
PRBS_generator_uplink["DLDATA_LOOPBACK"] = 0x6 # Loop back, downlink frame data
#PRBS_generator_uplink[""] = 0x7 # Reserved

PRBS_generator_downlink = {}
PRBS_generator_downlink["LINK_DATA"] = 0x0 # Normal mode of operation, data from the downlink data frame
PRBS_generator_downlink["PRBS7"] = 0x1 # PRBS7 patter on each channel
PRBS_generator_downlink["BIN_CNTR_UP"] = 0x2 # 	Binary counter counting up on each channel
PRBS_generator_downlink["CONST_PATTERN"] = 0x3 # Constant pattern

BERT_source_coarse = {}
BERT_source_coarse["DISABLED"] = 0x0 # Checker disabled
BERT_source_coarse["ULDG0"] = 0x1 # Uplink data group 0
BERT_source_coarse["ULDG1"] = 0x2 # Uplink data group 1
BERT_source_coarse["ULDG2"] = 0x3 # Uplink data group 2
BERT_source_coarse["ULDG3"] = 0x4 # Uplink data group 3
BERT_source_coarse["ULDG4"] = 0x5 # Uplink data group 4
BERT_source_coarse["ULDG5"] = 0x6 # Uplink data group 5
BERT_source_coarse["ULDG6"] = 0x7 # Uplink data group 6
BERT_source_coarse["ULEC"] = 0x8 # Uplink data group EC
BERT_source_coarse["DLDG0"] = 0x9 # Downlink data group 0
BERT_source_coarse["DLDG1"] = 0xa # Downlink data group 1
BERT_source_coarse["DLDG2"] = 0xb # Downlink data group 2
BERT_source_coarse["DLDG3"] = 0xc # Downlink data group 3
BERT_source_coarse["DLEC"] = 0xd # Downlink data group EC
BERT_source_coarse["DLFRAME"] = 0xe # Downlink deserializer frame

BERT_measure_time = {}
BERT_measure_time["BC_MT_2e5"] = 0x0
BERT_measure_time["BC_MT_2e7"] = 0x1
BERT_measure_time["BC_MT_2e9"] = 0x2
BERT_measure_time["BC_MT_2e11"] = 0x3
BERT_measure_time["BC_MT_2e13"] = 0x4
BERT_measure_time["BC_MT_2e15"] = 0x5
BERT_measure_time["BC_MT_2e17"] = 0x6
BERT_measure_time["BC_MT_2e19"] = 0x7
BERT_measure_time["BC_MT_2e21"] = 0x8
BERT_measure_time["BC_MT_2e23"] = 0x9
BERT_measure_time["BC_MT_2e25"] = 0xa
BERT_measure_time["BC_MT_2e27"] = 0xb
BERT_measure_time["BC_MT_2e29"] = 0xc
BERT_measure_time["BC_MT_2e31"] = 0xd
BERT_measure_time["BC_MT_2e33"] = 0xe
BERT_measure_time["BC_MT_2e35"] = 0xf

BERT_source_fine ={}
BERT_source_fine["UL_PRBS7_DR1_CHN0"] = 0x0 # Check PRBS7 sequence on channel 0 for data rate equal to 1
BERT_source_fine["UL_PRBS7_DR1_CHN1"] = 0x1 # Check PRBS7 sequence on channel 1 for data rate equal to 1
BERT_source_fine["UL_PRBS7_DR1_CHN2"] = 0x2 # Check PRBS7 sequence on channel 2 for data rate equal to 1
BERT_source_fine["UL_PRBS7_DR1_CHN3"] = 0x3 # Check PRBS7 sequence on channel 3 for data rate equal to 1
BERT_source_fine["UL_PRBS7_DR2_CHN0"] = 0x4 # Check PRBS7 sequence on channel 0 for data rate equal to 2
BERT_source_fine["UL_PRBS7_DR2_CHN2"] = 0x5 # Check PRBS7 sequence on channel 2 for data rate equal to 2
BERT_source_fine["UL_PRBS7_DR3_CHN0"] = 0x6 # Check PRBS7 sequence on channel 0 for data rate equal to 3
BERT_source_fine["UL_FIXED"] = 0x7 # Check the data against constant pattern

BERT_source_fine["DL_PRBS7_DR1_CHN0"] = 0x0 # Check PRBS7 sequence on channel 0 for data rate equal to 1
BERT_source_fine["DL_PRBS7_DR1_CHN1"] = 0x1 # Check PRBS7 sequence on channel 1 for data rate equal to 1
BERT_source_fine["DL_PRBS7_DR1_CHN2"] = 0x2 # Check PRBS7 sequence on channel 2 for data rate equal to 1
BERT_source_fine["DL_PRBS7_DR1_CHN3"] = 0x3 # Check PRBS7 sequence on channel 3 for data rate equal to 1
BERT_source_fine["DL_PRBS7_DR2_CHN0"] = 0x4 # Check PRBS7 sequence on channel 0 for data rate equal to 2
BERT_source_fine["DL_PRBS7_DR2_CHN2"] = 0x5 # Check PRBS7 sequence on channel 2 for data rate equal to 2
BERT_source_fine["DL_PRBS7_DR3_CHN0"] = 0x6 # Check PRBS7 sequence on channel 0 for data rate equal to 3
BERT_source_fine["DL_FIXED"] = 0x7 # Check the data against constant pattern

BERT_source_fine["ULEC"] = 0x0
BERT_source_fine["DLEC"] = 0x0

BERT_source_fine["DLDATA_PRBS"] = 0x0
BERT_source_fine["DLDATA_FIXED"] = 0x1 # Checks the group data in the downlink frame
BERT_source_fine["DLFRAME_PRBS7"] = 0x2 # PRBS7 (no header)
BERT_source_fine["DLFRAME_PRBS15"] = 0x3 # PRBS15 (no header)
BERT_source_fine["DLFRAME_PRBS23"] = 0x4 # PRBS23 (no header)
BERT_source_fine["DLFRAME_PRBS31"] = 0x5 # PRBS31 (no header)
BERT_source_fine["DLFRAME_FIXED"] = 0x7 # Check the data against constant pattern

def prbs_generate(system, boss, path, ohid, gbtid):

    print ("Generating PRBS signal for: " + path)

    if path == "uplink": # generate PRBS from lpGBT
        # Only generating PRBS7 for Serializer frame
        writeReg(getNode("LPGBT.RW.TESTING.ULSERTESTPATTERN"), PRBS_generator_serializer["PRBS7"], 0)
       
    elif path == "downlink" or path == "loopback": # generate PRBS from backend
        if path == "loopback": # additionally loopback prbs signal in lpGBT
            # Loopback from downlink to uplink at 10.24 Gbps
            writeReg(getNode("LPGBT.RW.TESTING.ULSERTESTPATTERN"), PRBS_generator_serializer["DLFRAME_10G24"], 0)

        mgt_channel = int(ohid) * 8 + int(gbtid)

        # PRBS7 for the entire data frame
        node = get_rwreg_node("BEFE.MGTS.MGT%d.CTRL.TX_PRBS_SEL" % (mgt_channel))
        write_backend_reg(node, 0x001)

        # Reset the TX and RX channels
        node = get_rwreg_node("BEFE.MGTS.MGT%d.RESET" % (mgt_channel))
        write_backend_reg(node, 0x001)
    
    print ("Started PRBS signal for: " + path + "\n")

def prbs_stop(system, boss, path, ohid, gbtid):

    print ("Stopping PRBS signal for: " + path)

    if path == "uplink": # stop PRBS from lpGBT
        # Stopping PRBS7 for Serializer frame
        writeReg(getNode("LPGBT.RW.TESTING.ULSERTESTPATTERN"), PRBS_generator_serializer["DATA"], 0)
        
    elif path == "downlink" or path == "loopback": # stop PRBS from backend
        if path == "loopback": # additionally stop loopback prbs signal in lpGBT
            # Stop loopback from downlink to uplink
            writeReg(getNode("LPGBT.RW.TESTING.ULSERTESTPATTERN"), PRBS_generator_serializer["DATA"], 0)
            
        mgt_channel = int(ohid) * 8 + int(gbtid)
        
        # Stopping PRBS7 for the entire data frame
        node = get_rwreg_node("BEFE.MGTS.MGT%d.CTRL.TX_PRBS_SEL" % (mgt_channel))
        write_backend_reg(node, 0x000)

        # Reset the TX and RX channels
        node = get_rwreg_node("BEFE.MGTS.MGT%d.RESET" % (mgt_channel))
        write_backend_reg(node, 0x001)

    print ("Stopped PRBS signal for: " + path + "\n")

def prbs_check(system, boss, path, ohid, gbtid, bert_source, time):

    print ("Measuring PRBS errors for: " + path)

    if path == "uplink" or path == "loopback": # checking PRBS on backend 
        mgt_channel = int(ohid) * 8 + int(gbtid)

        # Reading PRBS7
        rx_select_node = get_rwreg_node("BEFE.MGTS.MGT%d.CTRL.RX_PRBS_SEL" % (mgt_channel))
        write_backend_reg(rx_select_node, 0x001)

        # Reset the TX and RX channels
        node = get_rwreg_node("BEFE.MGTS.MGT%d.RESET" % (mgt_channel))
        write_backend_reg(node, 0x001)
           
        # Measurement Time
        bert_time_setting = BERT_measure_time[time]
        n_clocks_exp = int(time.split("_2e")[1])
        n_clocks = 2**n_clocks_exp
        print ("Measurement time in number of clock cycles: 2^" + str(n_clocks_exp) + "\n")
        measure_time = n_clocks * 25e-9 # 40 MHz clock
        
        n_transactions = n_clocks
        
        # Reset counter
        reset_node = get_rwreg_node("BEFE.MGTS.MGT%d.CTRL.RX_PRBS_CNT_RESET" % (mgt_channel))
        write_backend_reg(reset_node, 0x001)
        
        # Sleep for measurement time
        sleep(measure_time)
        
        # Read the error counter
        error_node = get_rwreg_node("BEFE.MGTS.MGT%d.STATUS.PRBS_ERROR_CNT" % (mgt_channel))
        prbs_errors = read_backend_reg(error_node)
        ber = prbs_errors
        #ber = float(prbs_errors)/float(n_transactions) # if prbs errors count error in each transaction
        
        result_string = ""
        print ("Measurement time: " + str(measure_time) + " seconds")
        if ber==0:
            result_string += Colors.GREEN 
        else:
            result_string += Colors.YELLOW 
        result_string += "Number of errors: " + str(ber) + Colors.ENDC + "\n"
        #result_string += "BER = " + str(ber) + Colors.ENDC + "\n"
        print (result_string)
        
        # Stopping reading PRBS7
        write_backend_reg(rx_select_node, 0x000)

        # Reset the TX and RX channels
        write_backend_reg(node, 0x001)

        # Reset counter
        write_backend_reg(reset_node, 0x001)
          
    elif path == "downlink": # checking PRBS on lpGBT
        
        # Getting the register nodes
        bert_coarse_node = getNode("LPGBT.RW.BERT.COARSEBERTSOURCE")
        bert_fine_node = getNode("LPGBT.RW.BERT.FINEBERTSOURCE")
        bert_time_node = getNode("LPGBT.RW.BERT.BERTMEASTIME")
        bert_skipdisable_node = getNode("LPGBT.RW.BERT.SKIPDISABLE")
        bert_start_node = getNode("LPGBT.RW.BERT.BERTSTART")
        bert_done_node = getNode("LPGBT.RO.BERT.BERTDONE")
        bert_error_node = getNode("LPGBT.RO.BERT.BERTPRBSERRORFLAG")
        bert_result0_node = getNode("LPGBT.RO.BERT.BERTERRORCOUNT0")
        bert_result1_node = getNode("LPGBT.RO.BERT.BERTERRORCOUNT1")
        bert_result2_node = getNode("LPGBT.RO.BERT.BERTERRORCOUNT2")
        bert_result3_node = getNode("LPGBT.RO.BERT.BERTERRORCOUNT3")
        bert_result4_node = getNode("LPGBT.RO.BERT.BERTERRORCOUNT4")

        # Setting Measurement Time
        bert_time_setting = BERT_measure_time[time]
        n_clocks_exp = int(time.split("_2e")[1])
        n_clocks = 2**n_clocks_exp
        print ("Measurement time: " + time + " , setting: " + str(hex(bert_time_setting)) + " , number of clock cycles: 2^" + str(n_clocks_exp) + "\n")
        writeReg(bert_time_node, bert_time_setting, 0)

        # Looping over the coarse BERT sources
        for bert in bert_source:
            if bert == "DISABLED":
                print ("Skipping DISABLED Coarse BERT Source")
                continue

            bert_coarse_setting = BERT_source_coarse[bert]
            print ("BERT for Coarse BERT Source: " + bert + " , setting: " + str(hex(bert_coarse_setting)) + "\n")
            writeReg(bert_coarse_node, bert_coarse_setting, 0)

            bert_fine_list = []
            bert_skipdisable_setting = 0x0
            bits_per_clock_cycle = 0
            if "ULDG" in bert:
                bert_fine_list.append("UL_PRBS7_DR1_CHN0")
                bert_fine_list.append("UL_PRBS7_DR1_CHN1")
                bert_fine_list.append("UL_PRBS7_DR1_CHN2")
                bert_fine_list.append("UL_PRBS7_DR1_CHN3")
                bits_per_clock_cycle = 8 # Uplink contains 8 bits per clock cycle (320 Mbps)
            elif "DLDG" in bert:
                bert_fine_list.append("DL_PRBS7_DR3_CHN0")
                bits_per_clock_cycle = 8 # Downlink contains 8 bits per clock cycle (320 Mbps)
            elif "DLFRAME" in bert:
                bert_fine_list.append("DLFRAME_PRBS7")
                bert_skipdisable_setting = 0x1
                bits_per_clock_cycle = 64 # Downlink frame contains 64 bits per clock cycle (2.56 Gbps)
            elif "EC" in bert:
                bert_fine_list.append(bert)
                bits_per_clock_cycle = 2 # EC contains 2 bits per clock cycle (80 Mbps)
            else:
                continue

            bits_checked = n_clocks * bits_per_clock_cycle
            writeReg(bert_skipdisable_node, bert_skipdisable_setting, 0)
            #writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGDISABLEFRAMEALIGNERLOCKCONTROL") , 0x1, 0)
            #writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGLOCKFILTERENABLE"), 0x0, 0) # quickstart recommends 0
            #writeReg(getNode("LPGBT.RWF.CALIBRATION.CLKGWAITCDRTIME"), 0xa, 0)

            # Looping over the fine BERT sources
            for bert_fine in bert_fine_list:
                bert_fine_setting = BERT_source_fine[bert_fine]
                print ("BERT for Fine BERT Source: " + bert_fine + " , setting: " + str(hex(bert_fine_setting)))
                writeReg(bert_fine_node, bert_fine_setting, 0)

                # Start the measurement
                print ("Starting BERT")
                writeReg(bert_start_node, 0x1, 0)

                done = 0
                while (done==0):
                    if system!="dryrun":
                        done = readReg(bert_done_node)
                    else:
                        done = 1
                err = readReg(bert_error_node)
                if (err):
                    print (Colors.RED + "ERROR: no data received" + Colors.ENDC)
                    break

                # Read the BER result
                bert_result = 0
                bert_result |= readReg(bert_result0_node) << 0
                bert_result |= readReg(bert_result1_node) << 8
                bert_result |= readReg(bert_result2_node) << 16
                bert_result |= readReg(bert_result3_node) << 24
                bert_result |= readReg(bert_result4_node) << 32

                # Stop the measurement by deaserting the start bit
                print ("Stopping BERT")
                writeReg(bert_start_node, 0x0, 0)

                # Calculate Bit Error Rate
                ber = float(bert_result) / float(bits_checked)
                print ("Number of clock cycles for measurement: " + str(n_clocks))
                print ("Result for coarse BERT source: " + bert + " and fine BERT source: " + bert_fine)
                result_string = ""
                if ber==0:
                    result_string += Colors.GREEN 
                else:
                    result_string += Colors.YELLOW 
                result_string += "Total number of bits checked = " + str(bits_checked) + ", Total number of bit errors: " + str(bert_result) + "\n"
                result_string += "BER = " + str(ber) + Colors.ENDC + "\n"
                print (result_string)

            writeReg(bert_fine_node, 0x0, 0)
            writeReg(bert_coarse_node, 0x0, 0)

    print ("Finished measuring PRBS errors for: " + path + "\n")

if __name__ == "__main__":
    # Parsing arguments
    parser = argparse.ArgumentParser(description="LPGBT Bit Error Rate Test (BERT)")
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle or dryrun")
    parser.add_argument("-y", "--oh_v", action="store", dest="oh_v", default="1", help="oh_v = 1 or 2")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss/sub")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-1 (only needed for backend)")
    parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0-7 (only needed for backend)")
    parser.add_argument("-p", "--path", action="store", dest="path", help="path = uplink, downlink, loopback")
    parser.add_argument("-f", "--func", action="store", dest="func", help="func = generate, check, all, stop")
    parser.add_argument("-b", "--bert_source", action="store", nargs="+", dest="bert_source", help="COURSE BERT SOURCE = See lpGBT manual Table 14.4 for options, default = DLFRAME")
    parser.add_argument("-t", "--time", action="store", dest="time", help="TIME = measurement time (See lpGBT manual Table 14.5 for options), default: BC_MT_2e35")
    args = parser.parse_args()

    if args.system == "chc":
        print ("Using Rpi CHeeseCake for BERT")
    elif args.system == "backend":
        print ("Using Backend for BERT")
        #print (Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun supported at the moment" + Colors.ENDC)
        #sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for checking configuration")
        print (Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun supported at the moment" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually running on lpGBT")
    else:
        print (Colors.YELLOW + "Only valid options: chc, backend, dongle, dryrun" + Colors.ENDC)
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

    boss = None
    if args.lpgbt is None:
        print (Colors.YELLOW + "Please select boss/sub" + Colors.ENDC)
        sys.exit()
    elif (args.lpgbt=="boss"):
        print ("BERT for boss LPGBT")
        boss=1
    elif (args.lpgbt=="sub"):
        print ("BERT for sub LPGBT")
        boss=0
    else:
        print (Colors.YELLOW + "Please select boss/sub" + Colors.ENDC)
        sys.exit()
    if boss is None:
        sys.exit()
      
    if args.system == "backend":
        if args.ohid is None:
            print (Colors.YELLOW + "Need OHID for backend" + Colors.ENDC)
            sys.exit()
        if args.gbtid is None:
            print (Colors.YELLOW + "Need GBTID for backend" + Colors.ENDC)
            sys.exit()
        if int(args.ohid) > 1:
            print(Colors.YELLOW + "Only OHID 0-1 allowed" + Colors.ENDC)
            sys.exit()
        if int(args.gbtid) > 7:
            print(Colors.YELLOW + "Only GBTID 0-7 allowed" + Colors.ENDC)
            sys.exit()
    else:
        if args.ohid is not None or args.gbtid is not None:
            print (Colors.YELLOW + "OHID and GBTID only needed for backend" + Colors.ENDC)
            sys.exit()

    if args.path not in ["uplink", "downlink", "loopback"]:
        print (Colors.YELLOW + "Enter valid path" + Colors.ENDC)
        sys.exit()
    if args.func not in ["generate", "check", "all", "stop"]:
        print (Colors.YELLOW + "Enter valid operation" + Colors.ENDC)
        sys.exit()

    if args.path == "uplink":
        if args.system == "chc" and args.func not in ["generate", "stop"]:
            print (Colors.YELLOW + "For uplink, only PRBS generation or stopping supported for CHeeseCake" + Colors.ENDC)
            sys.exit()
    elif args.path == "downlink":
        if args.func == "all":
            print (Colors.YELLOW + "For downlink, all operations not yet supported from one system" + Colors.ENDC)
            sys.exit()
        if args.system == "chc" and args.func != "check":
            print (Colors.YELLOW + "For downlink, only PRBS pattern checking supported for CHeeseCake" + Colors.ENDC)
            sys.exit()
        if args.system == "backend" and args.func not in ["generate", "stop"]:
            print (Colors.YELLOW + "For downlink, only PRBS generation or stopping supported for Backend" + Colors.ENDC)
            sys.exit()
    elif args.path == "loopback":
        if args.system == "chc":
            print (Colors.YELLOW + "For loopback, CHeeseCake is not supported" + Colors.ENDC)
            sys.exit()

    if not boss:
        if args.path != "uplink":
            print (Colors.YELLOW + "Only uplink can be checked for sub lpGBT" + Colors.ENDC)
            sys.exit()

    if args.path in ["uplink", "loopback"]:
        if args.bert_source is not None:
            print (Colors.YELLOW + "BERT source only required for downlink pattern checking on lpGBT" + Colors.ENDC)
            sys.exit()
    else:
        if args.func in ["check", "all"]:
            if args.bert_source is None:
                args.bert_source = ["DLFRAME"]
            for bert in args.bert_source:
                if bert not in BERT_source_coarse:
                    print (Colors.YELLOW + "Invalid course BERT source : " + bert + " (See lpGBT manual Table 14.4 for options)" + Colors.ENDC)
                    sys.exit()
                if bert != "DLFRAME":
                    print (Colors.YELLOW + "Only DLFRAME supported yet for downlink PRBS pattern checking" + Colors.ENDC)
                    sys.exit()
        else:
            if args.bert_source is not None:
                print (Colors.YELLOW + "BERT source only required for downlink pattern checking on lpGBT" + Colors.ENDC)
                sys.exit()

    if args.func in ["check", "all"]:
        if args.time is None:
            args.time = "BC_MT_2e35"
        if args.time not in BERT_measure_time:
            print (Colors.YELLOW + "Invalid BERT measurement time (See lpGBT manual Table 14.5 for options)" + Colors.ENDC)
            sys.exit()
    else:
        if args.time is not None:
            print (Colors.YELLOW + "BERT measurement time only required for pattern checking" + Colors.ENDC)
            sys.exit()

    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML(oh_v)
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system, boss, args.ohid, args.gbtid)
    print("Initialization Done\n")
    
    # Readback rom register to make sure communication is OK
    if args.system!="dryrun" and args.system!="backend":
        check_rom_readback()

    # Check if lpGBT is READY if running through backend
    #if args.system=="backend":
    #    check_lpgbt_link_ready(args.ohid, args.gbtid)

    try:
        if args.func == "generate" or args.func == "all":
            prbs_generate(args.system, boss, args.path, args.ohid, args.gbtid)
        if args.func == "check" or args.func == "all":
            prbs_check(args.system, boss, args.path, args.ohid, args.gbtid, args.bert_source, args.time)
        if args.func == "stop" or args.func == "all":
            prbs_stop(args.system, boss, args.path, args.ohid, args.gbtid)
    except KeyboardInterrupt:
        print (Colors.RED + "\nKeyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()
