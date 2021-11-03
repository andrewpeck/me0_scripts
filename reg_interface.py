from cmd import Cmd
import sys, os, subprocess
from rw_reg_lpgbt import *
import argparse


class Prompt(Cmd):

    def do_hello(self, args):
        """Says hello. If you provide a name, it will greet you with it."""
        if len(args) == 0:
            name = "stranger"
        else:
            name = args
        print("Hello, %s" % name)

    def do_read(self, args):
        """Reads register. USAGE: read <register name>. OUTPUT <address> <mask> <permission> <name> <value>"""
        reg = getNode(args)
        if reg is not None:
            address = reg.real_address
            if "r" in str(reg.permission):
                print(displayReg(reg))
            elif reg.isModule:
                print("This is a module!")
            else:
                print(hex(address), reg.name, "No read permission!")
        else:
            print(args, "not found!")

    def complete_read(self, text, line, begidx, endidx):
        return completeReg(text)

    def do_write(self, args):
        """Writes register. USAGE: write <register name> <register value>"""
        arglist = args.split()
        if len(arglist) != 2:
            print("Incorrect number of arguments!")
        else:
            reg = getNode(arglist[0])
            if reg is not None:
                try:
                    value = parseInt(arglist[1])
                except:
                    print("Write Value must be a number!")
                    return
                if "w" in str(reg.permission):
                    print(writeReg(reg, value, 0))
                else:
                    print("No write permission!")
            else:
                print(arglist[0], "not found!")

    def complete_write(self, text, line, begidx, endidx):
        return completeReg(text)

    def do_readGroup(self, args):  # INEFFICIENT
        """Read all registers below node in register tree. USAGE: readGroup <register/node name> """
        node = getNode(args)
        if node is not None:
            print("NODE:", node.name)
            kids = []
            getAllChildren(node, kids)
            print(len(kids), "CHILDREN")
            for reg in kids:
                if "r" in str(reg.permission): print
                displayReg(reg)
        else:
            print(args, "not found!")

    def complete_readGroup(self, text, line, begidx, endidx):
        return completeReg(text)

    def do_readFW(self, args):
        """Quick read of all FW-related registers"""
        for reg in getNodesContaining("STATUS.FW"):
            if "r" in str(reg.permission): print(hex(reg.real_address), reg.permission, reg.name, readRegStr(reg))

    def do_readKW(self, args):
        """Read all registers containing KeyWord. USAGE: readKW <KeyWord>"""
        if getNodesContaining(args) is not None and args != "":
            for reg in getNodesContaining(args):
                address = reg.real_address
                if "r" in str(reg.permission):
                    print(hex(address).rstrip("L"), reg.permission, reg.name, readRegStr(reg))
                elif reg.isModule:
                    print(hex(address).rstrip("L"), reg.permission, reg.name)  # ,"Module!"
                else:
                    print(hex(address).rstrip("L"), reg.permission, reg.name)  # ,"No read permission!"
        else:
            print(args, "not found!")

    def do_readAll(self, args):
        """Read all registers with read-permission"""
        for reg in getNodesContaining(""):
            if "r" in (reg.permission):
                print(displayReg(reg))

    def do_exit(self, args):
        """Exit program"""
        return True

    def do_readAddress(self, args):
        """ Directly read address. USAGE: readAddress <address> """
        try:
            reg = getNodeFromAddress(parseInt(args))
        except:
            print("Error retrieving node.")
            return
        if reg is not None:
            address = reg.real_address
            if "r" in str(reg.permission):
                print(hex(address), "{0:#010x}".format(reg.mask), reg.permission, reg.name, readRegStr(reg))
            elif reg.isModule:
                print("This is a module!")
            else:
                print(hex(address), reg.name, "No read permission!")
        else:
            print(args, "not found!")

    def do_readRawAddress(self, args):
        """Read raw address (from XML file). USAGE: readRawAddress <address> """
        try:
            print(readRawAddress(args))
        except:
            print("Error reading address. (reg_interface)")

    def do_mpeek(self, args):
        """Basic mpeek command to read register. USAGE: mpeek <address>"""
        print(mpeek(args))

    def do_mpoke(self, args):
        """Basic mpoke command to write register. USAGE: mpoke <address> <value>"""
        arglist = args.split()
        if len(arglist) == 2:
            print(mpoke(arglist[0], arglist[1]))
        else:
            print("Incorrect number of arguments!")


if __name__ == "__main__":
    # Parsing arguments
    parser = argparse.ArgumentParser(description="Register Interface for lpGBT")
    parser.add_argument("-s", "--system", action="store", dest="system", help="system = chc or backend or dongle or dryrun")
    parser.add_argument("-y", "--oh_v", action="store", dest="oh_v", help="oh_v = 1 or 2")
    parser.add_argument("-l", "--lpgbt", action="store", dest="lpgbt", help="lpgbt = boss or sub")
    parser.add_argument("-o", "--ohid", action="store", dest="ohid", help="ohid = 0-7 (only needed for backend)")
    parser.add_argument("-g", "--gbtid", action="store", dest="gbtid", help="gbtid = 0, 1 (only needed for backend)")
    parser.add_argument("-lv", "--lpgbt_v", action="store", dest="lpgbt_v", default="0", help="lpgbt_v = 0 or 1")
    args = parser.parse_args()

    if args.system == "chc":
        print("Using Rpi CHeeseCake for interface")
    elif args.system == "backend":
        print("Using Backend for interface")
        # print ("Only chc (Rpi Cheesecake) or dryrun supported at the moment")
        # sys.exit()
    elif args.system == "dongle":
        # print ("Using USB Dongle for interface")
        print(Colors.YELLOW + "Only chc (Rpi Cheesecake) or dryrun supported at the moment" + Colors.ENDC)
        sys.exit()
    elif args.system == "dryrun":
        print("Dry Run - not actually interfacing with lpGBT")
    else:
        print(Colors.YELLOW + "Only valid options: chc, backend, dongle, dryrun" + Colors.ENDC)
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
        print(Colors.YELLOW + "Please select boss or sub" + Colors.ENDC)
        sys.exit()
    elif (args.lpgbt == "boss"):
        print("Configuring LPGBT as boss")
        boss = 1
    elif (args.lpgbt == "sub"):
        print("Configuring LPGBT as sub")
        boss = 0
    else:
        print(Colors.YELLOW + "Please select boss or sub" + Colors.ENDC)
        sys.exit()
    if boss is None:
        sys.exit()

    if args.system == "backend":
        if args.ohid is None:
            print(Colors.YELLOW + "Need OHID for backend" + Colors.ENDC)
            sys.exit()
        if args.gbtid is None:
            print(Colors.YELLOW + "Need GBTID for backend" + Colors.ENDC)
            sys.exit()
        if int(args.ohid) > 7:
            print(Colors.YELLOW + "Only OHID 0-7 allowed" + Colors.ENDC)
            sys.exit()
        if int(args.gbtid) > 1:
            print(Colors.YELLOW + "Only GBTID 0 and 1 allowed" + Colors.ENDC)
            sys.exit()
    else:
        if args.ohid is not None or args.gbtid is not None:
            print(Colors.YELLOW + "OHID and GBTID only needed for backend" + Colors.ENDC)
            sys.exit()

    # Parsing Registers XML File
    print("Parsing xml file...")
    parseXML(oh_v)
    print("Parsing complete...")

    # Initialization (for CHeeseCake: reset and config_select)
    rw_initialize(args.system, boss, args.ohid, args.gbtid)
    print("Initialization Done\n")

    # Readback rom register to make sure communication is OK
    if args.system != "dryrun" and args.system != "backend":
        check_rom_readback()

    try:
        prompt = Prompt()
        prompt.prompt = args.system + ":> "
        prompt.cmdloop("Starting Register Command Line Interface.")
    except KeyboardInterrupt:
        print(Colors.RED + "Keyboard Interrupt encountered" + Colors.ENDC)
        rw_terminate()
    except EOFError:
        print(Colors.RED + "\nEOF Error" + Colors.ENDC)
        rw_terminate()

    # Termination
    rw_terminate()

