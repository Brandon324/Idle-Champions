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
       
 
def Coins_Upgrades():
    click('BlueCoin', 'BlueCoin.PNG')
    click('GreenCoin', 'GreenCoin.PNG')
    click('RedUpgrade', 'RedUpgrade.PNG')
    click('BlueUpgrade', 'BlueUpgrade.PNG')
    click('OrangeUpgrade', 'OrangeUpgrade.PNG')
    click('GreenUpgrade', 'GreenUpgrade.PNG')
    click('PurpleUpgrade', 'PurpleUpgrade.PNG')
    click('PinkUpgrade', 'PinkUpgrade.PNG')
    click('SelectButton', 'SelectButton.PNG')
    click('CloseButton', 'CloseButton.PNG')

for i in range(1000):

    Coins_Upgrades()



    




   
     


