import sys
import os
import re
import subprocess as sb
from pprint import pprint
from PySide import QtCore 
from PySide import QtGui 


def getCustomUIActions():
     
    action1 = {}
    action1["name"] = "lustre_launch"
    action1["caption"] = "Lustre Premium 2017"
    
    action2 = {}
    action2["name"] = "Metadata"
    action2["caption"] = "Display clip metadata"

    appGroup = {}
    appGroup["name"] = "Extra Options"
    appGroup["actions"] = (action1, action2)
    return (appGroup,)

def customUIAction( info, userData ):
    # Option selection check
    if info['name'] == 'lustre_launch':
        os.system('/opt/Autodesk/lustrepremium_2017.1.pr71/lustrepremium &')
    if info['name'] == 'Metadata':
        class Ui_Form(object):
            def setupUi(self, Form):
                Form.setObjectName("Form")
                Form.resize(950, 495)
                self.verticalLayout_4 = QtGui.QVBoxLayout(Form)
                self.verticalLayout_4.setObjectName("verticalLayout_4")
                self.horizontalLayout_2 = QtGui.QHBoxLayout()
                self.horizontalLayout_2.setContentsMargins(-1, -1, -1, 0)
                self.horizontalLayout_2.setObjectName("horizontalLayout_2")
                self.pushButton = QtGui.QPushButton(Form)
                self.pushButton.setObjectName("pushButton")
                self.horizontalLayout_2.addWidget(self.pushButton)
                self.pushButton_2 = QtGui.QPushButton(Form)
                self.pushButton_2.setObjectName("pushButton_2")
                self.horizontalLayout_2.addWidget(self.pushButton_2)
                self.pushButton_3 = QtGui.QPushButton(Form)
                self.pushButton_3.setObjectName("pushButton_3")
                self.horizontalLayout_2.addWidget(self.pushButton_3)
                self.verticalLayout_4.addLayout(self.horizontalLayout_2)
                self.verticalLayout_5 = QtGui.QVBoxLayout()
                self.verticalLayout_5.setObjectName("verticalLayout_5")
                self.textEdit = QtGui.QTextEdit(Form)
                self.textEdit.setObjectName("textEdit")
                self.verticalLayout_5.addWidget(self.textEdit)
                self.verticalLayout_4.addLayout(self.verticalLayout_5)
                self.textEdit.setReadOnly(True)

                self.retranslateUi(Form)
                QtCore.QMetaObject.connectSlotsByName(Form)

                ## Button actions 

                def frameSource():
                    cmdB1 = '/usr/discreet/wiretap/tools/current/wiretap_get_frames', '-p', '-n', nodeID
                    clip_SOURCE, err = sb.Popen(cmdB1, stdout=sb.PIPE).communicate()
                    self.textEdit.setText(clip_SOURCE)

                def frameXML():
                    cmdB2 = '/usr/discreet/wiretap/tools/current/wiretap_get_metadata', '-n', nodeID, '-s', 'XML'
                    clip_XML, err = sb.Popen(cmdB2, stdout=sb.PIPE).communicate()
                    self.textEdit.setText(clip_XML)
                
                def frameEDL():
                    cmdB3 = '/usr/discreet/wiretap/tools/current/wiretap_get_metadata', '-n', nodeID, '-s', 'EDL'
                    clip_EDL, err = sb.Popen(cmdB3, stdout=sb.PIPE).communicate()
                    self.textEdit.setText(clip_EDL)
                
                ## Connect 

                QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL('clicked()'), frameSource)
                QtCore.QObject.connect(self.pushButton_2, QtCore.SIGNAL('clicked()'), frameXML)
                QtCore.QObject.connect(self.pushButton_3, QtCore.SIGNAL('clicked()'), frameEDL)


            def retranslateUi(self, Form):
                Form.setWindowTitle(QtGui.QApplication.translate("Form", "Clip Info", None, QtGui.QApplication.UnicodeUTF8))
                self.pushButton.setText(QtGui.QApplication.translate("Form", "Source Path", None, QtGui.QApplication.UnicodeUTF8))
                self.pushButton_2.setText(QtGui.QApplication.translate("Form", "XML - Metadata", None, QtGui.QApplication.UnicodeUTF8))
                self.pushButton_3.setText(QtGui.QApplication.translate("Form", "EDL - Metadata", None, QtGui.QApplication.UnicodeUTF8))

        #app = QtGui.QApplication.instance()
        app = QtGui.QApplication.activePopupWidget()
        Form = QtGui.QWidget()
        ui = Ui_Form()
        ui.setupUi(Form)
        Form.show()
        nodeID = info['selection'][0]
        app.exec_()        


