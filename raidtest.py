#!/usr/bin/python

from commands import getstatusoutput
import os, stat

class HBA:
    def __init__(self, name):
        self.sys_name = name
        self.bdev_list_dir = {}

    def test_bdev(self):
        if not len(self.bdev_list_dir):
            return

        for (_, bdev_list) in self.bdev_list_dir.items():
            i = 0
            for bdev in bdev_list:
                cmd = ' '.join(['mount', '|', 'grep', bdev])
                (status, _) = getstatusoutput(cmd)
                if status: # not mounted
                    cmd = ' '.join(['dd if=/dev/zero of=/dev/' + bdev,
                                    'bs=1M count=1 oflag=direct 2>&1',
                                    '|', 'grep MB'])
                    (status, winfo) = getstatusoutput(cmd)
                    if status:
                        print '%s cannot write: %s' % (bdev, winfo)
                        del bdev_list[i]

                    i += 1
                    continue

                print 'not use bdev as it mounted: %s' % (bdev)
                del bdev_list[i]
                i += 1


    def get_bdev(self):
        base = '/sys/bus/pci/drivers/' + self.sys_name
        cmd = ' '.join(['ls', base, '|', 'grep :'])

        (status, host_ids) = getstatusoutput(cmd)

        if status:
            print '%s : %s' % (str(status), host_ids)
            return

        for host_id in host_ids.split():
            host_id_base = ''.join([base, '/', host_id])
            cmd = ' '.join(['ls', host_id_base, '|', 'grep host'])
            (status, host) = getstatusoutput(cmd)
            if status:
                print '%s : %s' % (str(status), host)
                return

            bdev_list = []
            host_base = ''.join([host_id_base, '/', host])
            cmd = ' '.join(['ls', host_base, '|', 'grep target'])
            (status, target_ids) = getstatusoutput(cmd)
            if status:
                print '%s : %s' % (str(status), target_ids)
                return

            for target_id in target_ids.split():
                target_id_base = ''.join([host_base, '/', target_id])
                cmd = ' '.join(['ls', target_id_base, '|', 'grep :'])
                (status, bdev_ids) = getstatusoutput(cmd)

                if status:
                    print '%s : %s' % (str(status), bdev_ids)
                    return

                for bdev_id in bdev_ids.split():
                    bdev_id_base = ''.join([target_id_base, '/',
                                            bdev_id, '/block'])
                    cmd = ' '.join(['ls', bdev_id_base, '|', 'grep sd'])
                    (status, bdev) = getstatusoutput(cmd)

                    if status:
                        #print '%s : %s' % (str(status), bdev)
                        continue

                    bdev_list.append(bdev)

            self.bdev_list_dir[host] = bdev_list

        self.test_bdev()

    def print_bdev_list(self):
        if not len(self.bdev_list_dir):
            self.get_bdev()

        for host, bdevs in self.bdev_list_dir.items():
            print 'host: %s' % (host)
            for bdev in bdevs:
                print '\t%s' % (bdev)

    def get_bdev_balanced(self, cnt):
        if not len(self.bdev_list_dir):
            return

        chose_list = []
        i = cnt / 2
        j = cnt - i
        for (_, bdev_list) in self.bdev_list_dir.items():
            if i > len(bdev_list) or j > len(bdev_list):
                print 'need %d bdevs' % (cnt)
                self.print_bdev_list()
                break

            for bdev in bdev_list:
                if i == 0 and j == 0:
                    break

                chose_list.append(bdev)
                if i > 0:
                    i -= 1
                    if i == 0:
                        break
                elif j > 0:
                    j -= 1
                    if j == 0:
                        break


        return chose_list


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

        mode = os.stat(path).st_mode

        tgt = os.readlink(path)
        print tgt
        self.__sys_name = tgt.split(os.sep)[-1]
        return self.__sys_name

    def run_command_list(self, cmds):
        for cmd in cmds:
            (status, output) = getstatusoutput(cmd)
            if status:
                print '%s, Err: %s: %s' % (cmd, str(status), output)
                return 0
            else:
                print '%s' % (output)

        return 1

    def remove_raid(self):
        path = self.get_raid_path()
        if not path:
            return
        cmds = [' '.join([self.get_cmd(), '-S', path])]

        if self.run_command_list(cmds):
            self.__sys_name = None

    def exit_raid(self):
        cmds = ['rmmod raid456 md_mod',
                'modprobe -r async_raid6_recov async_pq',
                #'rmmod raid6_pq',
                #'dmesg -C > /dev/null'
                ]

        self.run_command_list(cmds)

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

        self.run_command_list(cmds)

    def zero_raid_sub_dev(self):
        raid_cmd = self.get_cmd()
        if self.get_sub_dev_cnt() == 0:
            return

        devs = ' '.join(self.get_sub_dev_list())
        cmds = [' '.join([raid_cmd, '--zero-superblock',
                          '--force', devs])]
        self.run_command_list(cmds)


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
        self.run_command_list(cmds)

        if not self.get_sys_name():
            return

        cmd_change = ''.join(['echo ', str(self.get_stripe_cache_size()),
                              ' > /sys/block/', self.get_sys_name(),
                              '/md/stripe_cache_size'])
        cmds =  [cmd_change]
        print cmd_change
        self.run_command_list(cmds)

    def assemble_raid(self):
        raid_cmd = self.get_cmd()
        devs = ' '.join(self.get_sub_dev_list())
        cmds = [' '.join([raid_cmd, '-A', self.get_raid_path(), devs])]
        self.run_command_list(cmds)

    def show_raid_info(self):
        if not self.get_sys_name():
            return

        cmds = ['cat /proc/mdstat',
                ''.join(['cat /sys/block/', self.get_sys_name(),
                         '/md/stripe_cache_size']),
                'cat /proc/modules | grep raid456']
        self.run_command_list(cmds)

def test_create_remove_raid(raid_util, bdevs):
    sub_dev_list = []
    for bdev in bdevs:
        path = '/dev/' + bdev
        sub_dev_list.append(path)

    raid_util.set_sub_dev_list(sub_dev_list)
    raid_util.zero_raid_sub_dev()
    raid_util.create_raid()
    raid_util.show_raid_info()
    raid_util.remove_raid()


def test_hba_raid():
    hba = HBA('mv64xx')
    hba.get_bdev()
    hba.print_bdev_list()

#    raid_util = Raid_Util('/root/src/mdadm_ext/', '/root/src/md_ext/')
    raid_util = Raid_Util('/sbin/', None)
    raid_util.set_raid_txn(False)
    raid_util.init_raid()
    raid_util.set_raid_level(6)
    raid_util.set_raid_name('raid')
    raid_util.set_cmd_args('--assume-clean -e1.0')
    raid_util.set_raid_sub_dev_size_KB(100 * 1024 * 1024)

    for i in range(1, 17):
        bdevs = hba.get_bdev_balanced(i)
        if len(bdevs):
            print bdevs
        test_create_remove_raid(raid_util, bdevs)

    raid_util.exit_raid()

test_hba_raid()
