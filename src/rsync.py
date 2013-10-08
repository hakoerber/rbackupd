import os
import subprocess


def rsync(cmd, source, destination, link_ref, arguments, rsyncfilter,
          loggingOptions):
    args = [cmd]

    args.extend(rsyncfilter.get_args())

    args.extend(arguments)

    if link_ref is not None:
        args.append("--link-dest=%s" % link_ref)

    print(loggingOptions)
    if loggingOptions is not None:
        args.append("--log-file=%s" % os.path.join(destination,
                                                   loggingOptions.log_name))
        args.append("--log-file-format=%s" % loggingOptions.log_format)

    args.append(source)
    args.append(destination)

    print(" ".join(args))

    # create the directory first, otherwise logging will fail
    os.mkdir(destination)

    proc = subprocess.Popen(args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    (stdoutdata, stderrdata) = proc.communicate()
    return (proc.returncode, stdoutdata, stderrdata)


class LogfileOptions(object):

    def __init__(self, log_name, log_format):
        self.log_name = log_name
        self.log_format = log_format


class Filter(object):

    def __init__(self, include_patterns, exclude_patterns, include_files,
                 exclude_files, filters):
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
