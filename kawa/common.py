import os


VCS_DIRNAMES = (".git", ".hg")


def find_vc_root(filename, max_iterations=5):
    """Given the filename of a Python module, find its version control root.

    Parameters:
      filename(str)
      max_iterations(int)

    Raises:
      ValueError: If no vc root can be found.

    Returns:
      str
    """
    current_dir = os.path.dirname(filename)
    while True:
        files = os.listdir(current_dir)
        for dirname in VCS_DIRNAMES:
            if dirname in files:
                return current_dir

        current_dir = os.path.dirname(current_dir)
        max_iterations -= 1
        if max_iterations == 0:
            raise ValueError("Could not find version control root.")


def find_qualified_name(filename, max_iterations=5):
    """Given the filename of a Python module, find its fully qualified
    module name.

    Parameters:
      filename(str)
      max_iterations(int)

    Raises:
      ValueError: If no vc root can be found.

    Returns:
      str
    """
    filename = os.path.abspath(filename)
    vc_root = find_vc_root(filename, max_iterations)
    _, name = filename.split(f"{vc_root}/")
    if name.endswith(".py"):
        name = name[:-3]
    return name.replace("/", ".")
