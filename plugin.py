#!/usr/bin/env python
"""
APC UPS Monitoring
"""
"""
<plugin key="APCUPS" name="APC UPS" version="0.2" author="MadPatrick">
    <params>
        <param field="Address" label="Your APC UPS Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="40px" required="true" default="3551"/>
        <param field="Mode1" label="Reading Interval (sec)" width="40px" required="true" default="10" />
        <param field="Mode2" label="apcaccess path" width="200px" required="true" default="/sbin/apcaccess" />
    </params>
</plugin>
"""

import Domoticz
import subprocess	#For OS calls

# ----------------------------
# Values dictionary
# ----------------------------
values = {
    'STATUS': {'dname': 'Status', 'dunit': 1, 'dtype':243, 'dsubtype':19, 'Used': True},
    'LINEV': {'dname': 'Line Voltage', 'dunit': 2, 'dtype':243, 'dsubtype':8, 'Used': True},
    'LOADPCT': {'dname': 'Load Percentage', 'dunit': 3, 'dtype':243, 'dsubtype':6, 'options':'1;%', 'Used': True},
    'BCHARGE': {'dname': 'Battery Charge', 'dunit': 4, 'dtype':243, 'dsubtype':6, 'options':'1;%', 'Used': True},
    'MODEL': {'dname': 'Model', 'dunit': 5, 'dtype':243, 'dsubtype':19, 'Used': False},
    'SERIALNO': {'dname': 'Serial Number', 'dunit': 6, 'dtype':243, 'dsubtype':19, 'Used': False},
    'BATTV': {'dname': 'Battery Voltage', 'dunit': 7, 'dtype':243, 'dsubtype':8, 'Used': False},
    'NOMBATTV': {'dname': 'Nominal Battery Voltage', 'dunit': 8, 'dtype':243, 'dsubtype':8, 'Used': False},
    'BATTDATE': {'dname': 'Battery Date', 'dunit': 9, 'dtype':243, 'dsubtype':19, 'Used': True},
    'SELFTEST': {'dname': 'Last Self Test', 'dunit': 10, 'dtype':243, 'dsubtype':19, 'Used': True},
    'LASTXFER': {'dname': 'Last Transfer Reason', 'dunit': 11, 'dtype':243, 'dsubtype':19, 'Used': True},
    'NOMPOWER': {'dname': 'Nominal UPS Power', 'dunit': 12, 'dtype':243, 'dsubtype':31, 'options':'1;Watt', 'Used': True},
    'TIMELEFT': {'dname': 'Time Left on Battery', 'dunit': 13, 'dtype':243, 'dsubtype':31, 'options':'1;minutes', 'Used': True},
    'NUMXFERS': {'dname': 'Number of Transfers', 'dunit': 14, 'dtype':243, 'dsubtype':31, 'options':'1;times', 'Used': True},
    'TONBATT': {'dname': 'Time on Battery', 'dunit': 15, 'dtype':243, 'dsubtype':31, 'options':'1;minutes', 'Used': True},
    'CUMONBATT': {'dname': 'Cumulative Time on Battery', 'dunit': 16, 'dtype':243, 'dsubtype':31, 'options':'1;minutes', 'Used': True},

    # Extra velden
    'UPSNAME': {'dname': 'UPS Name', 'dunit': 17, 'dtype':243, 'dsubtype':19, 'Used': False},
    'CABLE': {'dname': 'Cable Type', 'dunit': 18, 'dtype':243, 'dsubtype':19, 'Used': False},
    'FIRMWARE': {'dname': 'Firmware', 'dunit': 19, 'dtype':243, 'dsubtype':19, 'Used': False},
    'UPSMODE': {'dname': 'UPS Mode', 'dunit': 20, 'dtype':243, 'dsubtype':19, 'Used': False},
    'STARTTIME': {'dname': 'UPS Start Time', 'dunit': 21, 'dtype':243, 'dsubtype':19, 'Used': False},
    'MINTIMEL': {'dname': 'Minimum Battery Time', 'dunit': 22, 'dtype':243, 'dsubtype':31, 'options':'1;minutes', 'Used': False},
    'MAXTIME': {'dname': 'Maximum Battery Time', 'dunit': 23, 'dtype':243, 'dsubtype':31, 'options':'1;minutes', 'Used': False},
    'SENSE': {'dname': 'Voltage Sense', 'dunit': 24, 'dtype':243, 'dsubtype':19, 'Used': False},
    'LOTRANS': {'dname': 'Low Transfer Voltage', 'dunit': 25, 'dtype':243, 'dsubtype':8, 'options':'1;V', 'Used': True},
    'HITRANS': {'dname': 'High Transfer Voltage', 'dunit': 26, 'dtype':243, 'dsubtype':8, 'options':'1;V', 'Used': True},
    'NOMINV': {'dname': 'Nominal Input Voltage', 'dunit': 27, 'dtype':243, 'dsubtype':8, 'options':'1;V', 'Used': False},
    # Uitgeschakeld
    #'ALARMDEL': {'dname': 'Alarm Delay', 'dunit': 28, 'dtype':243, 'dsubtype':19, 'Used': False},
    #'XOFFBATT': {'dname': 'Off Battery Count', 'dunit': 29, 'dtype':243, 'dsubtype':19, 'Used': False},
    #'STATFLAG': {'dname': 'Status Flags', 'dunit': 30, 'dtype':243, 'dsubtype':19, 'Used': False},
    #'DRIVER': {'dname': 'Driver Info', 'dunit': 31, 'dtype':243, 'dsubtype':19, 'Used': False},
}

# ----------------------------
# Helper functie om devices bij te werken
# ----------------------------
def UpdateDevice(Unit, nValue, sValue, BatteryLevel=None):
    if Unit in Devices:
        dev = Devices[Unit]
        update_needed = False

        if dev.nValue != nValue:
            update_needed = True
        if dev.sValue != str(sValue):
            update_needed = True
        if BatteryLevel is not None and dev.BatteryLevel != BatteryLevel:
            update_needed = True

        if update_needed:
            kwargs = {"nValue": nValue, "sValue": str(sValue)}
            if BatteryLevel is not None:
                kwargs["BatteryLevel"] = BatteryLevel
            dev.Update(**kwargs)
            Domoticz.Debug(f"Updated device {dev.Name}: nValue={nValue}, sValue={sValue}, BatteryLevel={BatteryLevel}")

# ----------------------------
# onStart functie
# ----------------------------
def onStart():
    Domoticz.Log("Domoticz APC UPS plugin start")

    for key, val in values.items():
        iUnit = val['dunit']
        if iUnit not in Devices:
            try:
                UsedFlag = 1 if val.get('Used', True) else 0
                Domoticz.Device(
                    Name=val['dname'],
                    Unit=iUnit,
                    Type=val['dtype'],
                    Subtype=val['dsubtype'],
                    Used=UsedFlag,
                    Options=val.get('options')
                ).Create()
            except Exception as e:
                Domoticz.Error(f"Failed to create device {val['dname']}: {e}")

    Domoticz.Heartbeat(int(Parameters["Mode1"]))

# ----------------------------
# onHeartbeat functie
# ----------------------------
def onHeartbeat():
    try:
        res = subprocess.check_output(
            [Parameters["Mode2"], '-u', '-h', f"{Parameters['Address']}:{Parameters['Port']}"],
            text=True
        )

        battery_values = {}
        for line in res.strip().split('\n'):
            key, _, val = line.partition(': ')
            key = key.strip()
            val = val.strip()

            if val in ('', 'N/A', 'None'):
                battery_values[key] = ''
                continue

            try:
                battery_values[key] = float(val)
            except ValueError:
                battery_values[key] = val

        batterylevel = int(battery_values.get('BCHARGE', -1)) if 'BCHARGE' in battery_values and battery_values['BCHARGE'] != '' else -1

        for key, val in battery_values.items():
            if key in values:
                iUnit = values[key]['dunit']
                sValue = str(val) if val != '' else ''
                nValue = 0
                if batterylevel >= 0:
                    UpdateDevice(iUnit, nValue, sValue, BatteryLevel=batterylevel)
                else:
                    UpdateDevice(iUnit, nValue, sValue)

    except Exception as err:
        Domoticz.Error("APC UPS Error: " + str(err))