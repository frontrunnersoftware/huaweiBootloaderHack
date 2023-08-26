import json
import time
import math
from os import system, name
import sys
import subprocess

welcomeText = """
********************************************************************************  
*                   Huawei Bootloader Brute Force Unlock                       *
*          Modified by PythonesqueSpam from code originated by Haex            *
*                                                                              *
*   Please enable USB DEBBUG and OEM UNLOCK if your device does not appear     *
*                                                                              *
*              Be aware of losing all your data => do backup ;)                *
******************************************************************************** 
IMEI1 = 123456789012345
* Execution Note - Latest shot 123456 with code 1234567890123456 *
IMEI2 = 543210987654321
* Execution Note - Latest shot 654321 with code 6543210987654321 *
"""

###############################################################################

failedAttemptsFilename   = 'failedAttempts.json'
foundUnlockCodesFilename = 'foundUnlockCodes.json'
startingPoint            = 1000000000000000

# if your device has a limit of false attempts before reboot
# otherwise set isLimitAttemptEnabled to false
limitAttempt             = 5
isLimitAttemptEnabled    = True

###############################################################################

def getFromFile(filename = 'failedAttempts.json'):
  try:

    with open(filename, 'r') as file:
      array = json.load(file)
      if (type(array) == list):
        return set(array)
      else:
        return set([ ])
  
  except:
    return set([ ])


def writeToFile(filename = 'failedAttempts.json', failedAttempts = [ ]):
  startTime = time.time()
  failedAttempts.sort(reverse = True)
  with open(filename, 'w') as file:
    json.dump(failedAttempts, file)
    print('* saved {0} file in {1} seconds *'.format(filename, time.time() - startTime))


def incrementChecksum(imei, checksum, testCode):
  testCode += int(checksum + math.sqrt(imei) * 1024)
  return testCode


def calculateChecksum(imei):
  def digits_of(n):
    return [int(d) for d in str(n)]
  digits      = digits_of(imei)
  oddDigits   = digits[-1::-2]
  evenDigits  = digits[-2::-2]
  checksum    = 0
  checksum    += sum(oddDigits)
  for i in evenDigits:
    checksum += sum(digits_of(i * 2))
  return checksum % 10


def tryUnlockBootloader(imei, checksum, failedAttempts = set([ ])):
  unlocked       = False
  testUnlockCode = 1000000000000000
  testedCode     = True
  dotNumber      = 0

  while(unlocked == False):

    # Increment and validate unlock codes against those already tested.. 
    testedCode = (testUnlockCode in failedAttempts or testUnlockCode < startingPoint)
    if testedCode:
        print('\nFinding the next untested unlock code..\n')
        dotNumber = progressIndicator()
        while testedCode:
            testUnlockCode = incrementChecksum(imei, checksum, testUnlockCode)
            testedCode = (testUnlockCode in failedAttempts or testUnlockCode < startingPoint)
            if testedCode:
                dotNumber = progressIndicator(dotNumber)
            else:
                clearScreen()
                print(welcomeText)
    
    # Try and unlock the phone..
    answer = subprocess.run(['fastboot', 'oem', 'unlock', str(testUnlockCode)], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL) 

    # Is the phone unlocked..
    if answer.returncode == 0:
        unlocked = True
        return testUnlockCode
    else:
      failedAttempts.add(testUnlockCode)

    countAttempts = len(failedAttempts)
    print('* shot {0} with code {1} *'.format(countAttempts, testUnlockCode))
    
    # Reboot in bootloader mode after limit of attempts is reached
    if (countAttempts % (limitAttempt - 1) == 0 and isLimitAttemptEnabled == True) or (countAttempts % 40000 == 0 and isLimitAttemptEnabled == False):
      answer = subprocess.run(['fastboot', 'reboot', 'bootloader'], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
    
    if (isLimitAttemptEnabled and countAttempts % (limitAttempt - 1) == 0) or (not isLimitAttemptEnabled and countAttempts % 100 == 0):
      writeToFile(failedAttemptsFilename, list(failedAttempts))

    testUnlockCode = incrementChecksum(imei, checksum, testUnlockCode)


def progressIndicator(dotNumber = 0):
  initialString = 'Processing '
  maxDotNumber = 68
  if dotNumber < maxDotNumber:
    dotNumber += 1
    dots = dotNumber * '-'
  else:
    dotNumber = 1
    dots = ''
  spaceNumber = maxDotNumber - dotNumber
  spaces = spaceNumber * ' '
  backspaceNumber = maxDotNumber + len(initialString) + 1
  backspaces = backspaceNumber * '\b'
  print('{0}{1}{2}{3}{4}'.format(initialString,dots,'>',spaces,backspaces), end='', flush=True)
  # time.sleep(0.00005)
  return dotNumber


def clearScreen():
  
    # for windows
    if name == 'nt':
        _ = system('cls')
  
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')


def main(args = [ ]):
  clearScreen()
  print(welcomeText)

  subprocess.run(['adb', 'devices'])

  imei = int(args[1]) if len(args) > 1 else int(input('Type IMEI digit: '))
  checksum = calculateChecksum(imei)

  subprocess.run(['adb', 'reboot', 'bootloader'], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

  input('\nPress any key when your device is in fastboot mode..')

  clearScreen()
  print(welcomeText)
  
  failedAttempts  = getFromFile(failedAttemptsFilename)
  foundUnlockCode = tryUnlockBootloader(imei, checksum, failedAttempts)

  clearScreen()
  print(welcomeText)

  # See if phone is unlocked and reboot it..
  subprocess.run(['fastboot', 'getvar', 'unlocked'])
  subprocess.run(['fastboot', 'reboot'])

  # Show found unlock code..  
  print('\n\nDevice unlocked! OEM CODE: {0}'.format(foundUnlockCode))
  print('Keep it safe\n')
  input('Press any key to continue...\n')

  # Save found unlock code to file...
  foundUnlockCodes  = getFromFile(foundUnlockCodesFilename)
  if foundUnlockCode not in foundUnlockCodes :
    foundUnlockCodes.add(foundUnlockCode)
    writeToFile(foundUnlockCodesFilename, list(foundUnlockCodes))

  input('Press any key to exit...\n')
  exit()
###############################################################################

if __name__ == '__main__':
  main(sys.argv)