#!/usr/bin/env python
# -*- coding: utf-8 -*-

PORT = '/dev/ttyUSB0'

import pygtk
pygtk.require('2.0')
import gtk

import os,os.path
import string
import time
import sys
sys.path.append('../kkmdrv')
import kkmdrv
import serial

kkmdrv.DEBUG = False
kkmdrv.TODO = False
       
if __name__ == "__main__":
	message = gtk.MessageDialog(flags=gtk.DIALOG_MODAL,type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO)
	message.set_markup("Продолжить печать?")
	result = message.run()
	message.destroy()
	if result == gtk.RESPONSE_YES:
		try:
			ser = serial.Serial(PORT, 19200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.7, writeTimeout=0.7)
		except:
			ser = False
			error = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
			error.set_markup("Не могу подключиться к кассе.")
			error.run()
			error.destroy()
		finally:
			if ser:
				kkm = kkmdrv.KKM(ser,kkmdrv.DEFAULT_PASSWORD)
				kkm.continuePrint()
				ser.close()	
		
		

