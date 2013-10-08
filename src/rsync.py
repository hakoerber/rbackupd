import subprocess

def rsync(cmd, source, destination, link_ref, arguments, rsyncfilter):
    args = [cmd]

    args.extend(rsyncfilter.get_args())

    args.extend(arguments)

    if link_ref is not None:
        args.append("--link-dest=%s" % link_ref)

    args.append(source)
    args.append(destination)

    print(" ".join(args))

    proc = subprocess.Popen(args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    (stdoutdata, stderrdata) = proc.communicate()
    return (proc.returncode, stdoutdata, stderrdata)



class Filter(object):
    def __init__(self, include_patterns, exclude_patterns, include_files, exclude_files, filters):
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns
        self.include_files = include_files
        self.exclude_files = exclude_files
        self.filters = filters

    def get_args(self):
        args = []
        for pattern in self.include_patterns:
            if pattern == "" or pattern is None:
                continue
            args.append("--include=%s" % pattern)

        for pattern in self.exclude_patterns:
            if pattern == "" or pattern is None:
                continue
            args.append("--exclude=%s" % pattern)

        for patternfile in self.include_files:
            if patternfile == "" or patternfile is None:
                continue
            args.append("--include-from=%s" % pattern)

        for patternfile in self.exclude_files:
            if patternfile == "" or patternfile is None:
                continue
            args.append("--exclude-from=%s" % pattern)

        for rfilter in self.filters:
            if rfilter == "" or rfilter is None:
                continue
            args.append("--filter=%s" % rfilter)

        return args
