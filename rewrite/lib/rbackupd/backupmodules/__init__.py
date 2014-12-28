from . import rsync

modules = {
    "rsync": rsync.BackupCreator
}

def get_module(name):
    return modules[name]
