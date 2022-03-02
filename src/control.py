class Stop():
    def __init__(self, status=False):
        self._status = status
    
    @property
    def status(self):
        return self._status
    
    def turn(self):
        self._status = True

    def __repr__(self) -> str:
        return str(self._status)

class Offline(Stop):
    def change(self, new_stat):
        if type(new_stat) != bool:
            print(TypeError("status must be boolean"))
        else:
            self._status = new_stat
