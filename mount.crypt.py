#!python3

import configparser, csv, getopt, getpass, subprocess, sys
from os.path import basename

class MountCrypt:
    
    def __init__(self):
        self.sleep = 30   # seconds to sleep between commands
        self.version = "0.1b"

    def print_version(self):
        print("Version: {version}".format(version=self.version))

    def read_config(self, config_file):
        print("Using config {}".format(config_file))
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.base_dir = self.config['DEFAULT']['base_dir']
        self.cryptsetup = self.config['DEFAULT']['cryptsetup']
        self.mount = self.config['DEFAULT']['mount']
        self.volumes = self.config.sections()

    def mount_volumes(self):
        for volume in self.volumes:
            uuid = self.config[volume]['UUID']
            print("Volume: {}".format(volume))
            print("UUID: {}".format(uuid))
            num_errors = 0
            mounts = self.config[volume]['mounts'].split(',')

            try:
                # Decrypt volume
                p = subprocess.Popen([self.cryptsetup, "open", "--type", "luks", "UUID=" + uuid, volume],stdout=subprocess.PIPE,stdin=subprocess.PIPE)
                p.stdin.write(bytes(getpass.getpass("Enter passphrase: "), 'utf-8'))
                p.communicate()[0]
                p.stdin.close()
            except Exception as details:
                print("Command error: {}".format(details))
                num_errors += 1

            if (num_errors == 0):
                for mnt_pt in mounts:
                    print("Mounting: {}".format(mnt_pt))
                    try:
                        # Mount volume
                        subprocess.Popen([self.mount, mnt_pt])
                    except Exception as details:
                        print("Command error: {}".format(details))
                        num_errors += 1

            if (num_errors == 0):
                self.run_programs(volume)
            else:
                print("Errors found! Did not run associated program(s).")

    def run_programs(self, volume):
        if (self.config.has_option(volume,'run_progs')):
            for program in self.config[volume]['run_progs'].split(','):
                print("Running: {}".format(program))
                try:
                    subprocess.run([program], shell=True, check=True)
                except Exception as details:
                    print("Error: {}".format(details))
        else:
            print("Nothing to run for this volume")

        
    def print_usage(self):
        usage_text="""{program} [options]

OPTIONS
    -c, --config <my-config.ini>     Configuration file
    -h, --help                    Print this help

CONFIG FILE

EXAMPLE:
[DEFAULT]
base_dir=/usr/local/sbin
cryptsetup=/sbin/cryptsetup
mount=/bin/mount

# Mount Definitions:
# ------------------
# NOTE: The mapper-name and mount-points need to also be defined and
# match the entries for these respective drives in /etc/fstab.
#
# [mapper-name]
# UUID = abc...def
# mounts = /mnt/mount-point,/mnt/other-mount-point,...
#
# [data]
# UUID = 123-abc-def-456
# mounts = /mnt/a,/mnt/b
#
# Optionally include any commands to run after a successful mount.
# run_progs = my-script.sh --some-flag,my-other-script.sh
# 
# NOTE: Lists MUST NOT have ANY spaces nor double-quotes 
# in-between the comma delimiter.

[test_internal_3.6T_1]
UUID=123-abc-def-456
mounts=/mnt/datafs,/mnt/local-backupfs
#run_progs=lxc list,echo bob

"""
# End here-doc

        print(usage_text.format(program=sys.argv[0]))

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"c:hv", 
            ["config=", "help", "version"])
    except getopt.GetoptError:
        print("Invalid option or missing argument!")
        print("For help, run: {program} {help_flag}".format(program=basename(__file__), help_flag="[-h | --help]"))
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            MountCrypt().print_usage()
            sys.exit()
        elif opt in ('-v', '--version'):
            MountCrypt().print_version()
            sys.exit()
        elif opt in ('-c', '--config'):
            mc = MountCrypt()
            mc.read_config(arg)
            mc.mount_volumes()
        else:
            print("ERROR: Must provide all required options. See usage below.")
            print("For help, run: {program} {help_flag}".format(program=basename(__file__), help_flag="[-h | --help]"))
            sys.exit(2)


if __name__ == "__main__": main(sys.argv[1:])
