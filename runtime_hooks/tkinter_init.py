import os
import sys

if getattr(sys, "frozen", False):
    application_path = os.path.dirname(sys.executable)
    os.environ["TCL_LIBRARY"] = os.path.join(application_path, "tcl", "tcl8.6")
    os.environ["TK_LIBRARY"] = os.path.join(application_path, "tcl", "tk8.6")
