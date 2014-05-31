# -*- encoding: utf-8 -*-
# Copyright (c) 2014 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

import sys

import dbus


def connect():
    systembus = dbus.SystemBus()
    try:
        daemon = dbus.Interface(
            systembus.get_object('org.rbackupd.daemon',
                                 '/org/rbackupd/daemon'),
            'org.rbackupd.daemon')
    except dbus.exceptions.DBusException:
        print("Could not connect to the daemon.")
        sys.exit(1)
    return daemon


def main(argv):
    daemon = connect()

    if len(argv) < 1:
        print("Please specify an operation")
        print()
        print("list-tasks\t- list all tasks")
        sys.exit()

    command = argv[0]

    if command == "list-tasks":
        for (i, task) in enumerate(daemon.GetTaskNames()):
            print("{i} -\t{task} -\t{status}".format(
                i=i + 1,
                task=task,
                status=daemon.GetTaskStatus(task)))

    elif command == "pause":
        name = argv[1]
        daemon.PauseTask(name)

    elif command == "resume":
        name = argv[1]
        daemon.ResumeTask(name)

    elif command == "stop":
        name = argv[1]
        daemon.StopTask(name)

    elif command == "start":
        name = argv[1]
        daemon.StartTask(name)
