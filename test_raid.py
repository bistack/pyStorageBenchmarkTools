#!/usr/bin/python

# pdev
# pdev cbd
# pdev asd cbd
# pdev asd sd cbd

from hba_util import HBA
from raid_util import Raid_Util
from subdev import *

def test_create_remove_raid(raid_util, bdevs):
    sub_dev_list = []
    for bdev in bdevs:
        path = '/dev/' + bdev
        sub_dev_list.append(path)

    raid_util.set_sub_dev_list(sub_dev_list)
    raid_util.zero_raid_sub_dev()
    raid_util.create_raid()
    raid_util.show_raid_info()
    raid_util.wait_sync()
    raid_util.fail_one()
    raid_util.add_one()
    raid_util.wait_recovery_time()
    raid_util.remove_raid()

def get_raid_util():
    #raid_util = Raid_Util('/root/src/mdadm_ext/', '/root/src/md_ext/')
    raid_util = Raid_Util('/sbin/', None)
    raid_util.set_raid_txn(False)
    raid_util.init_raid()
    raid_util.set_raid_level(6)
    raid_util.set_raid_name('raid6')
    raid_util.set_cmd_args('-e1.0')
    raid_util.set_raid_sub_dev_size_KB(4 * 1024 * 1024)
    return raid_util

def test_pdev_raid():
    hba = HBA('mv64xx')
    hba.get_bdev()

    raid_util = get_raid_util()

    for i in range(4, 16):
        bdevs = hba.get_bdev_balanced(i)
        if len(bdevs):
            print bdevs
        test_create_remove_raid(raid_util, bdevs)

    raid_util.exit_raid()

#test_pdev_raid()

def test_pdev_cbd_raid():
#    hba = HBA('mv64xx')
    hba = HBA('mptspi')
    hba.get_bdev()

    raid_util = get_raid_util()

    init_cbd()

    for i in range(4, 16):
        bdevs = hba.get_bdev_balanced(i)
        if len(bdevs):
            print bdevs

        cbds = create_multi_cbd(bdevs)
        print '%d %d: %s' % (len(cbds), i, cbds)

        if len(cbds) <= i:
            remove_multi_cbd(cbds)
            break
        
        test_create_remove_raid(raid_util, cbds)
        remove_multi_cbd(cbds)

    exit_cbd()

    raid_util.exit_raid()

test_pdev_cbd_raid()
