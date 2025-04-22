from typing import List

class Mount:
    """Represents a mount point for a virtual host."""
    def __init__(self, url_path: str, local_path: str):
        self.url_path = url_path
        self.local_path = local_path

    def __repr__(self):
        return f"Mount(url_path='{self.url_path}', local_path='{self.local_path}')"

class vHost:
    """Represents a virtual host configuration."""
    def __init__(self, name: str, mounts: List[Mount]):
        self.name = name
        self.mounts = mounts

    def __repr__(self):
        return f"vHost(name='{self.name}', mounts={self.mounts})"