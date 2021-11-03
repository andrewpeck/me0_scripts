from rw_reg_lpgbt import *
from time import sleep, time
import sys
import argparse

FUSE_TIMEOUT_MS = 10 # in ms
TOTAL_EFUSE_ON_TIME_MS = 0 # in ms
fuse_list = {}
n_rw_fuse = -9999
efuse_done_reg = -9999

def main(system, oh_v, boss, fusing, input_config_file, input_vtrx, input_register, input_data, user_id, complete):

    global fuse_list
    global n_rw_fuse
    global efuse_done_reg

    if oh_v == 1:
        for i in range(240):
            fuse_list[i] = 0x00
        n_rw_fuse = (0xEF+1) # number of registers in LPGBT rwf block
        efuse_done_reg = 0xEF
    elif oh_v == 2:
        for i in range(256):
            fuse_list[i] = 0x00
        n_rw_fuse = (0xFF+1) # number of registers in LPGBT rwf block
        efuse_done_reg = 0xFB 

    # Fusing of registers
    if fusing == "input_file":
        fuse_from_file(system, oh_v, boss, input_config_file, input_vtrx)
    elif fusing == "register":
        fuse_register(system, boss, input_register, input_data)
    elif fusing == "user_id":
        fuse_user_id(system, boss, user_id)
    print ("")
    
    if complete==1:
        print (Colors.YELLOW + "\nFusing Complete Configuration: 0x0EF for OH_v1 (dllConfigDone, pllConfigDone, updateEnable) or 0x0FF for OH_v2 (dllConfigDone, pllConfigDone)" + Colors.ENDC)
        if oh_v == 1:
            fuse_register(system, boss, str(efuse_done_reg), "0x07") #dllConfigDone=1, pllConfigDone=1, updateEnable=1
        elif oh_v == 2:
            fuse_register(system, boss, str(efuse_done_reg), "0x06") #dllConfigDone=1, pllConfigDone=1
        if oh_v == 2:
            print (Colors.YELLOW + "\nFusing CRC registers\n" + Colors.ENDC)

            protected_registers = read_all_fuse_data(n_rw_fuse)
            crc_registers = calculate_crc(protected_registers)
            crc = crc_registers[0] | (crc_registers[1] << 8) | (crc_registers[2] << 16) | (crc_registers[3] << 24)
            print ("CRC: %d\n"%crc)
            fuse_register(system, boss, 0x0FC, crc_registers[0])
            fuse_register(system, boss, 0x0FD, crc_registers[1])
            fuse_register(system, boss, 0x0FE, crc_registers[2])
            fuse_register(system, boss, 0x0FF, crc_registers[3])

    # Write the fuse values of registers in text file
    if boss:
        lpgbt_write_fuse_file("lpgbt_data/fuse_boss_ohv%d.txt"%oh_v)
    else:
        lpgbt_write_fuse_file("lpgbt_data/fuse_sub_ohv%d.txt"%oh_v)

def fuse_from_file(system, oh_v, boss, filename, vtrx):
    f = open(filename, "r")
    config = {}
    for line in f.readlines():
        config[int(line.split()[0],16)] = int(line.split()[1],16)
    f.close()
    
    # Fuse settings to enable TX2 of VTRX+ on start-up
    if vtrx and boss:
        config[0x03f] = 0xC0 # I2CMaster 2 selected
        config[0x040] = 0x50 # VTRX+ I2C slave address
        config[0x041] = 0x08 # Set 100 kHz and 2 bytes of data to be written
        config[0x042] = 0x00 # Data0: register address for TX channel enable
        config[0x043] = 0x03 # Data1: data value to enable TX2 (also TX1 which is enabled by default)
        
    data = 0x00

    print(Colors.YELLOW + "Fusing from file \"%s\"" % filename)
    print(Colors.ENDC)
    en = "no"
    en = raw_input(Colors.YELLOW + "Please type \"yes\" to continue: " + Colors.ENDC)
    if (en != "yes"):
        print (Colors.YELLOW + "Fusing not done, exiting" + Colors.ENDC)
        rw_terminate()

    print ("")
    write_fuse_magic(1)

    for reg_addr in range(0, len(config)):
        # Maximum fusible register
        if (reg_addr > (n_rw_fuse-1)):
            return

        if ((reg_addr % 4) == 0):
            data = 0x00

        # DONT FUSE efuse_done_reg HERE. Put it in a separate function for safety w/ updateEnable
        if reg_addr == efuse_done_reg:
            value = 0
        else:
            value = config[reg_addr]
        data |= value << (8 * (reg_addr % 4))

        if ((reg_addr % 4) == 3) and data != 0:
            write_blow_and_check_fuse(system, reg_addr & 0xfffc, data, True)

    write_fuse_magic(0)

# Sets fuse value, blows the fuse, and checks the result. It can operate on a sub-address (one byte out of 4 in the fuse block) whenever fullblock is set to false
def write_blow_and_check_fuse(system, adr, data, fullblock=False):
   if write_fuse_block_data(system, adr, data, fullblock):
      blow_fuse(system, boss)
      check_fuse_block_data(system, adr, data, fullblock)

def write_fuse_block_data(system, adr, data, fullblock=False):
    # Set EFUSE Settings
    # FUSEControl
    writeReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWPULSELENGTH"), 0xC, 0)
    writeReg(getNode("LPGBT.RW.EFUSES.FUSEBLOW"), 0x0, 0)

    fuse_block_adr = adr & 0xfffc
    fuse_block_subadr = adr % 4

    ok = 1
    # Write address
    ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWADDH"), 0xff&(fuse_block_adr>>8)) # FUSEBlowAddH
    ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWADDL"), 0xff&(fuse_block_adr>>0)) # FUSEBlowAddL

    # Zero out the rest of the address block to prevent accidental fusing
    if (not fullblock):
       ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATAA"), 0)
       ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATAB"), 0)
       ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATAC"), 0)
       ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATAD"), 0)

    if (fullblock):
        data0 = 0xff & (data >> 0)
        data1 = 0xff & (data >> 8)
        data2 = 0xff & (data >> 16)
        data3 = 0xff & (data >> 24)
        if "L" in str(hex(data0)):
            data0 = int(hex(data0).rstrip("L"),16)
        if "L" in str(hex(data1)):
            data1 = int(hex(data1).rstrip("L"),16)
        if "L" in str(hex(data2)):
            data2 = int(hex(data2).rstrip("L"),16)
        if "L" in str(hex(data3)):
            data3 = int(hex(data3).rstrip("L"),16)
        ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATAA"), data0)
        ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATAB"), data1)
        ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATAC"), data2)
        ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATAD"), data3)
    else:
        if (fuse_block_subadr==0):
            ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATAA"), data)
        elif (fuse_block_subadr==1):
            ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATAB"), data)
        elif (fuse_block_subadr==2):
            ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATAC"), data)
        elif (fuse_block_subadr==3):
            ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATAD"), data)

    if (not ok):
        print (Colors.RED + "ERROR: Failed to correctly read back fuse data block" + Colors.ENDC)
        write_fuse_magic(0)
        rw_terminate()
    return ok

def blow_fuse(system, boss):
    global TOTAL_EFUSE_ON_TIME_MS
    adr = 0;
    adr |= readReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWADDH")) << 8
    adr |= readReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWADDL")) << 0

    rd = 0;
    rd |= readReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATAA")) << 0
    rd |= readReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATAB")) << 8
    rd |= readReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATAC")) << 16
    rd |= readReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATAD")) << 24
    print ("\nBlowing Fuse with BLOCK ADDRESS = 0X%03X, BLOCK DATA = 0X%08X" % (adr, rd))

    # Start 2.5V
    t0_efusepower = time()
    lpgbt_efuse(boss, 1)
    sleep (0.001) # 1 ms for the 2.5V to turn on

    # Write 1 to Fuseblow
    writeReg(getNode("LPGBT.RW.EFUSES.FUSEBLOW"), 0x1, 0) # fuse blow

    # Wait for Fuseblowdone
    done = 0;
    t0 = time()
    while (done==0):
        if system!="dryrun":
            done = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEBLOWDONE"))
        else:
            done = 1
        if int(round((time() - t0) * 1000)) > FUSE_TIMEOUT_MS:
            # Stop 2.5V
            lpgbt_efuse(boss, 0)
            # Write 0 to Fuseblow
            writeReg(getNode("LPGBT.RW.EFUSES.FUSEBLOW"), 0x0, 0)
            TOTAL_EFUSE_ON_TIME_MS += int(round((time() - t0_efusepower) * 1000 ))
            print (Colors.RED + "ERROR: Fusing operation took longer than %d ms and was terminated due to a timeout" % FUSE_TIMEOUT_MS + Colors.ENDC)
            print (Colors.YELLOW + "Total efuse power on time: %d ms" % TOTAL_EFUSE_ON_TIME_MS + Colors.RED)
            write_fuse_magic(0)
            rw_terminate()

    # Stop 2.5V
    lpgbt_efuse(boss, 0)
    sleep (0.001) # 1 ms for the 2.5V to turn off
    TOTAL_EFUSE_ON_TIME_MS += int(round((time() - t0_efusepower) * 1000))
    print ("Total EFUSE power on time: %d ms" % TOTAL_EFUSE_ON_TIME_MS)

    err = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEBLOWERROR"))
    # Write 0 to Fuseblow
    writeReg(getNode("LPGBT.RW.EFUSES.FUSEBLOW"), 0x0, 0) # deassert fuse blow

    if err:
        print (Colors.RED + "ERROR: \tFuse blown, err=%d" % err + Colors.RED)
        write_fuse_magic(0)
        rw_terminate()

def check_fuse_block_data(system, adr, data, fullblock=False):
    global fuse_list
    fuse_block_adr    = adr & 0xfffc
    fuse_block_subadr = adr % 4

    # Write fuseread on
    #writeReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWPULSELENGTH"), 0xC, 0)
    writeReg(getNode("LPGBT.RW.EFUSES.FUSEREAD"), 0x1, 0)

    valid = 0
    while (valid==0):
        if system!="dryrun":
            valid = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEDATAVALID"))
        else:
            valid = 1

    # Write address
    writeReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWADDH"), 0xff&(fuse_block_adr>>8), 0) # FUSEBlowAddH
    writeReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWADDL"), 0xff&(fuse_block_adr>>0), 0) # FUSEBlowAddL

    read=4*[0]
    read[0] = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEVALUESA")) # FUSEValuesA
    read[1] = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEVALUESB")) # FUSEValuesB
    read[2] = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEVALUESC")) # FUSEValuesC
    read[3] = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEVALUESD")) # FUSEValuesD

    # Write fuseread off
    writeReg(getNode("LPGBT.RW.EFUSES.FUSEREAD"), 0x0, 0)

    read_dword = 0
    if (fullblock):
        read_dword = (read[0]) | (read[1]<<8) | (read[2] << 16) | (read[3] << 24)
        if system!="dryrun":
            fuse_list[adr] = read[0]
            fuse_list[adr+1] = read[1]
            fuse_list[adr+2] = read[2]
            fuse_list[adr+3] = read[3]
        else:
            fuse_list[adr] = 0xff & (data >> 0)
            fuse_list[adr+1] = 0xff & (data >> 8)
            fuse_list[adr+2] = 0xff & (data >> 16)
            fuse_list[adr+3] = 0xff & (data >> 24)
    else:
        read_dword = read[fuse_block_subadr]
        if system!="dryrun":
            fuse_list[adr] = read_dword
        else:
            fuse_list[adr] = data

    print_result_string = ""
    if data==read_dword:
        print_result_string += Colors.GREEN
    else:
        print_result_string += Colors.RED
    print_result_string += "Checking FUSE Address = 0X%03X, Block = 0X%03X Sub = %d, Valid = %d, Data_Expect = 0X%X, Data_read = 0X%X\n" % (adr, fuse_block_adr, fuse_block_subadr, valid, data, read_dword)
    print_result_string += Colors.ENDC
    print (print_result_string)
    
    if (system!="dryrun" and data!=read_dword):
        print (Colors.RED + "ERROR: Mismatch in expected and read data from EFUSE" + Colors.ENDC)
        write_fuse_magic(0)
        rw_terminate()

def read_all_fuse_data(n_rw_fuse):
    protected_registers = (n_rw_fuse-4)*[0]
    for i in range(0, (n_rw_fuse-4)):
        if i%4 != 0:
            continue
        fuse_block_adr = i & 0xfffc

        # Write fuseread on
        writeReg(getNode("LPGBT.RW.EFUSES.FUSEREAD"), 0x1, 0)

        valid = 0
        while (valid==0):
            if system!="dryrun":
                valid = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEDATAVALID"))
            else:
                valid = 1

        # Write address
        writeReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWADDH"), 0xff&(fuse_block_adr>>8), 0) # FUSEBlowAddH
        writeReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWADDL"), 0xff&(fuse_block_adr>>0), 0) # FUSEBlowAddL

        protected_registers[i] = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEVALUESA")) # FUSEValuesA
        protected_registers[i+1] = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEVALUESB")) # FUSEValuesB
        protected_registers[i+2] = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEVALUESC")) # FUSEValuesC
        protected_registers[i+3] = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEVALUESD")) # FUSEValuesD

        # Write fuseread off
        writeReg(getNode("LPGBT.RW.EFUSES.FUSEREAD"), 0x0, 0)

    return protected_registers

def fuse_register(system, boss, input_register, input_data):
    input_register = int(input_register,16)
    input_data = int(input_data,16)
    if boss:
        print (Colors.YELLOW + "Fusing Boss lpGBT, register: " + str(hex(input_register)) + ", data: " + str(hex(input_data)) + Colors.ENDC)
    else:
        print (Colors.YELLOW + "Fusing Sub lpGBT, register: " + str(hex(input_register)) + ", data: " + str(hex(input_data)) + Colors.ENDC)

    en = "no"
    en = raw_input(Colors.YELLOW + "Please type \"yes\" to continue: " + Colors.ENDC)
    if (en != "yes"):
        print (Colors.YELLOW + "Fusing not done, exiting" + Colors.ENDC)
        rw_terminate()

    print ("")
    write_fuse_magic(1)
    write_blow_and_check_fuse(system, input_register, input_data, False)
    write_fuse_magic(0)

def fuse_user_id(system, boss, user_id):
    user_id = int(user_id, 16)
    if boss:
        print (Colors.YELLOW + "Fusing Boss lpGBT with USER ID: " + str(hex(user_id)) + Colors.ENDC)
    else:
        print (Colors.YELLOW + "Fusing Sub lpGBT with USER ID: " + str(hex(user_id)) + Colors.ENDC)

    en = "no"
    en = raw_input(Colors.YELLOW + "Please type \"yes\" to continue: " + Colors.ENDC)
    if (en != "yes"):
        print (Colors.YELLOW + "Fusing not done, exiting" + Colors.ENDC)
        rw_terminate()

    print ("")
    write_fuse_magic(1)

    data_userid = {}
    data_userid[0x004] = (user_id >> 24)&0xff
    data_userid[0x005] = (user_id >> 16)&0xff
    data_userid[0x006] = (user_id >> 8)&0xff
    data_userid[0x007] = (user_id >> 0)&0xff
    data = 0
    for r in data_userid:
        data |= data_userid[r] << (8 * (r % 4))
     
    write_blow_and_check_fuse(system, 0x007 & 0xfffc, data, True)

    write_fuse_magic(0)

def write_fuse_magic(fuse_enable):
    value = 0x00
    if (fuse_enable):
        value = 0xA3
    # FuseMagic [7:0]
    writeReg(getNode("LPGBT.RW.EFUSES.FUSEMAGICNUMBER"), value, 0)
    print ("Magic Number Set for Fusing: " + str(hex(value)))
    magic_number = readReg(getNode("LPGBT.RW.EFUSES.FUSEMAGICNUMBER"))
    print ("Reading Magic Number: " + str(hex(magic_number)))

def lpgbt_write_fuse_file(fuse_file = "fuse.txt"):
    f = open(fuse_file, "w+")
    for i in range(n_rw_fuse):
        val = fuse_list[i]
        write_string = "0x%03X  0x%02X\n" % (i, val)
        f.write(write_string)
    f.close()

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="LpGBT Fusing for ME0 Optohybrid")
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or dryrun")
    parser.add_argument("-y", "--oh_v", action="store", dest="oh_v", default="1", help="oh_v = 1 or 2")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-f", "--fusing", action="store", dest="fusing", help="fusing = input_file, register, user_id")
    parser.add_argument("-i", "--input", action="store", dest="input_config_file", help="input_config_file = .txt file")
    parser.add_argument("-v", "--vtrx", action="store", default = "0", dest="vtrx", help="vtrx = 1 if you want to fuse settings to enable TX2 on startup, 0 by default")
    parser.add_argument("-r", "--register", action="store", dest="register", help="register = Enter a 16 bit register address in hex format")
    parser.add_argument("-d", "--data", action="store", dest="data", help="data = Enter a 8 bit data for the register in hex format")
    parser.add_argument("-u", "--user_id", action="store", dest="user_id", help="user_id = Enter a 32 bit number in hex format")
    parser.add_argument("-c", "--complete", action="store", dest="complete", default = "0", help="complete = Set to 1 to fuse complete configuration by fusing dllConfigDone, pllConfigDone, updateEnable (only for OHv1)")
    args = parser.parse_args()

    if args.system == "chc":
        print ("Using Rpi CHeeseCake for fusing")
    elif args.system == "backend":
        #print ("Using Backend for fusing")
        print (Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun allowed for fusing" + Colors.ENDC)
        sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for fusing")
        print (Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun allowed for fusing" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually fusing lpGBT")
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
        print (Colors.YELLOW + "Please select boss or sub" + Colors.ENDC)
        sys.exit()
    elif (args.lpgbt=="boss"):
        print ("Fusing boss LPGBT")
        boss=1
    elif (args.lpgbt=="sub"):
        print ("Fusing sub LPGBT")
        boss=0
    else:
        print (Colors.YELLOW + "Please select boss or sub" + Colors.ENDC)
        sys.exit()
    if boss is None:
        sys.exit()

    args.vtrx = int(args.vtrx)
    if args.vtrx not in [0,1]:
        print (Colors.YELLOW + "Invalid value for vtrx option, only 0 or 1 allowed" + Colors.ENDC)
        sys.exit()
    if args.complete not in ["0", "1"]:
        print (Colors.YELLOW + "Invalid value for complete option, only 0 or 1 allowed" + Colors.ENDC)
        sys.exit()
            
    if args.fusing == "input_file":
        if args.register is not None:
            print (Colors.YELLOW + "Register not needed" + Colors.ENDC)
            sys.exit()
        if args.data is not None:
            print (Colors.YELLOW + "Data not needed" + Colors.ENDC)
            sys.exit()
        if args.user_id is not None:
            print (Colors.YELLOW + "Do not enter USER ID" + Colors.ENDC)
            sys.exit()
        if args.input_config_file is None:
            print (Colors.YELLOW + "Need input file for fusing" + Colors.ENDC)
            sys.exit()
        if args.vtrx and not boss:
            print (Colors.YELLOW + "Can fuse settings for VTRX+ only for boss" + Colors.ENDC)
            sys.exit()
        print ("Fusing from Input File: " + args.input_config_file)
    elif args.fusing == "register":
        if args.user_id is not None:
            print (Colors.YELLOW + "Do not enter USER ID" + Colors.ENDC)
            sys.exit()
        if args.input_config_file is not None:
            print (Colors.YELLOW + "Input file not needed" + Colors.ENDC)
            sys.exit()
        if args.vtrx:
            print (Colors.YELLOW + "Fusing settings for VTRX+ only allowed when fusing from input file" + Colors.ENDC)
            sys.exit()
        if args.register is None:
            print (Colors.YELLOW + "Provide register to be fused" + Colors.ENDC)
            sys.exit()
        if args.data is None:
            print (Colors.YELLOW + "Provide data for register to be fused" + Colors.ENDC)
            sys.exit()
        if int(args.register,16) > (2**16-1):
            print (Colors.YELLOW + "Register address can be maximum 16 bits" + Colors.ENDC)
            sys.exit()
        if int(args.data,16) > (2**8-1):
            print (Colors.YELLOW + "Register data can be maximum 8 bits" + Colors.ENDC)
            sys.exit()
        print ("Fusing for Register: " + args.register + " , Data: " + args.data)
    elif args.fusing == "user_id":
        if args.register is not None:
            print (Colors.YELLOW + "Register not needed" + Colors.ENDC)
            sys.exit()
        if args.data is not None:
            print (Colors.YELLOW + "Data not needed" + Colors.ENDC)
            sys.exit()
        if args.input_config_file is not None:
            print (Colors.YELLOW + "Input file not needed" + Colors.ENDC)
            sys.exit()
        if args.vtrx:
            print (Colors.YELLOW + "Fusing settings for VTRX+ only allowed when fusing from input file" + Colors.ENDC)
            sys.exit()
        if args.user_id is None:
            print (Colors.YELLOW + "Enter the USER ID to be fused" + Colors.ENDC)
            sys.exit()
        if int(args.user_id,16) > (2**32-1):
            print (Colors.YELLOW + "USER ID can be maximum 32 bits" + Colors.ENDC)
            sys.exit()
        print ("Fusing USER_ID as :" + args.user_id)
    elif args.fusing is None:
        if args.complete == "0":
            print (Colors.YELLOW + "Enter option for fusing or completion" + Colors.ENDC)
            sys.exit()
        else:
            if args.register is not None:
                print (Colors.YELLOW + "Register not needed" + Colors.ENDC)
                sys.exit()
            if args.data is not None:
                print (Colors.YELLOW + "Data not needed" + Colors.ENDC)
                sys.exit()
            if args.user_id is not None:
                print (Colors.YELLOW + "Do not enter USER ID" + Colors.ENDC)
                sys.exit() 
            if args.input_config_file is not None:
                print (Colors.YELLOW + "Input file not needed" + Colors.ENDC)
                sys.exit()
            if args.vtrx:
                print (Colors.YELLOW + "Fusing settings for VTRX+ only allowed when fusing from input file" + Colors.ENDC)
                sys.exit()      
    else:
        print (Colors.YELLOW + "Invalid option for fusing" + Colors.ENDC)
        sys.exit()

    if args.complete == "1": 
        en_complete = "no"
        print (Colors.YELLOW + "Final fusing, no changes possible after this" + Colors.ENDC)
        en_complete = raw_input(Colors.YELLOW + "Please type \"yes\" to continue: " + Colors.ENDC)
        if (en_complete != "yes"):
            print (Colors.YELLOW + "Fusing not done, exiting" + Colors.ENDC)
            sys.exit()

    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML(oh_v)
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system, oh_v, boss)
    print("Initialization Done\n")
    
    # Readback rom register to make sure communication is OK
    if args.system!="dryrun":
        check_rom_readback()
        check_lpgbt_mode(boss)

    # Check if lpGBT is READY 
    if args.system!="dryrun" and args.system!="backend": 
        check_lpgbt_ready()

    # Fusing lpGBT
    try:
        main(args.system, oh_v, boss, args.fusing, args.input_config_file, args.vtrx, args.register, args.data, args.user_id, int(args.complete))
    except KeyboardInterrupt:
        print (Colors.RED + "\nKeyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print (Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()

















