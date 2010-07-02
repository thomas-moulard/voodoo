"""
This module handles Genom in Python.
It allows locally or remotely:
- Genom initialization and destruction.
- component start/stop

It should wrap transparently all Genom-related activities
and provide a consistant and reentrant API for the user.
"""
import StringIO, logging, os, subprocess

def getGenomPath ():
    """
    Retrieve that location of Genom related software.
    There position is defined by the GENOM_PATH environment variable.
    For convenience, if the variable is not set, the PATH environment variable
    is used instead.

    Caution: this path is forwarded when executing commands remotely.
    Make sure the variable is also valid on the remote hosts.

    >>> getGenomPath () != ""
    True
    """
    res = os.getenv('GENOM_PATH')
    if not res:
        Genom.logger.warning (
            'environment variable GENOM_PATH is not set, fallback to PATH.')
        os.environ['GENOM_PATH'] = os.getenv ('PATH')
        res = os.getenv('GENOM_PATH')
    return res

def launch (prog, stdout = subprocess.PIPE):
    """
    Simplified subprocess.Popen for readibility.

    >>> x = launch ("true")
    """

    if type(stdout) == str:
        stdout = open(stdout, 'w')

    return subprocess.Popen (prog,
                             stdin = subprocess.PIPE,
                             stdout = stdout,
                             stderr = subprocess.STDOUT)

def call (prog, stdout = subprocess.PIPE):
    """
    Simplified subprocess.call for readibility.

    >>> x = call ("true")
    """

    if type(stdout) == str:
        stdout = open(stdout, 'w')

    return subprocess.call (prog,
                            stdin = subprocess.PIPE,
                            stdout = stdout,
                            stderr = subprocess.STDOUT)


def sshLaunch (cmd, stdout = subprocess.PIPE, host="localhost"):
    """
    Use ssh to launch processes remotely.

    >>> x = sshLaunch ("true")
    """
    return launch (["ssh", "-X", host,
                    "sh -c 'PATH=\'%s:$PATH\' %s'"
                    % (getGenomPath (), cmd)],
                   stdout=stdout)

def sshCall (cmd, stdout = subprocess.PIPE, host="localhost"):
    """
    Use ssh to execute a program remotely.

    >>> x = sshCall ("true")
    """
    return call (["ssh", "-X", host,
                  "sh -c 'PATH=\'%s:$PATH\' %s'"
                  % (getGenomPath (), cmd)],
                 stdout=stdout)


def killall (prog, host="localhost"):
    """
    Execute killall shell command.

    >>> x = killall ("true")
    """
    return sshCall ("killall %s" % prog)


def module_ready(component):
    from socket import gethostname
    host = gethostname()
    return os.access(os.getenv("HOME") + "/." + component + ".pid-" + host,
                     os.F_OK)

class Genom:
    """
    This class represents an instance of Genom. It
    should be instantiated once as multiple instances of Genom
    on a single machine are not allowed.

    >>> from time import sleep
    >>> component = "walk"
    >>> g = Genom ()
    >>> g.start ()
    >>> g.start ()
    >>> g.startComponent (component)
    >>> g.startComponent (component)
    >>> sleep (0.33)
    >>> #g.stopComponent (component)
    >>> g.terminate ()
    >>> g.terminate ()
    """

    commands = {
        "h2": "h2",
        "tclserv": "tclserv",
        "killmodule": "killmodule"
        }
    """
    Location of used shell commands.
    Should be changed before using the class if the programs are not
    in the user PATH.
    """

    logger = logging.getLogger('voodoo.genom')

    def __init__ (self):
        """
        Initialize class and create the logger.

        >>> g = Genom ()
        """
        self.started = {}
        self.tclserv = None
        self.components = {}
        pass

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.terminate()
        return self

    def dumpLogs (self):
        """Dump module logs.
        Block if module has not been terminated beforehand."""
        for (name, p) in self.components.iteritems ():
            print "--- " + name + " ---"
            print "STDOUT:"
            print p.stdout.read ()
            print "STDERR:"
            print p.stderr.read ()

    def killmodule (self, component, host="localhost"):
        """
        Kill a genom module. Internal function.

        >>> g = Genom ()
        >>> # g.startComponent ("walk")
        >>> # from time import sleep; sleep (1)
        >>> # g.killmodule ("walk")
        """
        module = component.rsplit ('/', 1)
        if len (module):
            component = module[len (module) - 1]
        self.logger.debug ("killing module %s" % component)
        return sshCall (Genom.commands["killmodule"] + " " + component, host)

    def start (self, host="localhost"):
        """
        Start Genom: initalize through h2 and start tclserv.

        >>> g = Genom ()
        >>> g.start ()
        """
        self.logger.info ("starting genom")

        if self.started.get (host, None) == True:
            self.logger.warning ("skipping as Genom is already started")

        killall (host, "tclserv")

        p = sshLaunch (Genom.commands["h2"] + " init", host)
        p.communicate(input='y\n')
        if (p.wait ()):
            raise Exception ("failed to start h2")

        self.tclserv = sshLaunch (Genom.commands["tclserv"], host)
        if self.tclserv.returncode:
            self.logger.debug (self.tclserv.stdout.read ())
            self.logger.debug (self.tclserv.stderr.read ())
            raise Exception ("failed to start tclserv")
        self.started[host] = True

    def startComponent (self, component, host="localhost"):
        """
        Start Genom component.

        >>> g = Genom ()
        >>> g.start ()
        >>> g.startComponent ("walk")
        """
        killall (component, host)
        self.killmodule (component, host)

        self.logger.info ("starting component %s" % component)

        stdout = "/tmp/%s.log" % component
        p = sshLaunch (component, stdout, host)
        if p.returncode:
            raise Exception ("failed to start component %s (status = %d)" % p.returncode)
        self.components[host + "/" + component] = p

    # FIXME: broken.
    def stopComponent (self, component, host="localhost"):
        """
        Stop Genom component.

        >>> g = Genom ()
        >>> g.start ()
        >>> g.startComponent ("walk")
        >>> # g.stopComponent ("walk")
        """
        self.logger.info ("stopping component %s" % component)
        st = self.killmodule (host + "/" + component)
        if st:
            raise Exception ("failed to stop component %s (status = %d)"
                             % (component, st))
        p = self.components[host + "/" + component]
        if p.returncode:
            p.terminate ()
            p.kill ()
        st = p.wait ()
        if st:
            self.logger.debug (p.stdout.read ())
            self.logger.debug (p.stderr.read ())
            raise Exception ("error while terminating component %s (status = %d)"
                             % (component, st))

    def terminate (self):
        """
        Stop Genom: kill tclserv and call h2 end.

        >>> g = Genom ()
        >>> g.start ()
        >>> g.terminate ()
        """
        self.logger.info ("terminating Genom")
        if self.tclserv:
            self.tclserv.terminate ()
            self.tclserv.kill ()

        p = launch (["h2", "info"])
        if p.wait () != 3:
            p = launch (["h2", "end"])
            if (p.wait ()):
                raise Exception ("Failed to terminate h2")


__all__ = ["Genom", "module_ready"]

if __name__ == "__main__":
    import doctest
    logging.basicConfig (level=logging.DEBUG)
    doctest.testmod (verbose = True)
