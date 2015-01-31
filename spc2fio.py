#!/usr/bin/python
# Filename: spc2fio.py
# Author: Sun Zhenyuan <sunzhenyuan@163.com> 2014.12.17

# FIO trace like this '/dev//md127 write 165363359744 4096'
# device_file_path read_write LBA_address_bytes size_bytes

# SPC trace like this '0,20941264,8192,W,0.551706,Alpha/NT'
# ASU_id LBA_address_bytes size_bytes read_write timestamp_seconds optimal_field

# CVS trace
# Timestamp,Hostname,DiskNumber,Type,Offset,Size,ResponseTime

########### how it run:
# 1st, I will translate ASU_id in SPC to /dev//asu_id in a FIO trace file.
# 2nd, Need a Dictionary: asu_id -> real_tested_dev_file_path

# do your self:
# 3rd, create symbalic link. ln -s real_tested_dev_file_path /dev/asu_id 
# 4th, run fio to replay trace

########## Note:
# after trace translated, 
# we should print the max accessed address of each ASU

########## Design:
# 1. a trace is composed by footmarks. so, we create a Class Footmark
# 2. a Class Trace, to record Max of footmark, to write trace to file

import string
import sys

class Footmark:
    def getAsuId(self):
        return self.asuid

    def setAsuId(self, asuid):
        self.asuid = asuid

    def getAddr(self):
        return self.addr

    def setAddr(self, addr):
        self.addr = addr

    def getSize(self):
        return self.size

    def setSize(self, size):
        self.size = size

    def getOp(self):
        return self.op

    def setOp(self, op):
        self.op = op
    
    def getTime(self):
        return self.time

    def setTime(self, time):
        self.time = time

    def toSpcString(self):
        if self.op == "write":
            op = "w"
        else:
            op = "r"

        return self.asuid + "," + self.addr + "," + self.size + "," + op \
            + "," + self.time

    def toFioString(self):
        return "/dev//asu-" + self.asuid + " " + self.op + " " + self.addr \
            + " " + self.size

    def setBySpc(self, spcstr):
        mylist = spcstr.split(",")

        self.asuid = mylist[0]
        self.addr = mylist[1]
        self.size = mylist[2]

        if mylist[3] == "w":
            self.op = "write"
        else:
            self.op = "read"

        self.time = mylist[4]
        
    def setByFio(self, fiostr):
        mylist = fiostr.split()

        self.asuid = mylist[0]
        self.addr = mylist[1]
        self.size = mylist[2]
        self.op = mylist[3]
        self.time = mylist[4]

    def setByCsv(self, csvstr):
        mylist = csvstr.split(',')
        
        self.asuid = mylist[2]
        if mylist[3] == "Write":
            self.op = "write"
        else:
            self.op = "read"
        self.addr = mylist[4]
        self.size = mylist[5]

class Trace:
    def __init__(self):
        self.dict = {}

    def getMaxFootmark(self, asuid):
        if not self.dict.has_key(asuid):
            return -1
        return long(self.dict[asuid])

    def setMaxFootmark(self, asuid, addr, size):
        value = self.getMaxFootmark(asuid)
        new = long(addr) + long(size)
        if value < new:
            self.dict[asuid] = new
        return value

def checkArgument(srctrace, srctype):
    if not len(srctrace) or not len(srctype):
        print('not invalid trace')
        quit()

    if srctype != 'spc' and srctype != 'csv':
        print('wrong trace type: ' + srctype)
        quit()

def translateTrace(srctrace, tgttrace, srctype):
    src = file(srctrace, 'r')
    tgt = file(tgttrace, 'w')

    ft = Footmark()
    trace = Trace()

    tgt.write('fio version 2 iolog\n')
    line = src.readline()

    while len(line) > 0:
        if srctype == "spc":
            ft.setBySpc(line)
        else:
            ft.setByCsv(line)

        v = trace.setMaxFootmark(ft.asuid, ft.addr, ft.size)

        if v < 0:
            tgt.write('/dev//asu-' + ft.getAsuId() + ' add\n')
            tgt.write('/dev//asu-' + ft.getAsuId() + ' open\n')

        if long(ft.getSize()) & ((1 << 12) - 1):
            line = src.readline()
            continue

        tgt.write(ft.toFioString())
        tgt.write('\n')

        line = src.readline()

    for key in trace.dict:
        tgt.write('/dev//asu-' + key + ' close\n')

    src.close()
    tgt.close()
    
    print(srctrace)
    print(trace.dict)


def iteractiveTrans():
    srctrace = raw_input('input trace file:')
    srctype = raw_input('input trace type(spc csv):')
    tgttrace = raw_input('output FIO trace:')

    if not len(tgttrace):
        tgttrace="./fiotrace/fio_" + srctrace

    checkArgument(srctrace, srctype)
    translateTrace(srctrace, tgttrace, srctype);

def batchTrans():
    if len(sys.argv) != 3:
        for i in sys.argv:
            print i
        print "arguments: need 'a srctrace file' and 'srctype: cvs spc'"
        quit()

    srctrace = sys.argv[1]
    srctype = sys.argv[2]
    tgttrace = "./fiotrace/fio_" + srctrace
    checkArgument(srctrace, srctype)
    translateTrace(srctrace, tgttrace, srctype);

if len(sys.argv) > 1:
    batchTrans()
else:
    iteractiveTrans()

