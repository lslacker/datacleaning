import logging
from logging import FileHandler, StreamHandler

default_formatter = logging.Formatter("""%(module)s %(funcName)s -
%(filename)s - line:%(lineno)s - %(levelname)s:
%(message)s
""")

console_handler = StreamHandler()
console_handler.setFormatter(default_formatter)

error_handler = FileHandler("error.log", "a")
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(default_formatter)

root = logging.getLogger()
root.addHandler(console_handler)
root.addHandler(error_handler)
root.setLevel(logging.INFO)

def getlogger():
    return root