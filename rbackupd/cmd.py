import subprocess


def remove_symlink(path):
    # to remove a symlink, we have to strip the trailing
    # slash from the path
    args = ["rm", path.rstrip("/")]
    subprocess.check_call(args)


def create_symlink(target, linkname):
    args = ["ln", "-s", "-r", target, linkname]
    subprocess.check_call(args)


def move(path, target):
    args = ["mv", path, target]
    subprocess.check_call(args)


def remove_recursive(path):
    args = ["rm", "-r", "-f", path]
    subprocess.check_call(args)


def copy_hardlinks(path, target):
    # we could alternatively use rsync with destination
    # being the same as link-dest, this would create
    # only hardlinks, too
    args = ["cp", "-a", "-l", path, target]
    subprocess.check_call(args)
