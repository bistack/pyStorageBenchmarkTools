#!/usr/bin/python

import os
import time
#import stat
from misc_lib import run_command_list

class Speed:
    def __init__(self):
        self.__max = 0
        self.__min = -1
        self.__avg = 0

    def record_value(self, val):
        if float(val) > float(self.__max):
            self.__max = float(val)

        if self.__min < 0:
            self.__min = val
        elif float(val) < float(self.__min):
            self.__min = float(val)

        if self.__avg == 0:
            self.__avg = float(val)
        else:
            self.__avg = '%.2f' % ((float(self.__avg) + float(val)) / 2)

    def get_values(self):
        return self.__max, self.__avg, self.__min

class Raid_Util:
    def __init__(self, cmd_dir, src_dir):
        self.__cmd_dir = cmd_dir
        self.__src_dir = src_dir

        self.__raid_txn = True
        self.raid_name = None
        self.__sys_name = None
        self.sub_dev_list = []
        self.__sub_dev_cnt = 0
        self.cmd_args = ''
        self.__stripe_cache_size = 1024
        self.raid_sub_dev_size_KB = 0
        self.raid_level = 6

    def set_raid_level(self, level):
        self.raid_level = level

    def get_raid_level(self):
        return self.raid_level

    def get_lest_sub_dev_cnt(self):
        if self.raid_level == 6:
            return 4
        else:
            return 3

    def set_raid_sub_dev_size_KB(self, size_kb):
        self.raid_sub_dev_size_KB = size_kb

    def get_raid_sub_dev_size_KB(self):
        return self.raid_sub_dev_size_KB

    def set_stripe_cache_size(self, size):
        self.__stripe_cache_size = size

    def get_stripe_cache_size(self):
        return str(self.__stripe_cache_size)

    def set_cmd_args(self, args):
        self.cmd_args = args

    def get_cmd_args(self):
        return self.cmd_args

    def set_cmd_dir(self, path):
        self.__cmd_dir = path

    def get_cmd_dir(self):
        return self.__cmd_dir

    def set_src_dir(self, path):
        self.__src_dir = path

    def get_src_dir(self):
        return self.__src_dir

    def set_raid_txn(self, is_txn):
        self.__raid_txn = is_txn

    def get_raid_txn(self):
        return self.__raid_txn

    def get_cmd(self):
        return self.__cmd_dir + '/mdadm'

    def set_sub_dev_list(self, dev_list):
        self.sub_dev_list = dev_list

    def get_sub_dev_list(self):
        return self.sub_dev_list

    def get_sub_dev_cnt(self):
        self.__sub_dev_cnt = len(self.sub_dev_list)
        return self.__sub_dev_cnt

    def set_raid_name(self, name):
        self.raid_name = name

    def get_raid_path(self):
        path = None
        if os.path.exists('/dev/' + self.raid_name):
            path = ''.join(['/dev/', self.raid_name])
        elif os.path.exists('/dev/md/' + self.raid_name):
            path = ''.join(['/dev/md/', self.raid_name])

        return path

    def get_sys_name(self):
        if self.__sys_name:
            return self.__sys_name

        path = self.get_raid_path()
        if not path:
            return

        #mode = os.stat(path).st_mode
        tgt = os.readlink(path)
        #print tgt
        self.__sys_name = tgt.split(os.sep)[-1]
        return self.__sys_name


    def remove_raid(self):
        path = self.get_raid_path()
        if not path:
            return
        cmds = [' '.join([self.get_cmd(), '-S', path])]

        (status, _) = run_command_list(cmds)
        if not status:
            self.__sys_name = None

    def exit_raid(self):
        cmds = ['rmmod raid456 md_mod',
                'modprobe -r async_raid6_recov async_pq',
                #'rmmod raid6_pq',
                #'dmesg -C > /dev/null'
                ]

        run_command_list(cmds)

    def init_raid(self):
        if self.get_raid_txn():
            src_dir = self.get_src_dir()
            cmds = ['insmod ' + src_dir + '/raid6_pq.ko',
                        'modprobe async_raid6_recov',
                        'insmod ' + src_dir + '/md-mod.ko',
                        'insmod ' + src_dir + '/raid456.ko']

        else:
            cmds = ['modprobe md_mod',
                        'modprobe raid456']

        run_command_list(cmds)

    def zero_raid_sub_dev(self, tgt = None):
        raid_cmd = self.get_cmd()
        if self.get_sub_dev_cnt() == 0:
            return

        if tgt:
            devs = tgt
        else:
            devs = ' '.join(self.get_sub_dev_list())

        cmds = [' '.join([raid_cmd, '--zero-superblock',
                          '--force', devs])]
        run_command_list(cmds)


    def create_raid(self):
        if self.get_sub_dev_cnt() < self.get_lest_sub_dev_cnt():
            return

        raid_cmd = self.get_cmd()
        if self.get_raid_txn():
            txn = '-T'
        else:
            txn = ''

        devs = ' '.join(self.get_sub_dev_list())
        cmd_create = ' '.join(['echo "y" |', raid_cmd,
                               '-C', '/dev/md/' + self.raid_name,
                               self.cmd_args,
                               '-n', str(self.get_sub_dev_cnt()),
                               '-l', str(self.get_raid_level()),
                               '-z', str(self.get_raid_sub_dev_size_KB()),
                               txn, devs])

        cmds =  [cmd_create]
        run_command_list(cmds)

        if not self.get_sys_name():
            return

        cmd_change = ''.join(['echo ', str(self.get_stripe_cache_size()),
                              ' > /sys/block/', self.get_sys_name(),
                              '/md/stripe_cache_size'])
        cmds =  [cmd_change]
        run_command_list(cmds)

    def assemble_raid(self):
        raid_cmd = self.get_cmd()
        devs = ' '.join(self.get_sub_dev_list())
        cmds = [' '.join([raid_cmd, '-A', self.get_raid_path(), devs])]
        run_command_list(cmds)

    def show_raid_info(self):
        if not self.get_sys_name():
            return

        cmds = ['cat /proc/mdstat',
                ''.join(['cat /sys/block/', self.get_sys_name(),
                         '/md/stripe_cache_size']),
                #'cat /proc/modules | grep raid456'
                ]
        run_command_list(cmds)

    def fail_one(self, index = 0):
        if not self.get_sys_name():
            return
        tgt = self.get_sub_dev_list()[index]
        cmd_fail = ' '.join([self.get_cmd(),
                             self.get_raid_path(),
                             '--fail', tgt
                             ])
        cmd_remove = ' '.join([self.get_cmd(),
                             self.get_raid_path(),
                             '--remove', tgt
                             ])

        cmds = [cmd_fail, cmd_remove]
        run_command_list(cmds)

    def fail_two(self, index1 = 0, index2 = 1):
        self.fail_one(index1)
        self.fail_one(index2)

    def add_one(self, index = 0):
        if not self.get_sys_name():
            return
        tgt = self.get_sub_dev_list()[index]
        self.zero_raid_sub_dev(tgt)
        cmd = ' '.join([self.get_cmd(),
                        self.get_raid_path(),
                        '--add', tgt
                        ])
        cmds = [cmd]
        run_command_list(cmds)

    def add_two(self, index1 = 0, index2 = 1):
        self.add_one(index1)
        self.add_one(index2)

    def check_recovery_speed(self, speed_obj):
        if not self.get_sys_name():
            return 0

        cmd = ' '.join(['cat /proc/mdstat  | grep -A3', self.get_sys_name(),
                        '| grep speed'
                        ])
        cmds = [cmd]
        (status, speed) = run_command_list(cmds)
        if status:
            return 0

        speed_start = speed.find('speed=')
        if speed_start < 0:
            return 0

        speed_start += len('speed=')

        speed_end = -1
        speed_units = ['K', 'M', 'G', 'B']
        for unit in speed_units:
            speed_end = speed[speed_start:].find(unit)
            if speed_end >= 0:
                break

        if speed_end < 0:
            print speed
            return 0

        speed_end += speed_start
        speed_value = speed[speed_start: speed_end]
        speed_obj.record_value(speed_value)

        return 1

    def wait_recovery_time(self, cnt = 100):
        speed_obj = Speed()
        for i in range(cnt):
            if i < 7:
                continue

            ret = self.check_recovery_speed(speed_obj)
            if not ret:
                break
            time.sleep(1)

        print 'recovery speed (max avg min):', speed_obj.get_values()

    def wait_sync(self):
        speed_obj = Speed()

        while self.check_recovery_speed(speed_obj):
            time.sleep(5)

        print 'resync speed (max avg min):', speed_obj.get_values()
