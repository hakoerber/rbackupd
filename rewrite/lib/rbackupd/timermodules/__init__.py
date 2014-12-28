from . import cron

modules = {
    "cron": cron.Timer
}

def get_module(name):
    return modules[name]
