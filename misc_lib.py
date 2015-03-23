#!/usr/bin/python

import commands

def run_command_list(cmds):
    (status, output) = (None, None)
    for cmd in cmds:
        (status, output) = commands.getstatusoutput(cmd)
        if status:
            print 'Err: %d, %s' % (status, output)
            break
    return status, output
