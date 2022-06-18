import importlib.metadata

package_name = "cachedjdk"

try:
    __version__ = importlib.metadata.version(package_name)
except importlib.metadata.PackageNotFoundError:
    __version__ = None
