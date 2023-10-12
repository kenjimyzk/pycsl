from core.base import Base

class Pycsl:
    def __init__(self):
        self.base = Base("aerj")
        self.base.create()

if __name__=="__main__":
    Pycsl()