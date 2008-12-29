
tag = False
def distance(*args):
    global tag
    if not tag:
        from PyQt4.QtGui import QMessageBox as qmb
        qmb.information(None, "Missing Module", "The py-editdist module is missing!")
        tag = True
    return 0.01
