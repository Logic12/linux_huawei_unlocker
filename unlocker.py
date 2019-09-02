#!/usr/bin/env python3  
#
# unlocker.py
# - Remove simlock on huawei modems
#
# Copyright (C) 2013 Neil McPhail
#        neil@mcphail.homedns.org
#
# Unlock code generator Copyright (C) 2010 dogbert
#                                     dogber1@gmail.com

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import sys, time, serial, re, hashlib, glob, urllib.request, urllib.error, urllib.parse, collections

debugMode = True

class menuClass:
    status = 1
    command = {}
    setupDictonary={
        "lock status":{
            '0':'???',
            '1':'soft locked',
            '2':'unlocked to the inserted sim',
            '3':'hard locked'
        }
    }
    setup={
        'hilink ip':"192.168.8.1",
        'IMEI':"?",
        'serial port':"?",
        'lock status':"?",
        'lock try remaining':"?",
        'mobile carrier':"?",
        'unlock code':"?"
    }
    def switchToStickMode(self):
        response = urllib.request.urlopen('http://' + self.setup['hilink ip'] + '/html/switchProjectMode.html')
        html = response.read()
        response.close()  
    def details(self):
        print(80 * "-")
        for key in self.setup:
            try:
                print(key + " : " + self.setupDictonary[key][str(self.setup[key])])
            except:
                print(key + " : " + str(self.setup[key]))
        print(80 * "-")
    def detailsMenu(self):
        self.details()
        self.title('change')
        self.menuPoint({
            '1':"serial port",
            '2':"IMEI",
            '3':"unlock code",
            '4':"hilink ip",
            'a':"advanced ,menu",
            'm':"main menu",
        })
        self.command={
            '1':self.changeSerialPort,
            '2':self.changeIMEI,
            '3':self.changeUnlockCode,
            '4':self.changeHilinkIp,

        }
    def changeSerialPort(self):
        self.setup['serial port'] = self.input('serial port')
    def changeIMEI(self):
        self.setup['IMEI'] = self.input('IMEI')
    def changeUnlockCode(self):
        self.setup['unlock code'] = self.input('unlock code')
    def changeHilinkIp(self):
        self.setup['hilink ip'] = self.input('hilink ip')
    def input(self, text):
        return  input(text + " = ")
    def run(self):
        self.command['d'] = self.toDetailsMenu
        self.command['a'] = self.toAdvanced
        self.command['m'] = self.toMain
        self.command['e'] = self.toExit
        response = input(">> ")
        return  self.command[response]()
        try :
            return  self.command[response]()
        except:
             print("command '"+response+"' not found")
             return False
        return True
    def checkPorts(self):
        ports = glob.glob('/dev/ttyUSB*')
        result = {}
        resultDict = ['not active', 'active', 'error']
        for p in ports:
            try:
               print("test port : " + p)
               modem = modemClass(str(p))
               result[p] = modem.test()
               del modem
            except:
               result[p] = 2
               del modem
        for p in result:
            if result[p] == 1:
               self.setup['serial port']=p;
            print(p + " : "+ resultDict[result[p]])
    def unlock(self):
        modem = modemClass(self.setup['serial port'])
        modem.unlock(self.setup['unlock code'])
        del modem
    def getIMEI(self):
        modem = modemClass(self.setup['serial port'])
        self.setup['IMEI']=modem.getIMEI()
        del modem
    def getLockStatus(self):
        modem = modemClass(self.setup['serial port'])
        lockInfo=modem.getLock()
        del modem
        if not lockInfo == False:
            self.setup['lock try remaining'] = lockInfo['remaining']
            self.setup['mobile carrier']     = lockInfo['carrier']
            self.setup['lock status']        = lockInfo['lockStatus']
    def getUnlockCode(self):
        self.setup['unlock code']= computeUnlockCode(self.setup['IMEI'])
    def title(self, text):
        print(80*"=")
        print("Huawei unlocker "+text) 
        print(80*"=")
    def menuPoint (self, menu):
        for key in sorted(menu.keys()):
            print("\t " + key + ". " + menu[key])
        print("\t e. Exit")
    def menu(self):
        self.title("main menu")
        self.menuPoint(collections.OrderedDict({
            '1':"Basic (legacy)",
            '2':"Advanced"
        }))
        self.command={
            '1':auto,
            '2':self.toAdvanced
        }
    def advanced(self):
        self.details()
        self.title("advanced menu")
        self.menuPoint(collections.OrderedDict({
            '1':"detect port",
            '2':"detect imei",
            '3':"detect lock status",
            '4':"calculate unlock code",
            '5':"switch to stick mode",
            'd':"details menu",
            'm':"bact to main menu"
        }))
        self.command={
            '1':self.checkPorts,
            '2':self.getIMEI,
            '3':self.getLockStatus,
            '4':self.getUnlockCode,
            '5':self.switchToStickMode
        }
    def toDetailsMenu(self):
        self.status = 3
    def toAdvanced(self):
        self.status = 2
    def toExit(self):
        self.status = 0
    def toMain(self):
        self.status = 1
    def circle(self):
        while 1:
            if self.status == 1:
                self.menu()
            elif self.status == 2:
                self.advanced()
            elif self.status == 3:
                self.detailsMenu()
            else:
               break 
            self.run()
        print("bye bye")
        exit(0)

class argvClass:
    setup={'question':1,'menu':0}
    def __init__(self):
        for ar in sys.argv:
            if ar =='-n':
                self.setup['question']=0
            if ar =='-m':
                self.setup['menu']=1

class modemClass:
    connection = ""
    connected = False
    port = ""
    lastRead = ""
    def connect(self):
        if self.connected:
            self.disconnect()
        print('connetcting to ' + self.port + ' .. ', end='' )
        try:
            self.connection = serial.Serial(port = self.port,
                timeout = 15, xonxoff=False, rtscts=True, dsrdtr=True)
            self.connected = True
            print(' ok')
            return True
        except:
            print(' failed')
            return False
    def disconnect(self):
        print('disconnetcting  ... ', end='' )
        try:
            self.connection.close()
            print(' ok')
            return True
        except:
            print(' failed')
            return False
    def flush(self):
        self.lastRead = ""
        self.debug("flush")
        self.connection.flushInput()
    def write(self,string ):
        self.flush()
        self.debug("write - " + str(string)) 
        self.connection.write(string.encode())
    def read(self,byts):
        self.lastRead =  self.connection.read(byts).decode('utf8')
        self.debug("read - " + self.lastRead)
        return self.lastRead
    def search(self, write, expectation,byts):
        self.connect()
        self.write(write)
        self.read(byts)
        self.disconnect
        return re.search(expectation, self.lastRead)
    def test(self):
        self.connect()
        self.write('AT\r\n')
        self.lastRead =  self.connection.read(4).decode('utf8')
        if self.lastRead == '':
            return 0
        return 1
    def getIMEI(self):
        match = self.search('AT+CGSN\r\n','\\r\\n(\d{15})\\r\\n', 32)
        if match:
            print("Found IMEI: " + match.group(1))
            return match.group(1)
        else:
             print("IMEI not found")
        return '?'
    def getLock(self):
        match = self.search('AT^CARDLOCK?\r\n', 'CARDLOCK: (\d),(\d\d?),(\d+)\r',32)
        status = {
            'lockStatus' : "?",
            'remaning'   : "?",
            'carrier'    : "?"
        }
        if match:
            status['lockStatus'] = int(match.group(1)) 
            status['remaining'] = int(match.group(2))
            status['carrier'] = int(match.group(3))
        else:
            return False
        return status
    def unLock(self, unlockCode):
        self.write('AT^CARDLOCK="'+ str(unlockCode) + '"\r\n')
        self.read(64)
    def generateUnlockCodeV1(self):
        salt = '5e8dd316726b0335'
        digest = hashlib.md5((imei+salt).lower().encode('latin1')).digest().decode('latin1')
        print(digest)
        code = 0
        for i in range(0,4):
            code += (ord(digest[i])^ord(digest[4+i])^ord(digest[8+i])^ord(digest[12+i])) << (3-i)*8
        code &= 0x1ffffff
        code |= 0x2000000
        return code
    def debug(self, text):
        if debugMode:
            print("modem debug : " + text)
    def __init__(self, port):
        print(80*"#")
        self.port = port
    def __del__(self):
        if self.connected:
            self.disconnect()
        print(80*"#")


# Intro
def intro():
    print(80 * "*")
    print("\tHuawei modem unlocker")
    print("\tBy Neil McPhail and dogbert")
    print("\tThis is Free Software as defined by the GNU GENERAL PUBLIC")
    print("\tLICENSE version 2")
    print(80 * "*")
    print("\tThis software comes with NO WARRANTY")
    print("\tThis software can damage your hardware")
    print("\tUse it at your own risk")
    print(80 * "*")
    print("\tNot all modems can be unlocked with this software.")
    print("\tUsers have reported problems with the following devices:")
    print("\t\tE220, E353")
    print("\tAttempting to unlock these devices with this software is not")
    print("\trecommended. I hope to fix this in a later release.")
    print(80 * "*")
    if not _requireYes():
        print("Bye")
        exit(0)

# Helper function
# Require an explicit "YES" in upper case
# Returns True if "YES"
# Asks for explicit uppercase "YES" if mixed or lower case used
# Returns False for anything else
def _requireYes():
    print("If you wish to proceed, please type YES at the prompt")
    while 1:
        response = input(">> ")
        if response == "YES":
            return True
        if response.upper() == "YES":
            print("You must type YES in upper case to proceed")
            continue
        else:
            return False


# These modems seem to open 3 USB serial ports. Only one is the control port
# and this seems to vary from device to device. The other 2 ports appear to
# remain silent
def identifyPort():
    print("Trying to find which port is the active modem connection.")
    print("Please be patient as this can take a while.\n\n")
    for p in glob.glob('/dev/ttyUSB*'):
        print("Testing port " + p)
        ser = serial.Serial(port = p,
            timeout = 15, xonxoff=False, rtscts=True, dsrdtr=True)
        ser.write(b'AT\r\n')
        activity = ser.read(5)
        if activity == '':
            print("\tNo activity\n")
            ser.close()
            continue
        print("\tActivity detected\n")
        ser.close()
        return p
    return ''

# The modem should respond with the IMEI with the AT+CGSN command
def obtainImei(port):
    print("\nTrying to obtain IMEI.")
    print("The modem will be given 5 seconds to respond.")
    ser = serial.Serial(port = port,
        timeout = 15, xonxoff=False, rtscts=True, dsrdtr=True)
    ser.flushInput()
    ser.write(b'AT+CGSN\r\n')
    time.sleep(5)
    response = ser.read(4096)
    ser.close()
    match = re.search('\\r\\n(\d{15})\\r\\n', response.decode('utf8'))
    if match:
        print("Found probable IMEI: " + match.group(1))
        return match.group(1)
    else:
        print("IMEI not found")
        return ''

# Check the IMEI is correct
# Adapted from dogbert's original
def testImeiChecksum(imei):
    digits = []
    for i in imei:
        digits.append(int(i))
    _sum = 0
    alt = False
    for d in reversed(digits):
        assert 0 <= d <= 9
        if alt:
            d *= 2
        if d > 9:
            d -= 9
        _sum += d
        alt = not alt
    return (_sum % 10) == 0

# Display a warning if first digit of IMEI indicates a potentially troublesome
# modem
def checkImeiCompatibility(imei):
    if ('8' == imei[0]):
        print(80 * "*")
        print("\n\tWarning")
        print("\n\tYour modem's IMEI begins with '8'")
        print("\tIt is likely to be incompatible with this script")
        print("\tProceed at your own risk")
        print("\n\tPlease provide feedback: see README and HELPME\n")
        print(80 * "*")

# Interrogate the lock status
# Returns a dictionary with the lock status, remaining unlock attempts
# and the - largely unused - carrier code
#
# lockStatus 0 = unobtainable
#            1 = locked but can be unlocked
#            2 = unlocked to the inserted sim
#            3 = locked and cannot be unlocked
def checkLockStatus(port):
    status = {'lockStatus': "?", 'remaining': "?", 'carrier': "?"}
    print("\nChecking the lock status of the SIM.")
    print("The modem will be given 5 seconds to respond.")
    ser = serial.Serial(port = port,
        timeout = 15, xonxoff=False, rtscts=True, dsrdtr=True)
    ser.flushInput()
    ser.write(b'AT^CARDLOCK?\r\n')
    time.sleep(5)
    response = ser.read(4096)
    ser.close()
    match = re.search('CARDLOCK: (\d),(\d\d?),(\d+)\r', response.decode('utf8'))
    if match:
        status['lockStatus'] = int(match.group(1))
        status['remaining'] = int(match.group(2))
        status['carrier'] = int(match.group(3))
    else:
        return False
    return status

# Compute the unlock code
# Adapted from dogbert's original
def computeUnlockCode(imei):
    salt = '5e8dd316726b0335'
    digest = hashlib.md5((imei+salt).lower().encode('latin1')).digest().decode('latin1')
    print(digest)
    code = 0
    for i in range(0,4):
        code += (ord(digest[i])^ord(digest[4+i])^ord(digest[8+i])^ord(digest[12+i])) << (3-i)*8
    code &= 0x1ffffff
    code |= 0x2000000
    return code


# Send AT codes to unlock the modem
def unlockModem(port, lockCode):
    ser = serial.Serial(port = port, rtscts = True, dsrdtr = True)
    command = 'AT^CARDLOCK="'+ str(lockCode) + '"\r\n'
    ser.write(command)
    ser.close()

def auto():
    # Work out which is the control port
    try:
        activePort = identifyPort()
    except:
        print("\nAn error occurred when probing for active ports.")
        print("This may be because you need to run this program as root.")
        exit(1)
    else:
        if (activePort==''):
            print("\nCould not identify active port.")
            exit(1)

    # Obtain and check IMEI
    try:
        imei = obtainImei(activePort)
    except:
        print("\nAn error occurred when trying to check the IMEI.")
        exit(1)
    else:
        if (imei==''):
            print("\nCould not obtain IMEI.")
            print("Check the modem is properly inserted")
            print("Check a SIM card is in place")
            print("Check you are not already connected")
            print("Try removing and reinserting the device")
            exit(1)
        else:
            if not testImeiChecksum(imei):
                print("\nIMEI checksum invalid.")
                exit(1)
            else:
                print("IMEI checksum OK.")
                checkImeiCompatibility(imei)

    # Obtain lockstatus
    try:
        lockInfo = checkLockStatus(activePort)
    except:
        print("\nAn error occurred when trying to check the SIM lock.")
        exit(1)
    else:
        ls = lockInfo['lockStatus']
        if ls == 0:
            print("\nCouldn't obtain SIM lock status.")
            print("Further operations would be dangerous.")
            exit(1)
        elif ls == 2:
            print("\nThe modem is already unlocked for this SIM.")
            exit(0)
        elif ls == 3:
            print("\nThe modem is hard locked,")
            print("This program cannot help you.")
            exit(1)
        else:
            print("\nThis SIM should be unlockable...")
            print("Remaining attempts: ", lockInfo['remaining'])
            print("Exceeding this will hard-lock the modem")

    unlockCode = computeUnlockCode(imei)
    print("\nUnlock code = ", unlockCode)
    print("Please be aware that a failed unlocking attempt could break your modem.")
    print("This is a risky procedure.")
    if not _requireYes():
        print("Unlocking aborted")
        exit(0)

    print("\nAttempting to unlock...")
    try:
        unlockModem(activePort, unlockCode)
    except:
        print("\nAn error occurred when trying to unlock the modem.")
        exit(1)

    print("\nWill check result in 5 seconds.")
    time.sleep(5)

    # Check result
    try:
        lockInfo = checkLockStatus(activePort)
    except:
        print("\nAn error occurred when trying to check the SIM lock.")
        exit(1)
    else:
        ls = lockInfo['lockStatus']
        if ls == 0:
            print("\nCouldn't obtain SIM lock status.")
            print("Further operations would be dangerous.")
            exit(1)
        elif ls == 1:
            print("\nUnlocking unsuccessful. Sorry.")
            exit(1)
        elif ls == 3:
            print("\nUnlocking unsuccessful.")
            print("The modem appears to have been hard locked. Sorry.")
            exit(1)
        else:
            print("\nUnlocking successful!")


def main():
    argvM = argvClass()
    if argvM.setup['question'] == 1:
        intro()
    if argvM.setup['menu'] == 1:
        menu = menuClass()
        menu.circle()
    else:
        auto()


if __name__ == "__main__":
    main()
