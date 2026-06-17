#  This program will perform the following activities
#1) Open a Chrome browser
#2) hit the weather site
#3) Copy the data
#4) Open a notepad
#5) paste it 

import pyautogui
import time
from datetime import datetime
import pyperclip
import re

pyautogui.FAILSAFE = False
pyautogui.PAUSE=0.5

# Step 1 - To open the chrome browser 
print("Open the chrome browswer...")
time.sleep(1)
pyautogui.hotkey('win', 's', interval=0.1)
time.sleep(1)
pyautogui.write('chrome', interval=0.15)
time.sleep(1)
pyautogui.press('enter')
time.sleep(1)


#Step 2) Hit the weather site
pyautogui.hotkey('ctrl','t')
time.sleep(1)
pyautogui.write('https://www.accuweather.com/en/in/chennai/206671/weather-warnings/206671',interval=0.1)
time.sleep(1)
pyautogui.press('enter')
time.sleep(1)

#Step 3) Copy the data
print("Opening Chennai weather page...")
pyautogui.hotkey('ctrl','a',interval=0.1)
time.sleep(1)
pyautogui.hotkey('ctr','c',interval=0.1)
time.sleep(1)

pyautogui.moveTo(495, 160)
time.sleep(1)
pyautogui.dragTo(745, 160, duration=0.5, button='left')
time.sleep(1)
pyautogui.hotkey('ctrl', 'c')
time.sleep(1)
my_weather = pyperclip.paste()
match = re.search(r'(\d+\s*°\s*C)', my_weather)
temperature = match.group(1).replace(" ", "")
print("the chennai temp is ",temperature)

# Step 4: Preparing the Weather record
today_date = datetime.today().strftime("%d-%m-%Y")
temp_number = int(re.search(r'\d+', temperature).group())

if temp_number < 25:
    status = "Weather is cool"
elif temp_number >= 26 and temp_number <= 31:
    status = "Weather is moderate"
else:
    status = "Weather is hot"

my_record = today_date + " Chennai weather : " + temperature + " " + status

print(my_record)

# Step 5: Writing to Excel sheet 
# This step creats the date, file name, header and the data row 
# Finally open an Excel sheet and writes the header followed by the data row
# Finally the file is saved as daily_report_YYYY-MM-DD.xlxs format
  
today_date = datetime.today().strftime("%Y-%m-%d")
my_file_path = save_path = r"C:\Social Eagle AI Course\Social Eagle GenAI Projects\daily-report-bot"
my_file_name = "daily_report_" + today_date + ".xlsx"
my_full_filepath=my_file_path+"\\"+my_file_name
my_header="Date  " + "\t" + "Temperature " + "\t" + "Weather Condition"
my_row = today_date + "\t" + temperature + "\t" + status

pyautogui.hotkey('win', 'r')
time.sleep(1)
pyautogui.write('excel /x')
time.sleep(1)
pyautogui.press('enter')
time.sleep(5)
pyautogui.hotkey('ctrl', 'n')
time.sleep(2)

pyautogui.press('enter')
pyautogui.press('enter')
pyautogui.write(my_header, interval=0.03)
pyautogui.press('enter')
pyautogui.write(my_row, interval=0.03)
time.sleep(1)

pyautogui.press('enter')

# Save the Excel file
#pyautogui.hotkey('ctrl', 's')
#time.sleep(2)
#pyautogui.write(my_full_filepath, interval=0.03)
#time.sleep(1)
#pyautogui.press('enter')
#time.sleep(2)

#Step 6: Take a Screenshot of the Excelsheet
screenshot=pyautogui.screenshot()
screenshot.save(r"C:\Social Eagle AI Course\Social Eagle GenAI Projects\daily-report-bot\daily_weather_report.png")

