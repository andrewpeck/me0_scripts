from rw_reg_lpgbt import *
from time import sleep, time
import sys
import argparse

FUSE_TIMEOUT_MS = 10 # in ms
TOTAL_EFUSE_ON_TIME_MS = 0 # in ms
fuse_list = {}
for i in range(240):
    fuse_list[i] = 0x00
n_rw_fuse = (0xEF+1) # number of registers in LPGBT rwf block

def main(system, boss, fusing, input_config_file, input_vtrx, input_register, input_data, user_id, complete):

    # Fusing of registers
    if fusing == "input_file":
        fuse_from_file(system, boss, input_config_file, input_vtrx)
        if complete==1:
            print ("\nFusing Complete Configuration: 0xEF (dllConfigDone, pllConfigDone, updateEnable)")
            fuse_register(system, boss, "0xEF", "0x07") #dllConfigDone=1, pllConfigDone=1, updateEnable=1
    elif fusing == "register":
        fuse_register(system, boss, input_register, input_data)
    elif fusing == "user_id":
        fuse_user_id(system, boss, user_id)
    print ("")

    # Write the fuse values of registers in text file
    if boss:
        lpgbt_write_fuse_file("fuse_boss.txt")
    else:
        lpgbt_write_fuse_file("fuse_sub.txt")

def check_rom_readback():
    romreg=readReg(getNode("LPGBT.RO.ROMREG"))
    if (romreg != 0xA5):
        print ("ERROR: no communication with LPGBT. ROMREG=0x%x, EXPECT=0x%x" % (romreg, 0xA5))
        rw_terminate()
    else:
        print ("Successfully read from ROM. I2C communication OK")

def fuse_from_file(system, boss, filename, vtrx):
    f = open(filename, 'r')
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

    print("Fusing from file \"%s\"" % filename)
    en = "no"
    en = raw_input("Please type \"yes\" to continue: ")
    if (en != "yes"):
        print ("Fusing not done, exiting")
        rw_terminate()

    write_fuse_magic(1)

    for reg_addr in range(0, len(config)):
        # Maximum fusible register
        if (reg_addr > 0xEF):
            return

        if ((reg_addr % 4) == 0):
            data = 0x00

        # DONT FUSE 0xEF HERE. Put it in a separate function for safety w/ updateEnable
        if reg_addr == 0xEF:
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
    fuse_block_adr = adr & 0xfffc
    fuse_block_subadr = adr % 4

    ok = 1
    # Write address
    ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWADDRESS1"), 0xff&(fuse_block_adr>>8)) # [0x10e] FUSEBlowAddH
    ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWADDRESS0"), 0xff&(fuse_block_adr>>0)) # [0x10f] FUSEBlowAddL

    # Zero out the rest of the address block to prevent accidental fusing
    if (not fullblock):
       ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATA0"), 0)
       ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATA1"), 0)
       ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATA2"), 0)
       ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATA3"), 0)

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
        ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATA0"), data0)
        ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATA1"), data1)
        ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATA2"), data2)
        ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATA3"), data3)
    else:
        if (fuse_block_subadr==0):
            ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATA0"), data)
        elif (fuse_block_subadr==1):
            ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATA1"), data)
        elif (fuse_block_subadr==2):
            ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATA2"), data)
        elif (fuse_block_subadr==3):
            ok &= writeandcheckReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATA3"), data)

    if (not ok):
        print ("ERROR: Failed to correctly read back fuse data block")
        write_fuse_magic(0)
        rw_terminate()
    return ok

def blow_fuse(system, boss):
    global TOTAL_EFUSE_ON_TIME_MS
    adr = 0;
    adr |= readReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWADDRESS1")) << 8
    adr |= readReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWADDRESS0")) << 0

    rd = 0;
    rd |= readReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATA0")) << 0
    rd |= readReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATA1")) << 8
    rd |= readReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATA2")) << 16
    rd |= readReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWDATA3")) << 24
    print ("\nBlowing Fuse with BLOCK ADDRESS = 0X%03X, BLOCK DATA = 0X%08X" % (adr, rd))

    # Set EFUSE Settings
    # [0x109] FUSEControl
    writeReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWPULSELENGTH"), 0xC, 0)
    writeReg(getNode("LPGBT.RW.EFUSES.FUSEBLOW"), 0x0, 0)

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
            print ("ERROR: Fusing operation took longer than %d ms and was terminated due to a timeout" % FUSE_TIMEOUT_MS)
            print ("Total efuse power on time: %d ms" % TOTAL_EFUSE_ON_TIME_MS)
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
        print ("ERROR: \tFuse blown, err=%d" % err)
        write_fuse_magic(0)
        rw_terminate()

def check_fuse_block_data(system, adr, data, fullblock=False):
    fuse_block_adr    = adr & 0xfffc
    fuse_block_subadr = adr % 4

    # Write address
    writeReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWADDRESS1"), 0xff&(fuse_block_adr>>8), 0) # [0x10e] FUSEBlowAddH
    writeReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWADDRESS0"), 0xff&(fuse_block_adr>>0), 0) # [0x10f] FUSEBlowAddL

    # Write fuseread on
    writeReg(getNode("LPGBT.RW.EFUSES.FUSEBLOWPULSELENGTH"), 0xC, 0)
    writeReg(getNode("LPGBT.RW.EFUSES.FUSEREAD"), 0x1, 0)

    valid = 0
    while (valid==0):
        if system!="dryrun":
            valid = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEDATAVALID"))
        else:
            valid = 1
    read=4*[0]
    read[0] = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEVALUESA")) # [0x1a2] FUSEValuesA
    read[1] = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEVALUESB")) # [0x1a3] FUSEValuesB
    read[2] = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEVALUESC")) # [0x1a4] FUSEValuesC
    read[3] = readReg(getNode("LPGBT.RO.FUSE_READ.FUSEVALUESD")) # [0x1a5] FUSEValuesD

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

    print ("Checking FUSE Address = 0X%03X, Block = 0X%03X Sub = %d, Valid = %d, Data_Expect = 0X%X, Data_read = 0X%X\n" % (adr, fuse_block_adr, fuse_block_subadr, valid, data, read_dword))
    if (system!="dryrun" and data!=read_dword):
        print ("ERROR: Mismatch in expected and read data from EFUSE")
        write_fuse_magic(0)
        rw_terminate()

def fuse_register(system, boss, input_register, input_data):
    input_register = int(input_register,16)
    input_data = int(input_data,16)
    if boss:
        print ("Fusing Boss lpGBT, register: " + str(hex(input_register)) + ", data: " + str(hex(input_data)))
    else:
        print ("Fusing Sub lpGBT, register: " + str(hex(input_register)) + ", data: " + str(hex(input_data)))

    en = "no"
    en = raw_input("Please type \"yes\" to continue: ")
    if (en != "yes"):
        print ("Fusing not done, exiting")
        rw_terminate()

    write_fuse_magic(1)
    write_blow_and_check_fuse(system, input_register, input_data, False)
    write_fuse_magic(0)

def fuse_user_id(system, boss, user_id):
    user_id = int(user_id, 16)
    if boss:
        print ("Fusing Boss lpGBT with USER ID: " + str(hex(user_id)))
    else:
        print ("Fusing Sub lpGBT with USER ID: " + str(hex(user_id)))

    en = "no"
    en = raw_input("Please type \"yes\" to continue: ")
    if (en != "yes"):
        print ("Fusing not done, exiting")
        rw_terminate()

    write_fuse_magic(1)

    write_blow_and_check_fuse(system, 0x007, (user_id >> 0)&0xff, False) #[0x007] USERID3 BITS [7:0]
    write_blow_and_check_fuse(system, 0x006, (user_id >> 8)&0xff, False) #[0x006] USERID2 BITS [15:8]
    write_blow_and_check_fuse(system, 0x005, (user_id >> 16)&0xff, False) #[0x005] USERID1 BITS [23:16]
    write_blow_and_check_fuse(system, 0x004, (user_id >> 24)&0xff, False) #[0x004] USERID0 BITS [31:24]

    write_fuse_magic(0)

def write_fuse_magic(fuse_enable):
    value = 0x00
    if (fuse_enable):
        value = 0xA3
    # [0x110] FuseMagic [7:0]
    writeReg(getNode("LPGBT.RW.EFUSES.FUSEMAGICNUMBER"), value, 0)
    print ("Magic Number Set for Fusing: " + str(hex(value)))

def lpgbt_write_fuse_file(fuse_file = 'fuse.txt'):
    f = open(fuse_file, "w+")
    for i in range(n_rw_fuse):
        val = fuse_list[i]
        write_string = "0x%03X  0x%02X\n" % (i, val)
        f.write(write_string)
    f.close()

if __name__ == '__main__':

    # Parsing arguments
    parser = argparse.ArgumentParser(description='LpGBT Fusing for ME0 Optohybrid')
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or dryrun")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-f", "--fusing", action="store", dest="fusing", help="fusing = input_file, register, user_id")
    parser.add_argument("-i", "--input", action="store", dest="input_config_file", help="input_config_file = .txt file")
    parser.add_argument("-v", "--vtrx", action="store", default = "0", dest="vtrx", help="vtrx = 1 if you want to fuse settings to enable TX2 on startup, 0 by default")
    parser.add_argument("-r", "--register", action="store", dest="register", help="register = Enter a 16 bit register address in hex format")
    parser.add_argument("-d", "--data", action="store", dest="data", help="data = Enter a 8 bit data for the register in hex format")
    parser.add_argument("-u", "--user_id", action="store", dest="user_id", help="user_id = Enter a 32 bit number in hex format")
    parser.add_argument("-c", "--complete", action="store", dest="complete", default = "0", help="complete = Set to 1 to fuse complete configuration by fusing dllConfigDone, pllConfigDone, updateEnable")
    args = parser.parse_args()

    if args.system == "chc":
        print ("Using Rpi CHeeseCake for fusing")
    elif args.system == "backend":
        #print ("Using Backend for fusing")
        print ("Only chc (Rpi Cheesecake) or dryrun allowed for fusing")
        sys.exit()
    elif args.system == "dongle":
        #print ("Using USB Dongle for fusing")
        print ("Only chc (Rpi Cheesecake) or dryrun allowed for fusing")
        sys.exit()
    elif args.system == "dryrun":
        print ("Dry Run - not actually fusing lpGBT")
    else:
        print ("Only valid options: chc, backend, dongle, dryrun")
        sys.exit()

    boss = None
    if args.lpgbt is None:
        print ("Please select boss or sub")
        sys.exit()
    elif (args.lpgbt=="boss"):
        print ("Fusing boss LPGBT")
        boss=1
    elif (args.lpgbt=="sub"):
        print ("Fusing sub LPGBT")
        boss=0
    else:
        print ("Please select boss or sub")
        sys.exit()
    if boss is None:
        sys.exit()

    args.vtrx = int(args.vtrx)
    if args.vtrx not in [0,1]:
        print ("Invalid value for vtrx option, only 0 or 1 allowed")
        sys.exit()
    if args.complete not in ["0", "1"]:
        print ("Invalid valuefor complete option, only 0 or 1 allowed")
        sys.exit()
        
    if args.fusing == "input_file":
        if args.register is not None:
            print ("Register not needed")
            sys.exit()
        if args.data is not None:
            print ("Data not needed")
            sys.exit()
        if args.user_id is not None:
            print ("Do not enter USER ID")
            sys.exit()
        if args.input_config_file is None:
            print ("Need input file for fusing")
            sys.exit()
        if args.vtrx and not boss:
            print ("Can fuse settings for VTRX+ only for boss")
            sys.exit()
        print ("Fusing from Input File: " + args.input_config_file)
    elif args.fusing == "register":
        if args.user_id is not None:
            print ("Do not enter USER ID")
            sys.exit()
        if args.input_config_file is not None:
            print ("Input file not needed")
            sys.exit()
        if not args.vtrx:
            print ("Fusing settings for VTRX+ only allowed when fusing from input file")
            sys.exit()
        if args.register is None:
            print ("Provide register to be fused")
            sys.exit()
        if args.data is None:
            priint ("Provide data for register to be fused")
            sys.exit()
        if int(args.register,16) > (2**16-1):
            print ("Register address can be maximum 16 bits")
            sys.exit()
        if int(args.data,16) > (2**8-1):
            print ("Register data can be maximum 8 bits")
            sys.exit()
        print ("Fusing for Register: " + args.register + " , Data: " + args.data)
    elif args.fusing == "user_id":
        if args.register is not None:
            print ("Register not needed")
            sys.exit()
        if args.data is not None:
            print ("Data not needed")
            sys.exit()
        if args.input_config_file is not None:
            print ("Input file not needed")
            sys.exit()
        if not args.vtrx:
            print ("Fusing settings for VTRX+ only allowed when fusing from input file")
            sys.exit()
        if args.user_id is None:
            print ("Enter the USER ID to be fused")
            sys.exit()
        if int(args.user_id,16) > (2**32-1):
            print ("USER ID can be maximum 32 bits")
            sys.exit()
        print ("Fusing USER_ID as :" + args.user_id)
    else:
        print ("Invalid option for fusing")
        sys.exit()

    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML()
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system, boss)
    print("Initialization Done\n")
    
    # Readback rom register to make sure communication is OK
    if args.system!="dryrun":
        check_rom_readback()

    # Fusing lpGBT
    try:
        main(args.system, boss, args.fusing, args.input_config_file, args.vtrx, args.register, args.data, args.user_id, int(args.complete))
    except KeyboardInterrupt:
        print ("\nKeyboard Interrupt encountered")
        rw_terminate()
    except EOFError:
        print ("\nEOF Error")
        rw_terminate()

    # Termination
    rw_terminate()

















