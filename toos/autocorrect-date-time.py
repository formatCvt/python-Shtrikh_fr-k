#!/usr/bin/env python

import ConfigParser
import time
import sys
sys.path.append('../kkmdrv')
import kkmdrv
import serial
import smtplib
# Import the email modules we'll need
from email.mime.text import MIMEText

CONFIG_FILE = 'autocorrect-date.conf'

# Parse config
config = ConfigParser.RawConfigParser()
config.read(CONFIG_FILE)
try:
    PORT = config.get('settings', 'port')
    msgFROM = config.get('settings', 'from')
    msgTO = config.get('settings', 'to')
except:
    print 'Config not found (%s) or wrong config data.' % (CONFIG_FILE)
    sys.exit(1)
finally:
    # Hardcoded settings
    kkmdrv.DEBUG = False
    kkmdrv.TODO = False

    # Connect to KKM
    try:
        ser = serial.Serial(PORT, 19200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.7, writeTimeout=0.7)
    except:
        ser = False
    finally:
        if ser:
            kkm = kkmdrv.KKM(ser,kkmdrv.DEFAULT_PASSWORD)
            t=time.localtime()
            kkmStatus = kkm.statusRequest()
            kkmTime = kkmStatus['time'].split(":")
            if int(kkmStatus['mode']) == 4 and (int(kkmTime[0]) != t.tm_hour or int(kkmTime[1]) != t.tm_min):
                kkm.setDate(kkmdrv.DEFAULT_ADM_PASSWORD, t.tm_mday, t.tm_mon, t.tm_year)
                kkm.acceptSetDate(kkmdrv.DEFAULT_ADM_PASSWORD, t.tm_mday, t.tm_mon, t.tm_year)
                t = time.localtime()
                kkm.setTime(kkmdrv.DEFAULT_ADM_PASSWORD, t.tm_hour, t.tm_min, t.tm_sec)
                kkmNewStatus = kkm.statusRequest()
                print "Time updated!\nOld value: %s %s\nNew value: %s %s" % (kkmStatus['date'], kkmStatus['time'], kkmNewStatus['date'], kkmNewStatus['time'])
                msg = MIMEText("Time updated!\nOld value: %s %s\nNew value: %s %s" % (kkmStatus['date'], kkmStatus['time'], kkmNewStatus['date'], kkmNewStatus['time']))
                msg['Subject'] = 'KKM date/time updated'
                msg['From'] = msgFROM
                msg['To'] = msgTO
                s = smtplib.SMTP('localhost')
                s.sendmail(msgFROM, msg['To'].split(","), msg.as_string())
                s.quit()
            ser.close()