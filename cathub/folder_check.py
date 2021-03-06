#!/usr/bin/python

import os
import sys
import json

try:  # sherlock 1 or 2
    sherlock = os.environ['SHERLOCK']
    if sherlock == '1':
        catbase = '/home/winther/data_catapp'
    elif sherlock == '2':
        catbase = '/home/users/winther/data_catapp'
except:  # SUNCAT
    catbase = '/nfs/slac/g/suncatfs/data_catapp'

sys.path.append(catbase)

def main(folder):
    miss_list = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if 'MISSING: ' in file:
                traj = file.replace('MISSING: ', '')
                if os.path.isfile(root + '/' + traj):
                    print('found {}'.format(traj))
                    os.remove(root + '/' + file)
                else:
                    miss_list.append(traj)

    if len(miss_list) > 0:
        print('Files missing')
        print(miss_list)
    else:
        print('all files there!')
    return

if __name__ == "__main__":
    from sys import argv
    folder = argv[1]
    main(folder)
