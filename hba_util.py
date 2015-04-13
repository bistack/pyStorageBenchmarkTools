#!/usr/bin/python
from commands import getstatusoutput
from misc_lib import run_command_list

class HBA:
    def __init__(self, name = None):
        self.sys_name = name
        self.tested = 0
        self.bdev_list_dir = {}

    def test_bdev(self):
        if not len(self.bdev_list_dir):
            return

        for (_, bdev_list) in self.bdev_list_dir.items():
            i = 0

            while i < len(bdev_list):
                bdev = bdev_list[i]
                cmd = ' '.join(['swapon -s | grep', bdev])
                (status, info) = getstatusoutput(cmd)
                if not status or len(info):
                    print 'it used as swap: %s' % (bdev)
                    del bdev_list[i]
                    continue

                cmd = ' '.join(['mount', '|', 'grep', bdev])
                (status, _) = getstatusoutput(cmd)
                if status: # not mounted
                    cmd = ' '.join(['cat /proc/partitions',
                                    '|', 'grep', bdev, '|', 'wc -l'])
                    (status, info) = getstatusoutput(cmd)

                    if status or (int(info) > 1):
                        print 'it has partiations: %s' % (bdev)
                        del bdev_list[i]
                        continue

                    cmd = ' '.join(['dd if=/dev/zero of=/dev/' + bdev,
                                    'bs=1M count=100 oflag=direct 2>&1',
                                    '|', 'grep MB'])
                    (status, _) = getstatusoutput(cmd)
                    if status:
                        print 'cannot write: %s' % (bdev)
                        del bdev_list[i]
                        continue

                    i += 1
                else:
                    print 'it mounted: %s' % (bdev)
                    del bdev_list[i]

            print 'find %s' % (bdev_list)
        self.tested = 1

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

        if not self.tested:
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
        hba_cnt = len(self.bdev_list_dir)
        avg = cnt / hba_cnt
        rem = cnt % hba_cnt

        for i in range(0, avg):
            for (_, bdev_list) in self.bdev_list_dir.items():
                if i < len(bdev_list):
                    chose_list.append(bdev_list[i])
        
        for i in range(avg, avg + rem):
            for (_, bdev_list) in self.bdev_list_dir.items():
                if len(bdev_list) <= i:
                    continue

                chose_list.append(bdev_list[i])

        if len(chose_list) < cnt:
            print 'need %d bdevs' % (cnt)
            self.print_bdev_list()

        return chose_list

    def find_hba_name(self):
        hba_names = ['mv64xx', 'mptspi']
        for hba in hba_names:
            base = '/sys/bus/pci/drivers/'
            cmd = ' '.join(['ls', base, '|', 'grep', hba])
            (status, output) = getstatusoutput(cmd)

            if status or not len(output):
                continue
            else:
                self.sys_name = hba
                return self.sys_name

    def cleanup_dev_list(self, bdevs):
        for dev_name in bdevs:
            dev_path = '/dev/' + dev_name
            self.__cleanup_dev(dev_path)

    def cleanup_all_dev(self):
        if not len(self.bdev_list_dir):
            return

        for _, bdevs in self.bdev_list_dir.items():
            for dev_name in bdevs:
                dev_path = '/dev/' + dev_name
                self.__cleanup_dev(dev_path)

    def __cleanup_dev(self, dev):
        print 'clean %s' % (dev)
        cmd = ''.join(['dd if=/dev/zero of=', dev, ' bs=1M count=100'])
        cmds = [cmd]
        run_command_list(cmds)
