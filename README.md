## General

Script for configuring LpGBTs on ME0 Optohybrid using either RPi+Cheesecake (preferred option) or USB dongle

lpGBT naming :

master (ASIAGO schematics) == boss (in software)

slave (ASIAGO schematics) == sub (in software)

## Installation

```
git clone https://github.com/andrewpeck/me0_scripts.git
cd me0_scripts
git checkout cheesecake_integration
```

## Using Backend

Login as root

Set some environment variables (after compiling the 0xbefe repo):

```
export ADDRESS_TABLE="<Absolute Path for 0xbefe/address_table/gem/generated/me0_cvp13/gem_amc.xml>"
export ME0_LIBRWREG_SO="<Absolute Path for 0xbefe/scripts/boards/cvp13/rwreg/librwreg.so>"
export BOARD_TYPE="cvp13"
```

### Configuration

Configure the master/boss lpgbt:

```
python lpgbt_config.py -s backend -l boss -o <OH_LINK> -g <GBT_LINK>
```

Configure the slave/sub lpgbt:

```
python lpgbt_config.py -s backend -l sub -o <OH_LINK> -g <GBT_LINK>
```

Enable TX2 for VTRX+ if required:

```
python lpgbt_vtrx.py -s backend -l boss -o <OH_LINK> -g <GBT_LINK> -t name -c TX1 TX2 -e 1
```

## Using CHeeseCake

### Configuration

Configure the master/boss lpgbt:

```
python lpgbt_config.py -s chc -l boss
```

Configure the slave/sub lpgbt:

```
python lpgbt_config.py -s chc -l sub
```

Enable TX2 for VTRX+ if required (usually VTRX+ enabled during configuration):

```
python lpgbt_vtrx.py -s chc -l boss -t name -c TX2 -e 1
```

### Checking lpGBT Status

Check the status of the master/boss lpgbt:

```
python lpgbt_status.py -s chc -l boss
```

Check the status of the slave/sub lpgbt:

```
python lpgbt_status.py -s chc -l sub
```

### Fusing

Obtain the config .txt files first with a dryrun:

```
python lpgbt_config.py -s dryrun -l boss
python lpgbt_config.py -s dryrun -l sub

```

Fuse the USER IDs with Cheesecake:
```
python lpgbt_efuse.py -s chc -l boss -f user_id -u USER_ID_BOSS
python lpgbt_efuse.py -s chc -l sub -f user_id -u USER_ID_SUB
```

Fuse the master/boss lpgbt with Cheesecake from text file produced by lpgbt_config.py:

```
python lpgbt_efuse.py -s chc -l boss -f input_file -i config_boss.txt -v 1 -c 1
```

Fuse the slave/sub lpgbt with Cheesecake from text file produced by lpgbt_config.py:

```
python lpgbt_efuse.py -s chc -l sub -f input_file -i config_sub.txt -c 1
```

## Details of all scripts:

Use -h option for any script to check usage

```lpgbt_action_reset_wd.py```: either reset or disable/enable watchdog for lpGBT

```lpgbt_bert.py```: bit error rate tests for lpGBT (uplink/downlink/loopback)

```lpgbt_bert_fec.py```: bit error rate tests using fec error rate counting 

```lpgbt_config.py```: configure lpGBT

```lpgbt_efuse.py```: fuse registers on lpGBT

```lpgbt_elink_scan.py```: scan VFAT vs elink 

```lpgbt_eye.py```: downlink eye diagram using lpGBT

```lpgbt_eye_equalizer_scan.py```: scan equalizer settings using eye diagram

```lpgbt_eye_plot.py```: plot downlink eye diagram

```lpgbt_led_show.py```: GPIO led show

```lpgbt_phase_scan.py```: phase scan for VFAT elinks and set optimal phase setting

```lpgbt_reset.py```: reset lpGBT

```lpgbt_rssi_monitor.py```: monitor for VTRX+ RSSI value

```lpgbt_rw_register.py```: read/write to any register on lpGBT

```lpgbt_status.py```: check status of lpGBT

```lpgbt_vfat_error_test.py```: error rate tests by read/write on VFAT registers

```lpgbt_vfat_reset.py```: reset VFAT

```lpgbt_vtrx.py```: enable/disable TX channels or registers on VTRX+



