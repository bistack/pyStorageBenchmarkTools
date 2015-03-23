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

def cleanup_dev(dev):
    cmd = ''.join(['dd if=/dev/zero of=', dev, ' bs=1M count=100'])
    cmds = [cmd]
    run_command_list(cmds)

def exit_asd():
    cmds = ['modprobe -r asd_map_module',
            'modprobe -r asd_driver',
            'modprobe -r asd_deadline'
            ]
    run_command_list(cmds)

def create_asdpool(dev, plname):
    cmd = ' '.join(['asdpoolcreate -n', plname, '-d', dev])
    cmds = [cmd]
    (status, _) = run_command_list(cmds)
    return status

def remove_asdpool(plname):
    cmds = [' '.join(['asdpoolchange -a n', plname]),
            ' '.join(['asdpoolremove -f', plname])
            ]
    (status, _) = run_command_list(cmds)
    return status

def create_asd(pool, name, size):
    asd_name = 'asd_' + name
    cmd = ' '.join(['asdcreate -n', asd_name, '-L', size, pool])
    cmds = [cmd]
    (err, _) = run_command_list(cmds)
    if not err:
        return '/dev/' + name
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

def init_sd():
    cmds = ['sdload']
    (status, _) = run_command_list(cmds)
    return status

def exit_sd():
    cmds = ['sdunload']
    (status, _) = run_command_list(cmds)
    return status
    
def create_sd(asd1, asd2):
    sd_og = 'sd_' + asd1
    sd_ro = 'sd_' + asd2
    cmds = [' '.join(['sdcreate -n', sd_og, '-t orig', '-d', asd1]),
            ' '.join(['sdcreate -n', sd_ro, '-t sdro', '-d', asd2,
                      '-o', sd_og])
            ]
    (err, _) = run_command_list(cmds)
    if not err:
        return '/dev/'+sd_og, '/dev/' + sd_ro

    return None

def remove_sd(sd_og, sd_ro):
    cmds = [' '.join(['sdremove -n', sd_ro]),
            ' '.join(['sdremove -n', sd_og])
            ]
    (status, _) = run_command_list(cmds)
    return status

def assemble_all_sd():
    cmds = ['sdrebuild']
    (status, _) = run_command_list(cmds)
    return status

def init_cbd():
    cmds = ['modprobe bwtrace',
            'modprobe cbd',
            ]
    (status, _) = run_command_list(cmds)
    return status
    
def exit_cbd():
    cmds = ['modprobe -r buddy',
            'modprobe -r vlru',
            'modprobe -r cbd',
            'modprobe -r bwtrace'
            ]
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
        status = remove_cbd(plname, name)
        status = remove_cbdpool(plname)

    return status
