#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
Shtrikh FR-K GUI
=================================================================
Copyright (C) 2010  Dmitry Shamov demmsnt@gmail.com

    You can choose between two licenses when using this package:
    1) GNU GPLv2
    2) PSF license for Python 2.2

    Shtrikh KKM page: http://www.shtrih-m.ru/
        Project page: http://sourceforge.net/projects/pyshtrih/

"""
PORT = '/dev/ttyUSB0'
DUMMY=True # Отладочный режим при котором используется класс пустышка
#'COM1'
LOGFILE = 'kkmgui.log'
CLIENTS_FILE = './clients.txt'
OPERATOR_FILE= './operator.txt'
MAX_SUMM = 100000.00 # maximum cash operation limit

import gtk,gobject
import os,os.path
import string
import time
import sys
sys.path.append('../kkmdrv')
import kkmdrv
import serial

class EntryDescriptor(object):
    def __init__(self, object_name):
        self.object_name = object_name
    def __get__(self, obj, cls):
        return obj.get_object(self.object_name).get_text()
    def __set__(self, obj, value):
        obj.get_object(self.object_name).set_text(value)

class serialLogWrapper(object):
        def __init__(self,ser,fn):
                self.ser = ser
                self.fn = fn
                self.f = open(self.fn,"a")

        def getlogstring(self,func, args,results):
                return time.strftime("%d.%m.%Y %H:%M:%S") + " "+func+"\t"+kkmdrv.hexStr(str(args))+"  result "+kkmdrv.hexStr(str(args))

        def write(self,*args):
                result = apply(self.ser.write,args)
                #print >>,self.fn,self.getlogstring('write',args,result)
                return result
        def read(self,*args):
                result = apply(self.ser.read,args)
                #print >>,self.fn,self.getlogstring('read',args,result)
                return result
        def close(self,*args):
                result = apply(self.ser.close,args)
                #print >>,self.fn,self.getlogstring('close',args,result)
                return result

        def isOpen(self,*args):
                result = apply(self.ser.isOpen,args)
                #print >>,self.fn,self.getlogstring('isOpen',args,result)
                return result

        def flush(self,*args):
                result = apply(self.ser.close,args)
                #print >>,self.fn,self.getlogstring('flush',args,result)
                return result

class KkmGUI(gtk.Builder):
    def __init__(self):
        """Инициализация"""
        super(KkmGUI, self).__init__()
        self.logfile = open(LOGFILE,'a')
        self.add_from_file(os.path.join(os.path.dirname(__file__),'kkmgui.ui'))
        #Создаем кассовый аппарат
        if DUMMY:
                self.ser = None
        else:
                self.ser = serial.Serial(PORT, 115200,\
                            parity=serial.PARITY_NONE,\
                            stopbits=serial.STOPBITS_ONE,\
                            timeout=0.7,\
                            writeTimeout=0.7)
        if DUMMY:
             self.kkm = kkmdrv.ShtrihFRKDummy(kkmdrv.DEFAULT_PASSWORD,kkmdrv.DEFAULT_ADM_PASSWORD,self.ser)
        else:
             self.kkm = kkmdrv.ShtrihFRK(kkmdrv.DEFAULT_PASSWORD,kkmdrv.DEFAULT_ADM_PASSWORD,self.ser)
        #Типы
        liststore = gtk.ListStore(gobject.TYPE_STRING)
        liststore.append(["Продажа"])
        liststore.append(["Возврат"])
        self.type_combo.set_model(liststore)
        cell = gtk.CellRendererText()
        self.type_combo.pack_start(cell, True)
        self.type_combo.add_attribute(cell, 'text',0)
        self.type_combo.set_active(0)
        #
        self.nds_spin.set_value(18)
        # подключаем обработчики сигналов, описанные в demo.ui к объекту self
        self.connect_signals(self)
        #Читаем список клиентов из clients.txt
        if os.path.exists(CLIENTS_FILE):
                self.clients=map(lambda x: x.replace('\n',''), open(CLIENTS_FILE,'r').readlines())
        else:
                self.clients = []
        if os.path.exists(OPERATOR_FILE):
                self.operator=open(OPERATOR_FILE,'r').readline()
                self.operator_entry.set_text(self.operator)
        else:
                self.operator = ''
        self.setupCompletition()
        self.kkmGUI.show_all()
        self.log("Программа запущена")
        self.checkStatus()

    def checkStatus(self):
        """Check kkm status"""
        self.log(self.kkm.getStatusString())

    def log(self,*s):
            """Write log"""
            text = time.strftime("%d.%m.%Y %H:%M:%S")+'\t'+string.join(map(lambda x: str(x), s ),' ')
            self.logfile.write(text+'\n')
            self.logfile.flush()
            iter = self.logtext.get_end_iter()
            self.logtext.insert(iter, text+'\n')
            #Итератор стал невалидным так, как буффер поменялся
            iter = self.logtext.get_end_iter()
            self.log_text.forward_display_line(iter)

    def errorMsg(self,text):
                """show error message dialog"""
                self.log("ОШИБКА:",text)
                md = gtk.MessageDialog(self.kkmGUI,\
                                       gtk.DIALOG_DESTROY_WITH_PARENT,\
                                       gtk.MESSAGE_ERROR,\
                                       gtk.BUTTONS_CLOSE,\
                                       text)
                md.run()
                md.destroy()

    def setupCompletition(self):
        """Установка автодополнения"""
        COL_TEXT = 0
        def match_func(completion, key, iter):
                model = completion.get_model()
                if model[iter][COL_TEXT]:
                        return model[iter][COL_TEXT].startswith(self.client_entry.get_text())
        def on_completion_match(completion, model, iter):
                self.client_entry.set_text(model[iter][COL_TEXT])
                self.client_entry.set_position(-1)
        completion = gtk.EntryCompletion()
        completion.set_match_func(match_func)
        completion.connect("match-selected", on_completion_match)
        completion.set_model(gtk.ListStore(str))
        completion.set_text_column(COL_TEXT)
        self.client_entry.set_completion(completion)
        model = completion.get_model()
        for c in self.clients:
                model.append([c])

    def __getattr__(self, attr):
        # удобней писать self.window1, чем self.get_object('window1')
        obj = self.get_object(attr)
        if not obj:
            raise AttributeError('object %r has no attribute %r' % (self,attr))
        setattr(self, attr, obj)
        return obj

    # питоновский дескриптор, который позволяет нам гораздо удобнее работать со значениями в gtk.Entry
#    expr = EntryDescriptor('entry1')
    def print_check(self,widget):
        """Напечатать чек"""
        def get_summ():
    		result=self.summ_entry.get_value()
    		if type(result)==type(str) or type(result)==type(unicode):
    		    return float(self.summ_entry.get_value().replace(',','.'))
    		else:
    		    return result
        self.operator = self.operator_entry.get_text()
        client_name = self.client_entry.get_text()
        #print "Нажали печать чека",client_name
        if self.client_entry.get_text() not in self.clients:
                self.clients.append(client_name)
                model = self.client_entry.get_completion().get_model()
                model.append([client_name])
        #Напечатаем его
        if self.nds_check.get_active():
                nds = self.nds_spin.get_value()
        else:
                nds=0
        if self.type_combo.get_active()==0:
                ct = 0
        else:
                ct=1
        if  get_summ() > MAX_SUMM:
                self.log("Нельзя печатать чеки на сумму больше %0.2f"  % MAX_SUMM)
                return False
        if  len(self.comment_entry.get_text())>40 or len( self.client_entry.get_text() ):
                self.log("Комментарий к чеку или наименование клиента не должны привышать 40 символов")
                return False
        

        self.log("Печатаю чек",self.summ_entry.get_value(),\
                            self.comment_entry.get_text(),\
                            self.client_entry.get_text(),\
                            ct,\
                            nds)
        try:
                self.kkm.printCheck("Кассир:"+self.operator,\
                            get_summ(),\
                            self.comment_entry.get_text(),\
                            self.client_entry.get_text(),\
                            ctype=ct,\
                            nds=nds)
        except kkmdrv.kkmException,e:
                self.errorMsg("Произошла ошибка\n"+str(e));
        else:
                self.log("Чек напечатан")
        self.checkStatus()

    def reportWClose(self,widget):
            """Отчет с гашением"""
            self.log("Отчет с гашением")
            try:
                self.kkm.closeSession(password=kkmdrv.DEFAULT_ADM_PASSWORD)
            except kkmdrv.kkmException,e:
                self.errorMsg("Произошла ошибка\n"+str(e));
            else:
                self.log("Отчет с гашением напечатан")
            self.checkStatus()

    def reportWoClose(self,widget):
            """Отчет без гашения"""
            self.log("Отчет без гашения")
            try:
                self.kkm.printReport(password=kkmdrv.DEFAULT_ADM_PASSWORD)
            except kkmdrv.kkmException,e:
                self.errorMsg("Произошла ошибка\n"+str(e));
            else:
                self.log("Отчет без гашения напечатан")
            self.checkStatus()

    def cancelCheck(self,widget):
            """Отменить печать чека"""
            self.log("Отмена чека")
            try:
                self.kkm.cancelCheck()
            except kkmdrv.kkmException,e:
                self.errorMsg("Произошла ошибка\n"+str(e));
            else:
                self.log("Чек отменен")
            self.checkStatus()

    def cutCheck(self,widget):
            """Обрезать чек"""
            self.log("Обрезка чека")
            try:
                self.kkm.cutRibbon()
            except kkmdrv.kkmException,e:
                self.errorMsg("Произошла ошибка\n"+str(e));
            else:
                self.log("Чек отбрезан")
            self.checkStatus()


    def continuePrint(self,widget):
            """Продолжить печать"""
            self.log("Продолжить печать чека")
            try:
                    self.kkm.continuePrint()
            except:
                self.errorMsg("Произошла ошибка\n"+str(e));
            else:
                self.log("Чек напечатан")
            self.checkStatus()

    def setDateTime(self,widget):
            """Установить дату и время"""
            self.log("Установить время/дату")
            try:
                self.kkm.setupDateTime(kkmdrv.DEFAULT_ADM_PASSWORD)
            except kkmdrv.kkmException,e:
                self.errorMsg("Произошла ошибка\n"+str(e));
            else:
                self.log("Время/Дата установлены")
            self.checkStatus()

    def getText(self,header,label_text,prompt):
        """Get text from Entry dialog"""
        def responseToDialog(entry, dialog, response):
                dialog.response(response)

        #base this on a message dialog
        dialog = gtk.MessageDialog(
                None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_QUESTION,
                gtk.BUTTONS_OK,
                None)
        dialog.set_markup(header)#'Please enter your <b>name</b>:')
        #create the text input field
        entry = gtk.Entry()
        #allow the user to press enter to do ok
        entry.connect("activate", responseToDialog, dialog, gtk.RESPONSE_OK)
        #create a horizontal box to pack the entry and a label
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(label_text), False, 5, 5)
        hbox.pack_end(entry)
        #some secondary text
        dialog.format_secondary_markup(prompt)
        #add it and show it
        dialog.vbox.pack_end(hbox, True, True, 0)
        dialog.show_all()
        #go go go
        dialog.run()
        text = entry.get_text()
        dialog.destroy()
        return text

    def cashInput(self,widget):
            """Внесение денег"""
            cash = float(self.getText('Внесение денег','Сумма:','Введите сумму которую вносите в кассу (0 для отмены)'))
            if abs(0-cash)>0.001: # не 0
                    self.log("Внесение %.2f" % cash)
                    try:
                        self.kkm.inputMoney(cash)
                    except kkmdrv.kkmException,e:
                        self.errorMsg("Произошла ошибка\n"+str(e));
                    else:
                        self.log("Внесение проведено")
            self.checkStatus()

    def cashOutput(self,widget):
            """Внесение денег"""
            cash = float(self.getText('Инкассация','Сумма:','Введите сумму на которую производится инкассация (0 для отмены)'))
            if abs(0-cash)>0.001: # не 0
                    self.log("Инкассация %.2f" % cash)
                    try:
                        self.kkm.outputMoney(cash)
                    except kkmdrv.kkmException,e:
                        self.errorMsg("Произошла ошибка\n"+str(e));
                    else:
                        self.log("Инкассация проведена")
            self.checkStatus()


    def ndsToggle(self,widget):
        """Включить, выключить НДС"""
        #print widget.get_active()
        self.nds_spin.set_sensitive(widget.get_active())


    def quit(self, widget):
        #Сохраним clients.txt
        f = open(CLIENTS_FILE,'w').write(string.join(self.clients,'\n'))
        f = open(OPERATOR_FILE,'w').write(self.operator_entry.get_text())
        self.checkStatus()
        if self.ser:
           self.ser.close()
        self.log('Программа нормально завершена')
        self.logfile.close()
        gtk.main_quit()


if __name__ == '__main__':
    kkmGUI = KkmGUI()
    gtk.main()
