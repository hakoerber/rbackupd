#!/usr/bin/env python

import sys
import rbackupd.cmd as cmd
import rbackupd.remote.ssh as ssh
import rbackupd.remote.path as rpath
import rbackupd.remote.host as rhost
import functools
import time

#exists = cmd.exists('/home/hannes')
    #rpath.Path(path='/home/hannes')) #,
               #connection_parameters=ssh.ConnectionParameters(
               #    host=rhost.Host(ip='127.0.0.1') #, #'10.11.11.190'),
               #    #port=34784,
               #    #user='pi',
               #    #identity_file='/home/hannes/.ssh/id_rsa')))
               #)))

def timing(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        ret = func(*args, **kwargs)
        end = time.time()
        print("function %s took %0.03f ms" % (func.__name__, (end - start) * 1000))
        return ret
    return wrapper

connparm = ssh.ConnectionParameters(
    host=rhost.Host('10.11.11.190'),
    port=34784,
    user='pi',
    identity_file='/home/hannes/.ssh/id_rsa')


print(cmd.samefile(rpath.Path(path="/home/pi/",
                              connection_parameters=connparm),
                   "/var/log/auth.log"))
sys.exit(0)

@timing
def exists(*args, **kwargs):
    return cmd.exists(*args, **kwargs)

ret = exists(
    rpath.Path(path='/home/hannes',
               connection_parameters=connparm))
print(ret)

time.sleep(1)
ret = exists(
    rpath.Path(path='/home/pi',
               connection_parameters=connparm))
print(ret)

time.sleep(10)
ret = exists(
    rpath.Path(path='/etc/localtime',
               connection_parameters=connparm))
print(ret)

time.sleep(65)
ret = exists(
    rpath.Path(path='/etc/lel',
               connection_parameters=connparm))
print(ret)
