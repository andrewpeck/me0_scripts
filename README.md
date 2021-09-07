## General

Script for configuring lpGBTs on ME0 Optohybrid using either RPi+Cheesecake or Backend

lpGBT naming :

master (ASIAGO schematics) == boss (in software)

slave (ASIAGO schematics) == sub (in software)

## Installation

```
git clone https://github.com/andrewpeck/me0_scripts.git
cd me0_scripts
git checkout cheesecake_integration
```

Install python3

## Powering On

After every power on, lpGBTs on ASIAGO need to be configured.

For unfused ASIAGOs: configure both lpGBTs using RPi-CHeeseCake

For fused ASIAGOs: reconfigure both lpGBTs using Backend or RPi-CHeeseCake


## Using Backend

Login as root

Set some environment variables (after compiling the 0xbefe repo):

```
export ADDRESS_TABLE="<Absolute Path for 0xbefe/address_table/gem/generated/me0_cvp13/gem_amc.xml>"
export ME0_LIBRWREG_SO="<Absolute Path for 0xbefe/scripts/boards/cvp13/rwreg/librwreg.so>"
export BOARD_TYPE="cvp13"
export BOARD_IDX="0"
```

### Configuration

Configure the master/boss lpgbt:

```
python3 lpgbt_config.py -s dryrun -l boss
python3 lpgbt_config.py -s backend -l boss -o <OH_LINK_NR> -g <GBT_LINK_NR> -i config_boss.txt
```

Configure the slave/sub lpgbt:

```
python3 lpgbt_config.py -s dryrun -l sub
python3 lpgbt_config.py -s backend -l sub -o <OH_LINK_NR> -g <GBT_LINK_NR> -i config_sub.txt
```

Enable TX2 for VTRX+ if required:

```
python3 lpgbt_vtrx.py -s backend -l boss -o <OH_LINK_NR> -g <GBT_LINK_NR> -t name -c TX1 TX2 -e 1
```

## Using CHeeseCake

### Configuration

Configure the master/boss lpgbt:

```
python3 lpgbt_config.py -s chc -l boss
```

Configure the slave/sub lpgbt:

```
python3 lpgbt_config.py -s chc -l sub
```

Enable TX2 for VTRX+ if required (usually VTRX+ enabled during configuration):

```
python3 lpgbt_vtrx.py -s chc -l boss -t name -c TX2 -e 1
```

### Checking lpGBT Status

Check the status of the master/boss lpgbt:

```
python3 lpgbt_status.py -s chc -l boss
```

Check the status of the slave/sub lpgbt:

```
python3 lpgbt_status.py -s chc -l sub
```

### Fusing

Obtain the config .txt files first with a dryrun:

```
python3 lpgbt_config.py -s dryrun -l boss
python3 lpgbt_config.py -s dryrun -l sub

```

Fuse the USER IDs with Cheesecake:
```
python3 lpgbt_efuse.py -s chc -l boss -f user_id -u USER_ID_BOSS
python3 lpgbt_efuse.py -s chc -l sub -f user_id -u USER_ID_SUB
```

Fuse the master/boss lpgbt with Cheesecake from text file produced by lpgbt_config.py:

```
python3 lpgbt_efuse.py -s chc -l boss -f input_file -i config_boss.txt -v 1 -c 1
```

Fuse the slave/sub lpgbt with Cheesecake from text file produced by lpgbt_config.py:

```
python3 lpgbt_efuse.py -s chc -l sub -f input_file -i config_sub.txt -c 1
```

## Details of all scripts:

Use -h option for any script to check usage

```get_cal_info_vfat.py```: get calibration data for VFATs

```lpgbt_action_reset_wd.py```: either reset or disable/enable watchdog for lpGBT

```lpgbt_asense_monitor.py```: monitor asense on ME0 GEB

```lpgbt_config.py```: configure or unconfigure lpGBT

```lpgbt_efuse.py```: fuse registers on lpGBT

```lpgbt_eye.py```: downlink eye diagram using lpGBT

```lpgbt_eye_equalizer_scan.py```: scan equalizer settings using eye diagram

```lpgbt_eye_plot.py```: plot downlink eye diagram

```lpgbt_led_show.py```: GPIO led show

```lpgbt_optical_link_bert.py```: bit error ratio tests for optical links (uplink/downlink/loopback) between lpGBT and backend using PRBS

```lpgbt_optical_link_bert_fec.py```: bit error ratio tests for optical links (uplink/downlink) between lpGBT and backend using fec error rate counting 

```lpgbt_init.py```: initialize lpGBT

```lpgbt_rssi_monitor.py```: monitor for VTRX+ RSSI value

```lpgbt_rw_register.py```: read/write to any register on lpGBT

```lpgbt_status.py```: check status of lpGBT

```lpgbt_vfat_analysis_dac.py```: DAC Scan Analysis for VFATs

```lpgbt_vfat_analysis_scurve.py```: SCurve Analysis (fitting) using DAQ data for VFATs

```lpgbt_vfat_analysis_trimming.py```: Analysis for channel trimming for VFATs

```lpgbt_vfat_config.py```: configure VFAT

```lpgbt_vfat_dac_scan.py```: VFAT DAC Scan

```lpgbt_vfat_daq_crosstalk.py```: Scan for checking cross talk using DAQ data for VFATs

```lpgbt_vfat_daq_hitmap.py```: Hit/Noise map using DAQ data for VFATs

```lpgbt_vfat_daq_reg_scan.py```: Scan register values using DAQ data for VFATs

```lpgbt_vfat_daq_scurve.py```: SCurve using DAQ data for VFATs

```lpgbt_vfat_daq_test.py```: bit error ratio tests by reading DAQ data packets from VFATs

```lpgbt_vfat_elink_scan.py```: scan VFAT vs elink 

```lpgbt_vfat_phase_scan.py```: phase scan for VFAT elinks and set optimal phase setting

```lpgbt_vfat_plot_crosstalk.py```: Plotting scan for checking cross talk using DAQ data for VFATs

```lpgbt_vfat_plot_hitmap.py```: Plotting Hit/Noise map using DAQ data for VFATs

```lpgbt_vfat_plot_reg_scan.py```: Register Scan Plotting using DAQ data for VFATs

```lpgbt_vfat_plot_sbit_noise_rate.py```: Noise Rate Plotting using SBits for VFATs

```lpgbt_vfat_plot_scurve.py```: SCurve quick Plotting using DAQ data for VFATs

```lpgbt_vfat_reset.py```: reset VFAT

```lpgbt_vfat_sbit_crosstalk.py```: Scan for checking cross talk using S-bits for VFATs (only works with test firmware)

```lpgbt_vfat_sbit_mapping.py```: S-bit mapping for VFATs (only works with test firmware)

```lpgbt_vfat_sbit_monitor_clustermap.py```: Cluster mapping of channel using S-bit monitor (only works with test firmware)

```lpgbt_vfat_sbit_noise_rate.py```: S-bit Noise rates for VFATs (only works with test firmware)

```lpgbt_vfat_sbit_phase_scan.py```: S-bit phase scan for VFATs (only works with test firmware)

```lpgbt_vfat_sbit_scurve.py```: S-bit SCurve for VFATs (only works with test firmware)

```lpgbt_vfat_sbit_test.py```: S-bit testing for VFATs (only works with test firmware)

```lpgbt_vfat_slow_control_test.py```: error tests by read/write on VFAT registers using slow control

```lpgbt_vfat_slow_control_timing_test.py```: timing tests for read/write on VFAT registers using slow control

```lpgbt_vtrx.py```: enable/disable TX channels or registers on VTRX+

```reg_interface.py```: interactive tool to communicate with lpGBT registers

## Retrieving VFAT Calibrbation Data

To execute the script get_cal_info_vfat.py:
1. Install the `cx_Oracle` `python` module:
   ```
   $ pip3 install cx_Oracle
   ```
   `cx_Oracle` is an API used to interface with Oracle databases.
2. Define the following environment variables in your `.bash_profile`:
```
export GEM_ONLINE_DB_CONN="CMS_GEM_APPUSER_R/GEM_Reader_2015@"
export GEM_ONLINE_DB_NAME="INT2R_LB_LOCAL"
```
and source:
```
source ~/.bash_profile
```
3. Add the script `dbUtilities/tnsnames.ora` to `/etc`. This file specifies the connection information for the Oracle database.
4. Edit the last line of `DBconnect.sh` with your lxplus username.
5. In a separate shell session, open the tunnel to CERN's network with:
```
$ ./dbUtilities/DBconnect.sh .
```
and login using your CERN credentials. (To execute from any directory, place `DBconnectsh` in `/usr/local/bin`.)

6. Update the VFAT text file (example file provided at `vfat_data/ME0_OH0_vfatID.txt`) with your list of 24 plugin cards (for 1 layer) you want to retrieve calibration data for. Use -9999 as serial number for VFATs not connected
 
7. Execute the script:
```
python3 get_cal_info_vfat.py -s backend -o <oh_id> -t <input_type> -w
```
For more information on usage, run `# python3 get_cal_info_vfat.py -h`.

## Procedure for Channel Trimming

1. Run the SCurve script (DAQ or Sbit) wirth 3 different options for "-z": nominal, up, down to take SCurves at 3 different trim values

2. Run the SCurve analysis script to calculate the threshold for each channel for each VFAT

3. Run the trimming analysis script
```
python3 lpgbt_vfat_analysis_trimming.py -nd <nominal SCurve result directory> -ud <Trim up SCurve result directory> -dd <Trim down SCurve result directory>
```

This will generate text files in either directories - `vfat_data/vfat_daq_trimming_results` or `vfat_data/vfat_sbit_trimming_results` depending upon whether DAQ or Sbit SCurves were used

4. The trimming results can be used during VFAT configuration while using any of the scripts by using the additional option `-u daq` or `-u sbit` while running them, with daq or sbit indiciating whether you want to use the trimming results from the DAQ or SBit SCurves
