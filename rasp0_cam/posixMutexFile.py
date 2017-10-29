import os, fcntl

class mutexfile:
    def __init__(self, filename):
        if os.access(filename, os.F_OK):
            self.filename = filename
            self.fd = None
        else:
            errmssg = filename + " does not exist. Can't lock non-existent file."
            raise IOError, errmssg

    def __del__(self):
        try:
            self.unlock()
        except:
            pass
        try:
            self.f.close()
        except:
            pass

    def getReadLock(self):
        self.f = open(self.filename, 'r')
        self.fd = self.f.fileno()
        fcntl.lockf(self.fd, fcntl.LOCK_SH)


    def getWriteLock(self):
        self.f = open(self.filename, 'r+')
        self.fd = self.f.fileno()
        fcntl.lockf(self.fd, fcntl.LOCK_EX)


    def unlock(self):
        fcntl.lockf(self.fd, fcntl.LOCK_UN)
        self.f.close()
        self.fd = None

    def flock(self, flag):
        '''flags are:
        LOCK_UN - unlock
        LOCK_SH - acquire a shared (or read) lock
        LOCK_EX - acquire an exclusive (or write) lock
        '''
        if flag == 'LOCK_SH':
            self.getReadLock()
        elif flag == 'LOCK_EX':
            self.getWriteLock()
        elif flag == 'LOCK_UN':
            self.unlock()
        else:
            errmssg = "The flag " + flag + " is not implemented for flock"
            raise NotImplementedError, errmssg