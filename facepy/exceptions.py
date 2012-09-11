# -*- coding: utf-8 -*-


class FacepyError(Exception):
    """Base class for exceptions raised by Facepy."""
    def __init__(self, message, code=None):
        self.code = code

        if self.code:
            message = '[%s] %s' % (self.code, message)

        super(FacepyError, self).__init__(message)
