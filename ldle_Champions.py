import time
import pyautogui

pyautogui.FAILSAFE = False



def click(ImageName, ImagePicture):
    ImageFound = pyautogui.locateOnScreen(ImagePicture)
    if ImageFound:
        while ImageFound:
            print(ImageName + ' Located')
            x = ImageFound.left + 1
            y = ImageFound.top + 1
            pyautogui.mouseDown(x=(x), y=(y), button='PRIMARY')
            time.sleep(5)
            pyautogui.mouseUp(x=(x), y=(y), button='PRIMARY')
            ImageFound = pyautogui.locateOnScreen(ImagePicture)
    else:
        print('Nothing Located')
 

def AutoProgress():
    pyautogui.locateOnScreen('AutoProgress.PNG')
    if AutoProgress:
          Coins_Upgrades()
          print('Progress Active')

 
def Coins_Upgrades():
    click('BlueCoin', 'BlueCoin.PNG')
    click('GreenCoin', 'GreenCoin.PNG')
    click('RedUpgrade', 'RedUpgrade.PNG')
    click('SelectButton', 'SelectButton.PNG')
    click('SelectButtonV2', 'SelectButtonV2.PNG')
    click('CloseButton', 'CloseButton.PNG')
    click('BlueUpgrade', 'BlueUpgrade.PNG')
    click('BlueUpgradeV2', 'BlueUpgradeV2.PNG')
    click('OrangeUpgrade', 'OrangeUpgrade.PNG')
    click('GreenUpgrade', 'GreenUpgrade.PNG')
    click('PurpleUpgrade', 'PurpleUpgrade.PNG')
    click('PinkUpgrade', 'PinkUpgrade.PNG')
    click('SelectButton', 'SelectButton.PNG')
    click('SelectButtonV2', 'SelectButtonV2.PNG')
    click('CloseButton', 'CloseButton.PNG')
    click('AutoProgress', 'AutoProgress.PNG')
    click('CompleteButton', 'CompleteButton.PNG')
    click('CompleteButtonV2', 'CompleteButtonV2.PNG')
    click('SkipButton', 'SkipButton.PNG')
    click('ContineButton', 'ContineButton.PNG')

while True:
    
    Coins_Upgrades()
    
    AutoProgress()



    




   
     


