from configparser import ConfigParser

class Config():
    def __init__(self, files, storages, version):
        self.files = files
        self.storages = storages
        self.version = version

    @classmethod
    def parse(cls, path):
        conf = ConfigParser()
        conf.read(path)
        files = []
        for _, path in conf.items('SOURCES'):
            for i in range(len(str(path))-1, 0, -1):
                if str(path[i]) == '/':
                    files.append((str(path[:i]), str(path[i+1:]))) #list of tuples (key, mask)
                    break
        storages = []
        for _, path in conf.items('SYSTEM'):
            storages.append(path)
        version = conf.get('INFO', 'version')
        return cls(files, storages, version)

config = Config.parse('etc/config.ini')




