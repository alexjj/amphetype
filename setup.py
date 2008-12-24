
import glob
import matplotlib
from distutils.core import setup
import py2exe

setup(
      windows=[{"script" : "Amphetype.py"}],
        options={"py2exe" :
            {"includes" : ["sip"],
             "packages": ['matplotlib','pytz'],
            "excludes": ['_gtkagg', '_tkagg'],
            "dll_excludes":['libgdk-win32-2.0-0.dll','libgobject-2.0-0.dll', "libgdk_pixbuf-2.0-0.dll"]}},
        data_files=matplotlib.get_py2exe_datafiles()

    )

