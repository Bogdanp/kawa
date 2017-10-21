class Reader:
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, "r")

    def read(self, count):
        """Reads "count" bytes from the current file.
        """
        raise NotImplementedError


def read(filename, count):
    """Read "count" bytes from "filename".
    """
    return Reader(filename).read(count)


content = read("example", 10)
