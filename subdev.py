#!/usr/bin/python

from misc_lib import run_command_list

def init_asd(cleanup = 0):
    cmds = ['modprobe dm-mod',
            'modprobe asd_deadline',
            'modprobe asd_driver',
            'modprobe asd_map_module'
            ]
    if cleanup:
        cmds.append('apremove -a -f')
    run_command_list(cmds)

def exit_asd():
    cmds = ['modprobe -r asd_map_module',
            'modprobe -r asd_driver',
            'modprobe -r asd_deadline',
            'modprobe -r msios'
            ]
    run_command_list(cmds)

def create_asdpool(dev, plname):
    cmd = ' '.join(['asdpoolcreate -n', plname, '-g 16', '-d', dev])
    print cmd
    cmds = [cmd]
    (status, _) = run_command_list(cmds)
    return status

def remove_asdpool(plname):
    cmds = [' '.join(['asdpoolchange -a n', plname]),
            ' '.join(['asdpoolremove -f', plname])
            ]
    (status, _) = run_command_list(cmds)
    return status

def create_asd(pool, asd_name, size_kb):
    cmd = ' '.join(['asdcreate -n', asd_name, '-L', str(size_kb) + 'K', pool])
    cmds = [cmd]
    (err, _) = run_command_list(cmds)
    if not err:
        return asd_name
    return None

def remove_asd(name):
    cmds = [' '.join(['asdchange -a n', name]),
            ' '.join(['asdremove -f', name])
            ]
    (status, _) = run_command_list(cmds)
    return status

def assemble_all_asd():
    cmds = ['modprobe dm-mod',
            'asd_load'
            ]
    (status, _) = run_command_list(cmds)
    return status

def create_multi_asdpool(bdev_names):
    pools = []

    for dev_name in bdev_names:
        plname = 'asd_pool_' + dev_name
        dev_path = '/dev/' + dev_name
        create_asdpool(dev_path, plname)
        pools.append(plname)

    return pools

def remove_multi_asdpool(pools):
    status = 0
    for plname in pools:
        status += remove_asdpool(plname)

    return status

def create_multi_asd(pools, size_kb, vd_name = None):
    asds = []
    for plname in pools:
        dev_name = plname.split('_')[-1]
        if vd_name:
            name = '_'.join([vd_name, 'asd', dev_name])
        else:
            name = '_'.join(['asd', dev_name])
        if create_asd(plname, name, size_kb):
            asds.append(name)

    return asds

def remove_multi_asd(asds):
    status = 0
    for name in asds:
        status += remove_asd(name)

    return status

def init_sd():
    cmds = ['sdload']
    (status, _) = run_command_list(cmds)
    return status

def exit_sd():
    cmds = ['sdunload']
    (status, _) = run_command_list(cmds)
    return status

def cleanup_sd():
    cmds = ['truncate /etc/sd/meta  --size 0']
    (status, _) = run_command_list(cmds)
    return status

def create_sd(sd_name, asd_name, sd_type = 'orig', sd_orig = None):
    asd_path = '/dev/' + asd_name

    if sd_type == 'orig':
        cmds = [' '.join(['sdcreate -n', sd_name, '-t orig', '-d', asd_path])]
    elif sd_type == 'sdro' and sd_orig:
        cmds = [' '.join(['sdcreate -n', sd_name, '-t sdro', '-d', asd_path,
                          '-o', sd_orig])]

    (err, _) = run_command_list(cmds)

    if not err:
        return sd_name

    return None

def remove_sd(sd_name):
    cmds = [' '.join(['sdremove', sd_name])]
    (status, _) = run_command_list(cmds)
    return status

def create_multi_sd(asd_names, sd_type='orig'):
    sds = []
    for asd_name in asd_names:
        name = 'sd_' + asd_name

        sd_orig = None
        if sd_type == 'sdro':
            last = '_'.join(asd_name.split('_')[1:])
            sd_orig = 'sd_rg_' + last

        create_sd(name, asd_name, sd_type, sd_orig)
        sds.append(name)

    return sds

def remove_multi_sd(sd_names):
    for name in sd_names:
        remove_sd(name)

def assemble_all_sd():
    cmds = ['sdrebuild']
    (status, _) = run_command_list(cmds)
    return status

def init_cbd():
    cmds = ['modprobe cbd']
    (status, _) = run_command_list(cmds)
    return status

def exit_cbd():
    cmds = ['modprobe -r buddy',
            'modprobe -r vlru',
            'modprobe -r cbd']
    (status, _) = run_command_list(cmds)
    return status

def create_cbdpool(plname, size_kb):
    block_cnt = size_kb / 4
    cmd = ' '.join(['cbdpoolcreate -n', plname, '-p scap',
                    '-s', str(block_cnt)])
    cmds = [cmd]
    (status, output) = run_command_list(cmds)
    if status:
        print output
    return status

def remove_cbdpool(plname):
    cmd1 = ' '.join(['cbdpooldelete -n', plname])
    cmd2 = ' '.join(['rm -rf', plname])
    cmds = [cmd1, cmd2]
    (status, _) = run_command_list(cmds)
    return status

def create_cbd(plname, cbd_name, dev_path):
    cmd = ' '.join(['cbddevcreate -n', cbd_name, '-p', plname,
                    '-d', dev_path, '-c vlru -a buddy'])
    cmds = [cmd]
    (status, output) = run_command_list(cmds)
    if status:
        print output
    return status

def remove_cbd(plname, name):
    cmd1 = ' '.join(['cbddevdelete -n', name, '-p', plname])
    cmd2 = ' '.join(['rm -rf', '/dev/' + name])
    cmds = [cmd1, cmd2]
    (status, _) = run_command_list(cmds)
    return status

def create_multi_cbd(bdevs):
    size_kb = 64 * 1024
    cbds = []

    for dev_name in bdevs:
        plname = 'cbd_pool_' + dev_name
        dev_path = '/dev/' + dev_name
        name = 'cbd_' + dev_name
        create_cbdpool(plname, size_kb)
        create_cbd(plname, name, dev_path)
        cbds.append(name)

    return cbds

def remove_multi_cbd(cbds):
    status = 0
    for name in cbds:
        last = name.split('_')[-1]
        plname = 'cbd_pool_' + last
        status += remove_cbd(plname, name)
        status += remove_cbdpool(plname)

    return status

def remove_asd_env(pools, asdrgs = None, asdros = None):
    if asdros:
        remove_multi_asd(asdros)
    if asdrgs:
        remove_multi_asd(asdrgs)
    remove_multi_asdpool(pools)
    exit_asd()

def remove_sd_env(sdrgs, sdros = None):
    if sdros:
        remove_multi_sd(sdros)
    if sdrgs:
        remove_multi_sd(sdrgs)
    exit_sd()

def remove_cbd_evn(cbds):
    remove_multi_cbd(cbds)
    exit_cbd()

def create_asd_env(bdevs, size_kb):
    i = len(bdevs)

    init_asd()
    pools = create_multi_asdpool(bdevs)
    print '%d %d: %s' % (len(pools), i, pools)

    if len(pools) < i:
        remove_asd_env(pools)
        return None, None, None

    asdrgs = create_multi_asd(pools, size_kb, 'rg')
    print '%d %d: %s' % (len(asdrgs), i, asdrgs)

    if len(asdrgs) < i:
        remove_asd_env(pools, asdrgs)
        return None, None, None

    asdros = create_multi_asd(pools, size_kb, 'ro')
    print '%d %d: %s' % (len(asdros), i, asdros)

    if len(asdros) < i:
        remove_asd_env(pools, asdrgs, asdros)
        return None, None, None

    return pools, asdrgs, asdros

def create_sd_env(asdrgs, asdros):
    i = len(asdrgs)

    cleanup_sd()
    init_sd()
    sdrgs = create_multi_sd(asdrgs)
    print '%d %d: %s' % (len(sdrgs), i, sdrgs)

    if len(sdrgs) < i:
        remove_sd_env(sdrgs)
        return None, None

    sdros = create_multi_sd(asdros, 'sdro')
    print '%d %d: %s' % (len(sdros), i, sdros)

    if len(sdros) < i:
        remove_sd_env(sdrgs, sdros)
        return None, None

    return sdrgs, sdros

def create_cbd_env(devs):
    i = len(devs)

    init_cbd()
    cbds = create_multi_cbd(devs)
    print '%d %d: %s' % (len(cbds), i, cbds)

    if len(cbds) < i:
        remove_cbd_evn(cbds)
        return None

    return cbds
