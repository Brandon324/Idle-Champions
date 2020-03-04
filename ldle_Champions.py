import time
import pyautogui


# Still in the works 
def Startup():
    time.sleep(5)
    pyautogui.locateOnScreen
    pyautogui.click
    time.sleep(1)
    pyautogui.locateOnScreen
    pyautogui.click
    time.sleep(1)
    pyautogui.locateOnScreen
    pyautogui.click
    time.sleep(1)
    pyautogui.locateOnScreen('StartObjective.PNG')
    pyautogui.click('StartObjective.PNG')


pyautogui.FAILSAFE = False



def click(ImageName, ImagePicture):
    ImageFound = pyautogui.locateOnScreen(ImagePicture)
    if ImageFound:
        while ImageFound:
            print(ImageName + ' Located')
            x = ImageFound.left + 1
            y = ImageFound.top + 1
            pyautogui.click(x=(x), y=(y), button='PRIMARY')
            ImageFound = pyautogui.locateOnScreen(ImagePicture)
    else:
        print('Nothing Located')
       
 
def BlueCoin():
    return click('BlueCoin', 'BlueCoin.PNG')

def GreenCoin():
    return click('GreenCoin', 'GreenCoin.PNG')

def RedUpgrade():
    return click('RedUpgrade', 'RedUpgrade.PNG')

def BlueUpgrade():
    return click('BlueUpgrade', 'BlueUpgrade.PNG')

def OrangeUpgrade():
    return click('OrangeUpgrade', 'OrangeUpgrade.PNG')

def GreenUpgrade():
    return click('GreenUpgrade', 'GreenUpgrade.PNG')

for i in range(1000):

    BlueCoin()

    GreenCoin() 

    RedUpgrade()

    BlueUpgrade()

    OrangeUpgrade()

    GreenUpgrade()




    




   
     


