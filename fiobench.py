#!/usr/bin/python
'''Filename: fiobench.py
Author: Sun Zhenyuan <sunzhenyuan@163.com> 2015.02.06. '''

import commands
import time
import os
import sys

IOENGINE = 'libaio'

BS = 4 * 1024                      # bytes default 4KB
TESTFILE = 'asu-0'
RAIDCHUNK = 512 * 1024             # bytes
DISK_CACHE_SIZE = 64 * 1024 * 1024 # bytes

def compute_micro_test_size(data_disk_nr, disk_cache_size):
    '''in order to make disk cache impact <= 1% on sequential IO'''
    return disk_cache_size * data_disk_nr * 50

def get_io_block_size_list():
    '''io size from 4KB to 2MB'''
    bslist = []
    io_size = BS
    bslist.append(io_size)
    io_size <<= 4
    bslist.append(io_size)
    io_size <<= 3
    bslist.append(io_size)
    io_size <<= 1
    bslist.append(io_size)

    print bslist
    return bslist

def compute_raid_iodepth(data_disk_nr, raid_chunk_size, io_block_size):
    '''choose between NCQ size and RAID's chunk'''
    if (io_block_size == 0 or raid_chunk_size == 0 or data_disk_nr == 0):
        return 32

    ncq_size = 32 * io_block_size
    if (raid_chunk_size > ncq_size):
        perfect_size = raid_chunk_size
    else:
        perfect_size = (ncq_size / raid_chunk_size) * raid_chunk_size

    stripe_size = data_disk_nr * perfect_size
    return (stripe_size + io_block_size - 1) / io_block_size

def test_compute_raid_iodepth():
    '''unit tet for compute_raid_iodepth'''
    data_nr = 4
    chunk = 512 * 1024
    ioblock = 64 * 1024
    iodepth = compute_raid_iodepth(data_nr, chunk, ioblock)
    if (iodepth != 128):
        print('unit test fail: iodepth' + iodepth + ' ' +
              compute_raid_iodepth.__name__)

def comm_fio_cmd(engine, job_name, io_depth):
    '''common part of fio parameters'''
    return ('fio --direct=1 --ioengine=' + engine + 
            ' --name=' + job_name +
            ' --iodepth=' + str(io_depth) +
            ' --write_iops_log=' + job_name +
            ' --log_avg_msec=' + str(500))

def micro_job_type(rw_type, io_block_size):
    '''job name = rw + _seq_ + io block size'''
    return rw_type + '_seq_' + str(io_block_size)

def file_name(filepath):
    '''get file name without extension'''
    denties = os.path.split(filepath)
    trace = denties[-1]
    parts = trace.split(os.extsep)
    return parts[0]

def file_dir(filepath):
    '''get file dir'''
    denties = os.path.split(filepath)
    return denties[0]

def macro_job_type(trace_file):
    '''use trace file without path as job name'''
    return file_name(trace_file)

def test_macro_job_type():
    '''unit test for macro_job_type'''
    trace_file = '/mnt/trac.spc'
    job_type = macro_job_type(trace_file)
    if (job_type != 'trac'):
        print('unit test fail:' + macro_job_type.__name__ +
              ' job name:' + job_type)

    trace_file = '/mnt/trac'
    job_type = macro_job_type(trace_file)
    if (job_type != 'trac'):
        print('unit test fail:' + macro_job_type.__name__ + 
              'job name:' + job_type)

def micro_fio_cmd(tgt, rw_type, io_block_size, test_size, fio_comm):
    '''a simple io configuration'''
    tgt_name = file_name(tgt)
    tgt_dir = file_dir(tgt) + '/'
    return (fio_comm +
            ' --rw=' + rw_type + ' --size=' + str(test_size) +
            ' --bs=' + str(io_block_size) +
            ' --directory=' + tgt_dir + ' --filename=' + tgt_name)

def macro_fio_cmd(tgt, trace_file, fio_comm):
    '''a trace io configuration'''
    return (fio_comm +
            ' --read_iolog=' + trace_file + ' --replay_no_stall=1' + 
            ' --replay_redirect=' + tgt)

def print_fio_cmd(fio_cmd):
    '''print fio one parameter per line'''
    for line in fio_cmd.split(' '):
        print line

def print_err_info(status, info):
    '''print err info'''
    print 'Err: ' + str(status) + ', ' + info

def fio_cmd_from_file(fio_file):
    '''change a fio config to cmd'''
    (status, fio_cmd) = commands.getstatusoutput('fio --showcmd ' +  fio_file)
    if (status):
        print_err_info(status, fio_cmd)
        return

    print_fio_cmd(fio_cmd)
    return fio_cmd

def store_fio_result(result, rfile):
    '''store fio result to file'''
    if (rfile):
        wfd = file(rfile, 'a')
        wfd.write(result)
        wfd.write('\n')
        wfd.close()

def exec_fio_cmd(fio_cmd, result_file):
    '''execute fio cmd and save result file'''
    print_fio_cmd(fio_cmd)
    store_fio_result(fio_cmd, result_file)
    (status, result) = commands.getstatusoutput(fio_cmd)
    if (status):
        print_err_info(status, result)

    for line in result.split('\n'):
        print line

    store_fio_result(result, result_file)

    os.system('sync')

def result_file_name(tgt, raid_data_nr, job_type):
    '''result file name = target file name + date + job name'''
    tgt_name = file_name(tgt)
    if (os.path.exists('/sys/block/' + tgt_name + '/md/txn')):
        tgt_name = tgt_name + 'T'

    return ('./' + tgt_name + '_' + str(raid_data_nr) + '_' + 
            time.strftime('%Y%m%d_%H%M%S') + 
            '_' + job_type + '.txt')

def micro_test(tgt, io_block_size, rw_type):
    '''fio run micro benchmark'''
    job_type = micro_job_type(rw_type, io_block_size)
    raid_data_nr = md_data_nr(tgt)
    result_file = result_file_name(tgt, raid_data_nr, job_type)
    io_depth = compute_raid_iodepth(raid_data_nr, RAIDCHUNK, io_block_size)
    test_size = compute_micro_test_size(raid_data_nr, DISK_CACHE_SIZE)
    job_name = file_name(result_file)
    fio_comm = comm_fio_cmd(IOENGINE, job_name, io_depth)
    fio_cmd = micro_fio_cmd(tgt, rw_type, io_block_size, test_size, fio_comm)
    exec_fio_cmd(fio_cmd, result_file)

def macro_prepare(tgt, trace_file):
    '''create symbol link for trace target'''
    trace_fd = file(trace_file, 'r')
    line = trace_fd.readline()
    line = trace_fd.readline()
    trace_fd.close()

    items = line.split()

    try:
        if (os.path.lexists(items[0]) and os.path.islink(items[0])):
            os.remove(items[0])
        os.symlink(tgt, items[0])
    except OSError:
        print 'link ' + items[0] + ' error'

def test_macro_prepare():
    '''unit test macro_prepare'''
    test_trace = './fio_web_1.csv'
    test_fd = file(test_trace, 'w')
    test_fd.write('fio version 2 iolog\n')
    test_fd.write('/dev//asu-1 add\n')
    test_fd.write('/dev//asu-1 open\n')
    test_fd.close()
    macro_prepare('/dev/md127', test_trace)
    link = '/dev/asu-1'
    if (os.path.lexists(link) and os.path.islink(link)):
        pass
    else:
        print 'unit test fail: ' + test_macro_prepare.__name__
    os.remove(test_trace)

def macro_test(tgt, trace_file):
    '''fio replay trace benchmark'''
    raid_data_nr = md_data_nr(tgt)
    job_type = macro_job_type(trace_file)
    result_file = result_file_name(tgt, raid_data_nr, job_type)
    io_depth = compute_raid_iodepth(raid_data_nr, RAIDCHUNK, BS)
    macro_prepare(tgt, trace_file)
    job_name = file_name(result_file)
    fio_comm = comm_fio_cmd(IOENGINE, job_name, io_depth)
    fio_cmd = macro_fio_cmd(tgt, trace_file, fio_comm)
    exec_fio_cmd(fio_cmd, result_file)

def unit_test_all():
    '''run all unit test'''
    test_macro_job_type()
    test_compute_raid_iodepth()
    test_macro_prepare()

unit_test_all()

def md_data_nr(tgt_file):
    '''get data disk number of a RAID6'''
    tgt = file_name(tgt_file)
    (status, disk_nr) = commands.getstatusoutput('cat /sys/block/' +
                                                 tgt + '/md/raid_disks')
    if (status):
        print_err_info(status, disk_nr)
        return -1
    
    (status, raid_type) = commands.getstatusoutput('cat /sys/block/' +
                                                   tgt + '/md/level')
    if (status):
        print_err_info(status, raid_type)
        return -1

    print 'md type:' + raid_type + ' disk nr:' + disk_nr

    if raid_type == 'raid6':
        return int(disk_nr) - 2
    elif (raid_type == 'raid5' or raid_type == 'raid4'):
        return int(disk_nr) - 1
    else:
        print 'unkown md type:' + raid_type
        return int(disk_nr)

def all_micro_test(md_dev):
    '''run all micro test, var in io size'''
    for io_size in get_io_block_size_list():
        micro_test(md_dev, io_size, 'write')
        micro_test(md_dev, io_size, 'read')

def micro_read_test(md_dev):
    '''run all micro read test, var in io size'''
    for io_size in get_io_block_size_list():
        micro_test(md_dev, io_size, 'read')

def micro_write_test(md_dev):
    '''run all micro test, var in io size'''
    for io_size in get_io_block_size_list():
        micro_test(md_dev, io_size, 'write')

def get_file_list(trace_dir):
    '''files in a dir'''
    (status, all_traces) = commands.getstatusoutput('ls ' + trace_dir)
    if (status):
        print_err_info(status, all_traces)
        return
    
    return all_traces.split()

def initialize_target(tgt, size_gb):
    '''write zero to initialize a alloc-on-write disk for read test'''
    test_size = str(size_gb) + 'G'
    raid_data_nr = md_data_nr(tgt)
    io_block_size = 1024 * 1024 # 1MB
    io_depth = compute_raid_iodepth(raid_data_nr, RAIDCHUNK, io_block_size)
    fio_comm = comm_fio_cmd(IOENGINE, 'init_target', io_depth)
    fio_cmd = micro_fio_cmd(tgt, 'write', io_block_size, test_size, fio_comm)
    exec_fio_cmd(fio_cmd, None)

def all_macro_test(md_dev, trace_dir):
    '''run all macro test, var in io size'''
    traces = get_file_list(trace_dir)

    if (traces):
        for itrace in traces:
            macro_test(md_dev, trace_dir + itrace)

def all_test():
    '''run all micro and macro test, var in io size'''
    for i in sys.argv:
        print "arg: " + i

    sys_arg_cnt = len(sys.argv)

    if (sys_arg_cnt < 3):
        print 'need a dev file and test type'
        return -1

    md_dev = sys.argv[1]
    test_type = sys.argv[2]

    if (file_name(sys.argv[0]) != 'fiobench'):
        return

    if (test_type == 'micro' or test_type == 'all'):
        all_micro_test(md_dev)

    if (test_type == 'read'):
        micro_read_test(md_dev)
        return

    if (test_type == 'write'):
        micro_write_test(md_dev)
        return

    if (test_type == 'micro'):
        return

    if (test_type != 'macro' and test_type != 'all'):
        return

    if (sys_arg_cnt >= 4):
        trace_dir = sys.argv[3]
    else:
        trace_dir = '/root/trace/chosentrace/'

    if (sys_arg_cnt >= 5):
        if (sys.argv[4] == 'ninit'):
            pass
    else:
        initialize_target(md_dev, 403)

    all_macro_test(md_dev, trace_dir)

all_test()
