#!/usr/bin/env python
#
# unlocker.py
# - Remove simlock on huawei modems
#
# Copyright (C) 2013 Neil McPhail
#		neil@mcphail.homedns.org
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

import time, serial, re, hashlib, glob, urllib2


class menuClass:
    status = 1
    command = {}
    setup={'hilinkIp':"192.168.8.1",'IMEI':"?",'serialPort':"?",'lock status':"?",'lock try remaining':"?",'mobile carrier':"?"}
    def details(self):
        print 80 * "-"
        for key in self.setup:
            print key + " : " + str(self.setup[key])
        print 80 * "-"
    def run(self):
        response = raw_input(">> ")
        try :
            return  self.command[response]()
        except:
             print "command '"+response+"' not found"
             return False
        return True
    def checkPorts(self):
        try:
            activePort = identifyPort()
        except:
            print "\nAn error occurred when probing for active ports."
            print "This may be because you need to run this program as root."
            return False
        else:
            if (activePort==''):
                print "\nCould not identify active port."
                return False
            self.setup['serialPort'] = activePort
            return True
    def getIMEI(self):
        try:
            imei = obtainImei(self.setup['serialPort'])
        except:
            print "\nAn error occurred when trying to check the IMEI."
            return False 
        else:
            if (imei==''):
                 print "\nCould not obtain IMEI."
                 print "Check the modem is properly inserted"
                 print "Check a SIM card is in place"
                 print "Check you are not already connected"
                 print "Try removing and reinserting the device"
                 return False
            else:
                 if not testImeiChecksum(imei):
                     print "\nIMEI checksum invalid."
                     return False
        self.setup['IMEI']=imei
      #  setup['unlock code v1'] = computeUnlockCode(imei)
        return True

    def getLockStatus(self):
        try:
            lockInfo = checkLockStatus(self.setup['serialPort'])
            if not lockInfo:
                return False
            self.setup['lock status'] = lockInfo['lockStatus']
            self.setup['lock try remaining'] = lockInfo['remaining']
            self.setup['mobile carrier'] = lockInfo['carrier']
        except:
            print "\nAn error occurred when trying to check the SIM lock."
            return False
        else:
            ls = lockInfo['lockStatus']
            if ls == 0:
                print "\nCouldn't obtain SIM lock status."
                print "Further operations would be dangerous."
                return False 
            elif ls == 2:
                print "\nThe modem is already unlocked for this SIM."
                return True
            elif ls == 3:
                print "\nThe modem is hard locked,"
                print "This program cannot help you."
                return False
            else:
                print "\nThis SIM should be unlockable..."
                print "Remaining attempts: ", lockInfo['remaining']
                print "Exceeding this will hard-lock the modem"
                return False
            return True
    def title(self, text):
        print 80*"="
        print "Huawei unlocker "+text 
        print 80*"="
    def menuPoint (self, menu):
        for key in menu:
            print "\t " + key + ". " + menu[key]
    def menu(self):
        self.title("main menu")
        print "\t 1. Automatic"
        print "\t 2. Advanced"
        print "\t e. Exit"
        self.command={'1':auto,'2':self.toAdvanced,'e':self.toExit}
    def advanced(self):
        self.details()
        self.title("advanced menu")
        print "\t 1. detect port"
        print "\t 2. detect imei"
        print "\t 3. detect lock status"
        print "\t m. bact to main menu"
        print "\t e. Exit"
        self.command={'1':self.checkPorts,'2':self.getIMEI,'3':self.getLockStatus,'m':self.toMain,'e':self.toExit}
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
            else:
               break 
            self.run()
        print "bye bye"
        exit(0)




# Intro
def intro():
	print 80 * "*"
	print "\tHuawei modem unlocker"
	print "\tBy Neil McPhail and dogbert"
	print "\tThis is Free Software as defined by the GNU GENERAL PUBLIC"
	print "\tLICENSE version 2"
	print 80 * "*"
	print "\tThis software comes with NO WARRANTY"
	print "\tThis software can damage your hardware"
	print "\tUse it at your own risk"
	print 80 * "*"
	print "\tNot all modems can be unlocked with this software."
	print "\tUsers have reported problems with the following devices:"
	print "\t\tE220, E353"
	print "\tAttempting to unlock these devices with this software is not"
	print "\trecommended. I hope to fix this in a later release."
	print 80 * "*"
	if not _requireYes():
		print "Bye"
		exit(0)

# Helper function
# Require an explicit "YES" in upper case
# Returns True if "YES"
# Asks for explicit uppercase "YES" if mixed or lower case used
# Returns False for anything else
def _requireYes():
	print "If you wish to proceed, please type YES at the prompt"
	while 1:
		response = raw_input(">> ")
		if response == "YES":
			return True
		if response.upper() == "YES":
			print "You must type YES in upper case to proceed"
			continue
		else:
			return False

            
def searchIMEI():
    try:
        imei = obtainImei(setup['serialPort'])
    except:
        print "\nAn error occurred when trying to check the IMEI."
        return False 
    else:
        if (imei==''):
            print "\nCould not obtain IMEI."
            print "Check the modem is properly inserted"
            print "Check a SIM card is in place"
            print "Check you are not already connected"
            print "Try removing and reinserting the device"
            return False
        else:
            if not testImeiChecksum(imei):
                print "\nIMEI checksum invalid."
                return False
    setup['IMEI']=imei
    setup['unlock code v1'] = computeUnlockCode(imei)
    return True

def searchLockStatus():
    try:
        lockInfo = checkLockStatus(setup['serialPort'])
        if not lockInfo:
            return False
        setup['lock status'] = lockInfo['lockStatus']
        setup['lock try remaining'] = lockInfo['remaining']
        setup['mobile carrier'] = lockInfo['carrier']
    except:
        print "\nAn error occurred when trying to check the SIM lock."
        return False
    else:
        ls = lockInfo['lockStatus']
        if ls == 0:
            print "\nCouldn't obtain SIM lock status."
            print "Further operations would be dangerous."
            return False 
        elif ls == 2:
            print "\nThe modem is already unlocked for this SIM."
            return True
        elif ls == 3:
            print "\nThe modem is hard locked,"
            print "This program cannot help you."
            return False
        else:
            print "\nThis SIM should be unlockable..."
            print "Remaining attempts: ", lockInfo['remaining']
            print "Exceeding this will hard-lock the modem"
            return False
        return True

# These modems seem to open 3 USB serial ports. Only one is the control port
# and this seems to vary from device to device. The other 2 ports appear to
# remain silent
def identifyPort():
	print "Trying to find which port is the active modem connection."
	print "Please be patient as this can take a while.\n\n"
	for p in glob.glob('/dev/ttyUSB*'):
		print "Testing port " + p
		ser = serial.Serial(port = p,
			timeout = 15, xonxoff=False, rtscts=True, dsrdtr=True)
		ser.write('AT\r\n')
		activity = ser.read(5)
		if activity == '':
			print "\tNo activity\n"
			ser.close()
			continue
		
		print "\tActivity detected\n"
		ser.close()
		return p
	return ''

# The modem should respond with the IMEI with the AT+CGSN command
def obtainImei(port):
	print "\nTrying to obtain IMEI."
	print "The modem will be given 5 seconds to respond."
	ser = serial.Serial(port = port,
			timeout = 15, xonxoff=False, rtscts=True, dsrdtr=True)
	ser.flushInput()
	ser.write('AT+CGSN\r\n')
	time.sleep(5)
	response = ser.read(4096)
	ser.close()
	match = re.search('\r\n(\d{15})\r\n', response)
	if match:
		print "Found probable IMEI: " + match.group(1)
		return match.group(1)
	else:
		print "IMEI not found"
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
		print 80 * "*"
		print "\n\tWarning"
		print "\n\tYour modem's IMEI begins with '8'"
		print "\tIt is likely to be incompatible with this script"
		print "\tProceed at your own risk"
		print "\n\tPlease provide feedback: see README and HELPME\n"
		print 80 * "*"

# Interrogate the lock status
# Returns a dictionary with the lock status, remaining unlock attempts
# and the - largely unused - carrier code
#
# lockStatus 0 = unobtainable
#            1 = locked but can be unlocked
#            2 = unlocked to the inserted sim
#            3 = locked and cannot be unlocked
def checkLockStatus(port):
    status = {'lockStatus': 0, 'remaining': 0, 'carrier': 0}
    print "\nChecking the lock status of the SIM."
    print "The modem will be given 5 seconds to respond."
    ser = serial.Serial(port = port,
			timeout = 15, xonxoff=False, rtscts=True, dsrdtr=True)
    ser.flushInput()
    ser.write('AT^CARDLOCK?\r\n')
    time.sleep(5)
    response = ser.read(4096)
    print response
    ser.close()
    match = re.search('CARDLOCK: (\d),(\d\d?),(\d+)\r', response)
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
	digest = hashlib.md5((imei+salt).lower()).digest()
	code = 0
	for i in range(0,4):
		code += (ord(digest[i])^ord(digest[4+i])^ord(digest[8+i])^ord(digest[12+i])) << (3-i)*8
	code &= 0x1ffffff
	code |= 0x2000000
	return code

# Send AT codes to unlock the modem
def unlockModem(port, lockCode):
	ser = serial.Serial(port = port)
	command = 'AT^CARDLOCK="'+ str(lockCode) + '"\r\n'
	ser.write(command)
	ser.close()

def auto():
	intro()
	# Work out which is the control port
	try:
		activePort = identifyPort()
	except:
		print "\nAn error occurred when probing for active ports."
		print   "This may be because you need to run this program as root."
		exit(1)
	else:
		if (activePort==''):
			print "\nCould not identify active port."
			exit(1)

	# Obtain and check IMEI
	try:
		imei = obtainImei(activePort)
	except:
		print "\nAn error occurred when trying to check the IMEI."
		exit(1)
	else:
		if (imei==''):
			print "\nCould not obtain IMEI."
			print "Check the modem is properly inserted"
			print "Check a SIM card is in place"
			print "Check you are not already connected"
			print "Try removing and reinserting the device"
			exit(1)
		else:
			if not testImeiChecksum(imei):
				print "\nIMEI checksum invalid."
				exit(1)
			else:
				print "IMEI checksum OK."
				checkImeiCompatibility(imei)

	# Obtain lockstatus
	try:
		lockInfo = checkLockStatus(activePort)
	except:
		print "\nAn error occurred when trying to check the SIM lock."
		exit(1)
	else:
		ls = lockInfo['lockStatus']
		if ls == 0:
			print "\nCouldn't obtain SIM lock status."
			print "Further operations would be dangerous."
			exit(1)
		elif ls == 2:
			print "\nThe modem is already unlocked for this SIM."
			exit(0)
		elif ls == 3:
			print "\nThe modem is hard locked,"
			print "This program cannot help you."
			exit(1)
		else:
			print "\nThis SIM should be unlockable..."
			print "Remaining attempts: ", lockInfo['remaining']
			print "Exceeding this will hard-lock the modem"

	unlockCode = computeUnlockCode(imei)
	print "\nUnlock code = ", unlockCode
	print "Please be aware that a failed unlocking attempt could break your modem."
	print "This is a risky procedure."
	if not _requireYes():
		print "Unlocking aborted"
		exit(0)

	print "\nAttempting to unlock..."
	try:
		unlockModem(activePort, unlockCode)
	except:
		print "\nAn error occurred when trying to unlock the modem."
		exit(1)

	print "\nWill check result in 5 seconds."
	time.sleep(5)

	# Check result
	try:
		lockInfo = checkLockStatus(activePort)
	except:
		print "\nAn error occurred when trying to check the SIM lock."
		exit(1)
	else:
		ls = lockInfo['lockStatus']
		if ls == 0:
			print "\nCouldn't obtain SIM lock status."
			print "Further operations would be dangerous."
			exit(1)
		elif ls == 1:
			print "\nUnlocking unsuccessful. Sorry."
			exit(1)
		elif ls == 3:
			print "\nUnlocking unsuccessful."
			print "The modem appears to have been hard locked. Sorry."
			exit(1)
		else:
			print "\nUnlocking successful!"


def main():
    menu = menuClass()
    menu.circle()


if __name__ == "__main__":
    main()


