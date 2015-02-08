#!/usr/bin/python
'''Filename: fiobench.py
Author: Sun Zhenyuan <sunzhenyuan@163.com> 2015.02.06. '''

import commands
import time
import os
import sys

IOENGINE = 'libaio'
TEST_SIZE = '8GB'

RW = 'write'
BS = 4 * 1024 # default 4KB
TESTFILE = 'asu-0'
RAIDCHUNK = 512 * 1024

def get_io_block_size_list():
    '''io size from 4KB to 2MB'''
    bslist = []
    io_size = BS
    for _ in range(0, 10):
        bslist.append(io_size)
        io_size = io_size << 1
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
        print 'iodepth' + iodepth

def comm_fio_cmd(engine, job_name, io_depth):
    '''common part of fio parameters'''
    return ('fio --direct=1 --ioengine=' + engine + 
            ' --name=' + job_name +
            ' --iodepth=' + str(io_depth))

def micro_job_name(rw_type, io_block_size):
    '''job name = rw + io block size'''
    return rw_type + str(io_block_size)

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

def macro_job_name(trace_file):
    '''use trace file without path as job name'''
    return file_name(trace_file)

def test_macro_job_name():
    '''unit test for macro_job_name'''
    trace_file = '/mnt/trac.spc'
    job_name = macro_job_name(trace_file)
    if (job_name != 'trac'):
        print 'job name:' + job_name

    trace_file = '/mnt/trac'
    job_name = macro_job_name(trace_file)
    if (job_name != 'trac'):
        print 'job name:' + job_name

def micro_fio_cmd(tgt, rw_type, io_block_size, io_depth):
    '''a simple io configuration'''
    job_name = micro_job_name(rw_type, io_block_size)
    tgt_name = file_name(tgt)
    tgt_dir = file_dir(tgt) + '/'
    return (comm_fio_cmd(IOENGINE, job_name, io_depth) +
            ' --rw=' + rw_type + ' --size=' + TEST_SIZE +
            ' --bs=' + str(io_block_size) +
            ' --directory=' + tgt_dir + ' --filename=' + tgt_name)

def macro_fio_cmd(tgt, trace_file, io_depth):
    '''a trace io configuration'''
    job_name = trace_file
    return (comm_fio_cmd(IOENGINE, job_name, io_depth) +
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
    wfd = file(rfile, 'w')
    wfd.write(result)
    wfd.write('\n')
    wfd.close()

def exec_fio_cmd(fio_cmd, result_file):
    '''execute fio cmd and save result file'''
    print_fio_cmd(fio_cmd)
    (status, result) = commands.getstatusoutput(fio_cmd)
    if (status):
        print_err_info(status, result)

    for line in result.split('\n'):
        print line

    store_fio_result(result, result_file)

    os.system('sync')

def result_file_name(tgt, job_name):
    '''result file name = target file name + date + job name'''
    tgt_name = file_name(tgt)
    data_nr = md_data_nr(tgt)
    return ('./' + tgt_name + '_' + str(data_nr) + '_' + 
            time.strftime('%Y%m%d%H%M%S') + 
            '_' + job_name + '.txt')

def micro_test(tgt, io_block_size):
    '''fio run micro benchmark'''
    job_name = micro_job_name(RW, io_block_size)
    raid_data_nr = md_data_nr(tgt)
    result_file = result_file_name(tgt + '_' + str(raid_data_nr), job_name)
    io_depth = compute_raid_iodepth(raid_data_nr, RAIDCHUNK, io_block_size)
    fio_cmd = micro_fio_cmd(tgt, RW, io_block_size, io_depth)
    exec_fio_cmd(fio_cmd, result_file)

def macro_test(tgt, trace_file):
    '''fio replay trace benchmark'''
    raid_data_nr = md_data_nr(tgt)
    job_name = macro_job_name(trace_file)
    result_file = result_file_name(tgt + '_' + str(raid_data_nr), job_name)
    io_depth = compute_raid_iodepth(raid_data_nr, RAIDCHUNK, BS)
    fio_cmd = macro_fio_cmd(tgt, trace_file, io_depth)
    exec_fio_cmd(fio_cmd, result_file)

def unit_test_all():
    '''run all unit test'''
    test_macro_job_name()
    test_compute_raid_iodepth()

unit_test_all()

def md_data_nr(tgt_file):
    '''get data disk number of a RAID6'''
    tgt = file_name(tgt_file)
    (status, data_nr) = commands.getstatusoutput('cat /sys/block/' +
                                                 tgt + '/md/raid_disks')
    if (status):
        print_err_info(status, data_nr)
        return -1

    print 'md data nr:' + data_nr
    return int(data_nr) - 2

def all_micro_test():
    '''run all micro test, var in io size'''
    sys_arg_cnt = len(sys.argv)
    if (sys_arg_cnt < 2):
        print 'need a dev file'
        return -1

    md_dev = sys.argv[1]
    
    for io_size in get_io_block_size_list():
        micro_test(md_dev, io_size)

def get_file_list(trace_dir):
    '''files in a dir'''
    (status, all_traces) = commands.getstatusoutput('ls ' + trace_dir)
    if (status):
        print_err_info(status, all_traces)
        return
    
    return all_traces.split()

def all_macro_test():
    '''run all macro test, var in io size'''
    sys_arg_cnt = len(sys.argv)
    if (sys_arg_cnt < 2):
        print 'need a dev file'
        return -1

    md_dev = sys.argv[1]
    trace_dir = '/root/trace/chosentrace/'
    traces = get_file_list(trace_dir)

    if (traces):
        for itrace in traces:
            macro_test(md_dev, trace_dir + itrace)

all_macro_test()