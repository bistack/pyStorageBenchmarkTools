#!/usr/bin/python
'''Filename: fiobench.py
Author: Sun Zhenyuan <sunzhenyuan@163.com> 2015.02.06. '''

import commands
import time
import os

IOENGINE = 'libaio'
TEST_SIZE = '8GB'

RW = 'write'
BS = 4 * 1024 # default 4KB
TESTFILE = 'asu-0'
RAIDCHUNK = 512 * 1024

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
    return rw_type + io_block_size

def file_name(filepath):
    '''get file name without extension'''
    denties = os.path.split(filepath)
    trace = denties[-1]
    parts = trace.split(os.extsep)
    return parts[0]

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
    return (comm_fio_cmd(IOENGINE, job_name, io_depth) +
            ' --rw=' + rw_type + ' --size=' + TEST_SIZE +
            ' --bs=' + io_block_size +
            '--directory=/mnt/ --filename=' + tgt)

def macro_fio_cmd(tgt, trace_file, io_depth):
    '''a trace io configuration'''
    job_name = trace_file
    return (comm_fio_cmd(IOENGINE, job_name, io_depth) +
            ' --read_iolog=' + trace_file + ' --replay_no_stall=1' + 
            ' --replay_redirect=' + tgt)

def fio_cmd_from_file(fio_file):
    '''change a fio config to cmd'''
    fio_cmd = commands.getoutput('fio --showcmd ' +  fio_file)

    for line in fio_cmd.split(' '):
        print line

    return fio_cmd

def store_fio_result(result, rfile):
    '''store fio result to file'''
    wfd = file(rfile, 'w')
    wfd.write(result)
    wfd.close()

def exec_fio_cmd(fio_cmd, result_file):
    '''execute fio cmd and save result file'''
    result = commands.getoutput(fio_cmd)

    for line in result.split('\n'):
        print line

    store_fio_result(result, result_file)

    os.system('sync')

def result_file_name(tgt, job_name):
    '''result file name = target file name + date + job name'''
    tgt_name = file_name(tgt)
    return ('./' + tgt_name + time.strftime('%Y%m%d%H%M%S') + 
            '_' + job_name + '.txt')

def micro_test(tgt, raid_data_nr):
    '''fio run micro benchmark'''
    job_name = micro_job_name(RW, BS)
    result_file = result_file_name(tgt + '_' + raid_data_nr, job_name)
    io_depth = compute_raid_iodepth(raid_data_nr, RAIDCHUNK, BS)
    fio_cmd = micro_fio_cmd(tgt, RW, BS, io_depth)
    exec_fio_cmd(fio_cmd, result_file)

def macro_test(tgt, trace_file):
    '''fio replay trace benchmark'''
    raid_data_nr = 6
    job_name = macro_job_name(trace_file)
    result_file = result_file_name(tgt + '_' + raid_data_nr, job_name)
    io_depth = compute_raid_iodepth(raid_data_nr, RAIDCHUNK, BS)
    fio_cmd = macro_fio_cmd(tgt, trace_file, io_depth)
    exec_fio_cmd(fio_cmd, result_file)

def unit_test_all():
    '''run all unit test'''
    test_macro_job_name()
    test_compute_raid_iodepth()

unit_test_all()

micro_fio_cmd(sys.argv[1], sys.argv[2])
