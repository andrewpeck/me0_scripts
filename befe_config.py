#!/usr/bin/env python3

import os
BEFE_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# =================================================================================================
#            Backend configuration
# =================================================================================================

CONFIG_RWREG_CVP13 = [
    {
        # setting this to auto will scan /sys/bus/pci/devices and try to find the CVP13, you can also just set it to the exact device BAR2 resource e.g. /sys/bus/pci/devices/0000:05:00.0/resource2 (see lspci to find the correct bus)
        # note that auto setting can only be used if you only have one card in the system
        'DEVICE': 'auto',
        #    'DEVICE'                        : '/sys/bus/pci/devices/0000:05:00.0/resource2', # for CVP13 set this to the BAR2 resource of appropriate bus e.g. /sys/bus/pci/devices/0000:05:00.0/resource2 (see lspci to find the correct bus). For other boards this parameter is not yet used
        'BASE_ADDR': 0
    }
]

CONFIG_RWREG_CTP7 = [
    {
        'DEVICE': '',
        'BASE_ADDR': 0x64000000
    }
]

CONFIG_RWREG_APEX0 = [
    {
        'DEVICE': 'FPGA0',  # for APEX set this to either FPGA0 or FPGA1
        'BASE_ADDR': 0
    }
]

CONFIG_RWREG_APEX = [
    {
        'DEVICE': 'FPGA0',  # for APEX set this to either FPGA0 or FPGA1
        'BASE_ADDR': 0
    },
    {
        'DEVICE': 'FPGA1',  # for APEX set this to either FPGA0 or FPGA1
        'BASE_ADDR': 0
    }
]

CONFIG_RWREG = {"cvp13": CONFIG_RWREG_CVP13, "ctp7": CONFIG_RWREG_CTP7, "apex": CONFIG_RWREG_APEX}

CONFIG_USE_TCDS = False

# CVP13 specific
CONFIG_CVP13_GE11_BITFILE = BEFE_SCRIPTS_DIR + "/resources/cvp13_ge11.bit"
CONFIG_CVP13_GE21_BITFILE = BEFE_SCRIPTS_DIR + "/resources/cvp13_ge21.bit"
CONFIG_CVP13_ME0_BITFILE = BEFE_SCRIPTS_DIR + "/resources/cvp13_me0.bit"
CONFIG_CVP13_CSC_BITFILE = BEFE_SCRIPTS_DIR + "/resources/cvp13_csc.bit"

CONFIG_CVP13_PCIE_CONFIG = BEFE_SCRIPTS_DIR + "/resources/cvp13_pcie_config"

# vivado or vivado lab tools can be used to program CVP13
CONFIG_VIVADO_DIR = "/opt/Xilinx/Vivado/2021.1" #this can also be a path to vivado lab tools e.g. "/opt/Xilinx/Vivado_Lab/2020.2"
CONFIG_VIVADO_HW_SERVER = "localhost:3121"

# X2O specific
CONFIG_X2O_SW_DIR = "/root/X2O-Zynq-software"

# APEX specific
CONFIG_APEX_GE11_BITFILE = BEFE_SCRIPTS_DIR + "/resources/apex_ge11.bit"
CONFIG_APEX_GE21_BITFILE = BEFE_SCRIPTS_DIR + "/resources/apex_ge21.bit"
CONFIG_APEX_ME0_BITFILE = BEFE_SCRIPTS_DIR + "/resources/apex_me0.bit"
CONFIG_APEX_CSC_BITFILE = BEFE_SCRIPTS_DIR + "/resources/apex_csc.bit"

# =================================================================================================
#            GE1/1 configuration
# =================================================================================================

# OH firmware bitfile (same file is loaded to all OHs)
CONFIG_GE11_OH_BITFILE = BEFE_SCRIPTS_DIR + "/resources/ge11_oh.bit"
# GBT0 and GBT1 config files: these are arrays that should have a length of at least how many OHs are connected
# NOTE: the example below is using the same config for all OHs
# To specify config files individually for each OH just make each element of the two arrays refer to the configs of the particular OH (and remove the * 16 at the end)
# Only modify CONFIG_GE11_OH_GBT0_CONFIGS, CONFIG_GE11_OH_GBT1_CONFIGS, and CONFIG_GE11_OH_GBT2_CONFIGS if needed, do not modify CONFIG_GE11_OH_GBT_CONFIGS
CONFIG_GE11_OH_GBT0_CONFIGS = [BEFE_SCRIPTS_DIR + "/resources/ge11_gbt0_config.txt"] * 16
CONFIG_GE11_OH_GBT1_CONFIGS = [BEFE_SCRIPTS_DIR + "/resources/ge11_gbt1_config.txt"] * 16
CONFIG_GE11_OH_GBT2_CONFIGS = [BEFE_SCRIPTS_DIR + "/resources/ge11_gbt2_config.txt"] * 16
CONFIG_GE11_OH_GBT_CONFIGS = [CONFIG_GE11_OH_GBT0_CONFIGS, CONFIG_GE11_OH_GBT1_CONFIGS, CONFIG_GE11_OH_GBT2_CONFIGS] # do not modify this line
# VFAT HDLC addresses
CONFIG_GE11_VFAT_HDLC_ADDRESSES = [0] * 24

# =================================================================================================
#            GE2/1 configuration
# =================================================================================================

# OH firmware bitfile (same file is loaded to all OHs)
CONFIG_GE21_OH_BITFILE = BEFE_SCRIPTS_DIR + "/resources/ge21_oh.bit"
# GBT0 and GBT1 config files: these are arrays that should have a length of at least how many OHs are connected
# NOTE: the example below is using the same config for all OHs, while in a real system you will likely need different files for each OH (e.g. containing correct phases for the GEB that they're installed on)
# To specify config files individually for each OH just make each element of the two arrays refer to the configs of the particular OH (and remove the * 16 at the end)
# Only modify CONFIG_GE21_OH_GBT0_CONFIGS and CONFIG_GE21_OH_GBT1_CONFIGS if needed, do not modify CONFIG_GE21_OH_GBT_CONFIGS
CONFIG_GE21_OH_GBT0_CONFIGS = [BEFE_SCRIPTS_DIR + "/resources/ge21_gbt0_config.txt"] * 16
CONFIG_GE21_OH_GBT1_CONFIGS = [BEFE_SCRIPTS_DIR + "/resources/ge21_gbt1_config.txt"] * 16
CONFIG_GE21_OH_GBT_CONFIGS = [CONFIG_GE21_OH_GBT0_CONFIGS, CONFIG_GE21_OH_GBT1_CONFIGS] # do not modify this line
# VFAT HDLC addresses
CONFIG_GE21_VFAT_HDLC_ADDRESSES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11] # replace with zeros if your setup has older GEBs and/or VFAT hybrids that don't support addressing

# =================================================================================================
#            ME0 configuration
# =================================================================================================

# GBT0 and GBT1 config files: these are arrays that should have a length of at least how many OHs are connected
# NOTE: the example below is using the same config for all OHs, while in a real system you will likely need different files for each OH (e.g. containing correct phases for the GEB that they're installed on)
# To specify config files individually for each OH just make each element of the two arrays refer to the configs of the particular OH (and remove the * 16 at the end)
# Only modify CONFIG_ME0_OH_GBT0_CONFIGS and CONFIG_ME0_OH_GBT1_CONFIGS if needed, do not modify CONFIG_ME0_OH_GBT_CONFIGS
CONFIG_ME0_OH_GBT0_CONFIGS = [BEFE_SCRIPTS_DIR + "/resources/me0_boss_config_ohv*.txt"] * 16
CONFIG_ME0_OH_GBT1_CONFIGS = [BEFE_SCRIPTS_DIR + "/resources/me0_sub_config_ohv*.txt"] * 16
CONFIG_ME0_OH_GBT_CONFIGS = [CONFIG_ME0_OH_GBT0_CONFIGS, CONFIG_ME0_OH_GBT1_CONFIGS] # do not modify this line
# VFAT HDLC addresses
CONFIG_ME0_VFAT_HDLC_ADDRESSES = [4, 3, 10, 9, 1, 3, 7, 9, 1, 5, 7, 11, 4, 5, 10, 11, 2, 6, 8, 12, 2, 6, 8, 12] # replace with zeros if your setup has VFAT hybrids that don't support addressing
# GBT version - 0 for ME0 OH-v1 and 1 for ME0 OH-v2 (0 for GE1/1 and GE2/1)
CONFIG_ME0_GBT_VER = {
    0: [0, 0, 0, 0, 0, 0, 0, 0], # lpGBT ver for 8 GBTs for OH0
    1: [0, 0, 0, 0, 0, 0, 0, 0], # lpGBT ver for 8 GBTs for OH1
    2: [0, 0, 0, 0, 0, 0, 0, 0], # lpGBT ver for 8 GBTs for OH2
    3: [0, 0, 0, 0, 0, 0, 0, 0]  # lpGBT ver for 8 GBTs for OH3
}
