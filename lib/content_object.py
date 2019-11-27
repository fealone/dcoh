class ContentObject(object):

    def read(self):
        raise NotImplementedError

    def size(self):
        raise NotImplementedError
