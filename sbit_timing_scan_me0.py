from rw_reg import *
from time import *
import array
import struct
import sys

#VFAT DEFAULTS

ADDR_JTAG_LENGTH = None
ADDR_JTAG_TMS = None
ADDR_JTAG_TDO = None
ADDR_JTAG_TDI = None

SCAN_RANGE = 17

class Colors:
    WHITE   = '\033[97m'
    CYAN    = '\033[96m'
    MAGENTA = '\033[95m'
    BLUE    = '\033[94m'
    YELLOW  = '\033[93m'
    GREEN   = '\033[92m'
    RED     = '\033[91m'
    ENDC    = '\033[0m'


def configureVfatForPulsing(vfatN, ohN):

        writeReg(getNode("GEM_AMC.GEM_SYSTEM.CTRL.LINK_RESET"), 1)

        sleep (0.1)

        writeReg(getNode("GEM_AMC.GEM_SYSTEM.VFAT3.SC_ONLY_MODE"), 1)
        #print "\tLink good: "
        #print "\t\t" + readReg(getNode("GEM_AMC.OH_LINKS.OH%i.VFAT%i.LINK_GOOD"%(ohN,vfatN)))
        #print "\tSync Error: "
        #print "\t\t" + readReg(getNode("GEM_AMC.OH_LINKS.OH%i.VFAT%i.SYNC_ERR_CNT"%(ohN,vfatN)))

        if (parseInt(readReg(getNode("GEM_AMC.OH_LINKS.OH%i.VFAT%i.SYNC_ERR_CNT"%(ohN,vfatN)))) > 0):
            print ("\tLink errors.. exiting")
            sys.exit()


           #Configure TTC generator on CTP7
        writeReg(getNode("GEM_AMC.TTC.GENERATOR.RESET"),  1)
        writeReg(getNode("GEM_AMC.TTC.GENERATOR.ENABLE"), 1)
        writeReg(getNode("GEM_AMC.TTC.GENERATOR.CYCLIC_CALPULSE_TO_L1A_GAP"), 50)
        writeReg(getNode("GEM_AMC.TTC.GENERATOR.CYCLIC_L1A_GAP"),  500)
        writeReg(getNode("GEM_AMC.TTC.GENERATOR.CYCLIC_L1A_COUNT"),  0)

        writeReg(getNode("GEM_AMC.TRIGGER.SBIT_MONITOR.OH_SELECT"), ohN)

        writeReg(getNode("GEM_AMC.OH.OH%i.FPGA.TRIG.CTRL.VFAT_MASK" % ohN), 0xffffff ^ (1 << (vfatN)))

        writeReg(getNode("GEM_AMC.TTC.GENERATOR.CYCLIC_START"), 1)

        for i in range(128):
            writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.VFAT_CHANNELS.CHANNEL%i"%(ohN,vfatN,i)), 0x4000)  # mask all channels and disable the calpulse

        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_PULSE_STRETCH"       % (ohN , vfatN)) , 7)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_SYNC_LEVEL_MODE"     % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_SELF_TRIGGER_MODE"   % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_DDR_TRIGGER_MODE"    % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_SPZS_SUMMARY_ONLY"   % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_SPZS_MAX_PARTITIONS" % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_SPZS_ENABLE"         % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_SZP_ENABLE"          % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_SZD_ENABLE"          % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_TIME_TAG"            % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_EC_BYTES"            % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_BC_BYTES"            % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_FP_FE"               % (ohN , vfatN)) , 7)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_RES_PRE"             % (ohN , vfatN)) , 1)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAP_PRE"             % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_PT"                  % (ohN , vfatN)) , 15)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_EN_HYST"             % (ohN , vfatN)) , 1)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_SEL_POL"             % (ohN , vfatN)) , 1)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_FORCE_EN_ZCC"        % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_FORCE_TH"            % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_SEL_COMP_MODE"       % (ohN , vfatN)) , 1)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_VREF_ADC"            % (ohN , vfatN)) , 3)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_MON_GAIN"            % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_MONITOR_SELECT"      % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_IREF"                % (ohN , vfatN)) , 32)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_THR_ZCC_DAC"         % (ohN , vfatN)) , 10)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_THR_ARM_DAC"         % (ohN , vfatN)) , 100)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_HYST"                % (ohN , vfatN)) , 5)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_LATENCY"             % (ohN , vfatN)) , 45)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_SEL_POL"         % (ohN , vfatN)) , 1)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_PHI"             % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_EXT"             % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_DAC"             % (ohN , vfatN)) , 50)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_MODE"            % (ohN , vfatN)) , 1)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_FS"              % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_CAL_DUR"             % (ohN , vfatN)) , 200)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_BIAS_CFD_DAC_2"      % (ohN , vfatN)) , 40)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_BIAS_CFD_DAC_1"      % (ohN , vfatN)) , 40)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_BIAS_PRE_I_BSF"      % (ohN , vfatN)) , 13)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_BIAS_PRE_I_BIT"      % (ohN , vfatN)) , 150)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_BIAS_PRE_I_BLCC"     % (ohN , vfatN)) , 25)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_BIAS_PRE_VREF"       % (ohN , vfatN)) , 86)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_BIAS_SH_I_BFCAS"     % (ohN , vfatN)) , 250)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_BIAS_SH_I_BDIFF"     % (ohN , vfatN)) , 150)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_BIAS_SH_I_BFAMP"     % (ohN , vfatN)) , 0)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_BIAS_SD_I_BDIFF"     % (ohN , vfatN)) , 255)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_BIAS_SD_I_BSF"       % (ohN , vfatN)) , 15)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_BIAS_SD_I_BFCAS"     % (ohN , vfatN)) , 255)
        writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.CFG_RUN"%(ohN,vfatN)), 1)
        writeReg(getNode("GEM_AMC.GEM_SYSTEM.VFAT3.SC_ONLY_MODE"), 0)

def main():

    ohN = 0
    vfatN = 0

    if len(sys.argv) < 3:
        print('Usage: sbit_timing_scan.py <oh_num> <vfat_mask>')
        return

    ohN      = int(sys.argv[1])
    vfat_mask    = int(sys.argv[2],0)

    # construct a list of vfats to be scanned based on the mask
    vfat_list = []
    for vfat in range(0,12):
        if (0x1 & (vfat_mask>>vfat)):
            vfat_list.append(vfat)

    parseXML()
    initJtagRegAddrs()

    #writeReg(getNode("GEM_AMC.TRIGGER.SBIT_MONITOR.OH_SELECT"), ohN)

    #tap_dly_initial = [0,0,0,0,0,0,0,0]

    for ivfat in vfat_list:

        print ("")
        print ("####################################################################################################")
        print ("Scanning VFAT %i" % ivfat)
        print ("####################################################################################################")
        print ("")

        writeReg(getNode('GEM_AMC.SLOW_CONTROL.SCA.CTRL.MODULE_RESET'), 0x1)
        writeReg(getNode('GEM_AMC.SLOW_CONTROL.SCA.MANUAL_CONTROL.LINK_ENABLE_MASK'), 0x1<<ohN)
        writeReg(getNode('GEM_AMC.TTC.GENERATOR.ENABLE'), 0x1)
        writeReg(getNode('GEM_AMC.SLOW_CONTROL.SCA.CTRL.TTC_HARD_RESET_EN'), 0x0)
        writeReg(getNode('GEM_AMC.SLOW_CONTROL.SCA.ADC_MONITORING.MONITORING_OFF'), 0xffffffff)

        ohList=[ohN]

        ##################
        #
        ##################

        configureVfatForPulsing(ivfat, ohN)

        err_matrix = [[0 for i in range(0,2*SCAN_RANGE+1)] for j in range(8)]

        writeReg(getNode("GEM_AMC.OH.OH%i.FPGA.TRIG.CTRL.ALIGNED_COUNT_TO_READY" % ohN), 0xfff)

        sot_dly_reg     = getNode('GEM_AMC.OH.OH%d.FPGA.TRIG.TIMING.SOT_TAP_DELAY_VFAT%s' % (ohN, ivfat))
        sot_dly_initial = parseInt(readReg(sot_dly_reg))

        sc_only_reg = getNode("GEM_AMC.GEM_SYSTEM.VFAT3.SC_ONLY_MODE")

	writeReg(sot_dly_reg, dly_offset)
	sot_rdy = parseInt(readReg(getNode("GEM_AMC.OH.OH%i.FPGA.TRIG.CTRL.SBIT_SOT_READY" % ohN)))
	sleep (0.1)
	if (not (sot_rdy >> ivfat)&0x1):
	    print ("Sot not ready... cannot scan")
	    sys.exit()

	for ipair in range(8): # loop over 8 diff pairs in the vfat

	    # write the mask
	    #writeReg(getNode("GEM_AMC.OH.OH%i.FPGA.TRIG.CTRL.TU_MASK.VFAT%i_TU_MASK" % (ohN, ivfat)), 0xff ^ (1 << (ipair)))
	    writeReg(getNode("GEM_AMC." % (ohN, ivfat)), 0xff ^ (1 << (ipair)))

	    for ipad in range (8): # loop over triger pads per pair (16 channels)

		trigger_channel = ipair*8 + ipad

		writeReg(sc_only_reg, 1)
		strip = trigger_channel*2+0
		writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.VFAT_CHANNELS.CHANNEL%i"%(ohN,ivfat,strip)), 0x8000) # enable calpulse and unmask
		writeReg(sc_only_reg, 0)

		sleep(0.0001)
		wReg(sbit_monitor_reset_reg, 1)
		sleep(0.0001)

		rate_on = parseInt(readReg(##########################)) # vfat counter register

		writeReg(sc_only_reg, 1)
		writeReg(getNode("GEM_AMC.OH.OH%i.GEB.VFAT%i.VFAT_CHANNELS.CHANNEL%i"%(ohN,ivfat,strip)), 0x4000) # disable calpulse and mask
		writeReg(sc_only_reg, 0)

		rate_off = parseInt(readReg(##########################)) # vfat counter register
		err_dead_sbit = rate < 0x2638e98 * 0.9
		err_stuck_sbit = rate > 0

		print ("vfat=%d, pair=%d, channel=%i, rate_on=0x%X, rate_off=0x%X" % (ivfat,ipair, trigger_channel,  rate_on, rate_off)

	writeReg(sot_dly_reg, sot_dly_initial);

        ngood_center = [0 for i in range (8)]
        ngood_width  = [0 for i in range (8)]
        best_tap_delay  = [0 for i in range (8)]

        min_center = 1000

        line =  "      "
        for dly in range (2*SCAN_RANGE+1):
            text = "%2X" % (abs(dly-SCAN_RANGE) % 16)
            line = line + text

        print (line)

        for ibit in range(8):

            ngood        = 0
            ngood_max    = 0
            ngood_edge   = 0

            for dly in range (2*SCAN_RANGE+1):
                if (err_matrix[ibit][dly]==0):
                    ngood+=1
                    if (dly==2*SCAN_RANGE):
                        if (ngood > 0 and ngood >= ngood_max):
                            ngood_max  = ngood
                            ngood_edge = dly
                            ngood=0
                else:
                    if (ngood > 0 and ngood >= ngood_max):
                        ngood_max  = ngood
                        ngood_edge = dly
                        ngood=0
                    #print("%3i" % err_matrix[ibit][dly]),

            if (ngood_max>0):
                ngood_width[ibit] = ngood_max

                # even windows
                if (ngood_max % 2 == 0):
                    ngood_center[ibit]=ngood_edge-(ngood_max/2)-1;
                if (err_matrix[ibit][ngood_edge] > err_matrix[ibit][ngood_edge-ngood_max-1]):
                    ngood_center[ibit]=ngood_center[ibit]
                else:
                    ngood_center[ibit]=ngood_center[ibit]+1

                # oddwindows
                if (ngood_max % 2 == 1):
                    ngood_center[ibit]=ngood_edge-(ngood_max/2)-1;

                # minimum
                if (ngood_center[ibit] < min_center):
                    min_center = ngood_center[ibit]

        ################################################################################
        # Printout Timing Window
        ################################################################################

        for ibit in range(8):

            line = ("Sbit%i: " % ibit)

            initial = SCAN_RANGE - sot_dly_initial + tap_dly_initial[ibit]

            for dly in range (2*SCAN_RANGE+1):
                if (err_matrix[ibit][dly]==0):
                    #if (dly == ngood_center[ibit] and initial == ngood_center[ibit]):
                    #    line = line + Colors.GREEN + "= "
                    if (dly == ngood_center[ibit]):
                        line = line + Colors.GREEN + "| "
                    elif (dly == initial and initial < ngood_center[ibit]):
                        line = line + Colors.GREEN + "> "
                    elif (dly == initial and initial > ngood_center[ibit]):
                        line = line + Colors.GREEN + "< "
                    else:
                        line = line + Colors.GREEN + "- "
                else:
                    line = line + Colors.RED + "x "

            line = line + Colors.ENDC
            print line

        ################################################################################
        # Printout Summary
        ################################################################################

        print ("min center = %i" % min_center)

        best_sot_tap_delay = 99
        if (min_center - SCAN_RANGE < 0):
            best_sot_tap_delay = SCAN_RANGE-min_center
        else:
            best_sot_tap_delay = min_center-SCAN_RANGE

        print ("sot :           best_dly=% 2d" % ( best_sot_tap_delay))
        for ibit in range(8):
            best_tap_delay [ibit] = ngood_center[ibit] - min_center
            print ("bit%i: center=% 2d best_dly=% 2d width=% 2d (%f ns)" % (ibit, ngood_center[ibit]-SCAN_RANGE, best_tap_delay[ibit], ngood_width[ibit], ngood_width[ibit]*78./1000))


    print("")
    print("bye now..")

def sendScaCommand(ohList, sca_channel, sca_command, data_length, data, doRead):
    #print('fake send: channel ' + hex(sca_channel) + ', command ' + hex(sca_command) + ', length ' + hex(data_length) + ', data ' + hex(data) + ', doRead ' + str(doRead))
    #return

    d = data

    writeReg(getNode('GEM_AMC.SLOW_CONTROL.SCA.MANUAL_CONTROL.SCA_CMD.SCA_CMD_CHANNEL'), sca_channel)
    writeReg(getNode('GEM_AMC.SLOW_CONTROL.SCA.MANUAL_CONTROL.SCA_CMD.SCA_CMD_COMMAND'), sca_command)
    writeReg(getNode('GEM_AMC.SLOW_CONTROL.SCA.MANUAL_CONTROL.SCA_CMD.SCA_CMD_LENGTH'), data_length)
    writeReg(getNode('GEM_AMC.SLOW_CONTROL.SCA.MANUAL_CONTROL.SCA_CMD.SCA_CMD_DATA'), d)
    writeReg(getNode('GEM_AMC.SLOW_CONTROL.SCA.MANUAL_CONTROL.SCA_CMD.SCA_CMD_EXECUTE'), 0x1)
    reply = []
    if doRead:
        for i in ohList:
            reply.append(parseInt(readReg(getNode('GEM_AMC.SLOW_CONTROL.SCA.MANUAL_CONTROL.SCA_REPLY_OH%d.SCA_RPY_DATA' % i))))
    return reply

def initJtagRegAddrs():
    global ADDR_JTAG_LENGTH
    global ADDR_JTAG_TMS
    global ADDR_JTAG_TDO
    global ADDR_JTAG_TDI
    ADDR_JTAG_LENGTH = getNode('GEM_AMC.SLOW_CONTROL.SCA.JTAG.NUM_BITS').real_address
    ADDR_JTAG_TMS = getNode('GEM_AMC.SLOW_CONTROL.SCA.JTAG.TMS').real_address
    ADDR_JTAG_TDO = getNode('GEM_AMC.SLOW_CONTROL.SCA.JTAG.TDO').real_address
    #ADDR_JTAG_TDI = getNode('GEM_AMC.SLOW_CONTROL.SCA.JTAG.TDI').real_address

def check_bit(byteval,idx):
    return ((byteval&(1<<idx))!=0);

def debug(string):
    if DEBUG:
        print('DEBUG: ' + string)

def debugCyan(string):
    if DEBUG:
        printCyan('DEBUG: ' + string)

def heading(string):
    print (Colors.BLUE)
    print ('\n>>>>>>> '+str(string).upper()+' <<<<<<<')
    print (Colors.ENDC)

def subheading(string):
    print (Colors.YELLOW)
    print ('---- '+str(string)+' ----',Colors.ENDC)

def printCyan(string):
    print (Colors.CYAN)
    print (string, Colors.ENDC)

def printRed(string):
    print (Colors.RED)
    print (string, Colors.ENDC)

def hex(number):
    if number is None:
        return 'None'
    else:
        return "{0:#0x}".format(number)

def binary(number, length):
    if number is None:
        return 'None'
    else:
        return "{0:#0{1}b}".format(number, length + 2)

if __name__ == '__main__':
    main()

