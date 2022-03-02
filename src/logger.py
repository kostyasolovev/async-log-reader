import logging
import os

filename = 'etc/example.log' 
appendmode = False #False means overwrite mode and True means append
autocreate = True #create log file if it doesnt exist
LOG = None

def init_logger(log_name=None, append=False, autocreate=True, log_level=logging.DEBUG):
    if log_name is not None:
        if not os.path.isfile(log_name):
            if autocreate:
                def create_dir_and_file(file_path):
                    dir = os.path.dirname(file_path)
                    if not os.path.exists(dir):
                        os.makedirs(dir)
                    def create_file(file_path):
                        with open(file_path, 'w') as file:
                            file.close()
                    create_file(file_path)
                create_dir_and_file(log_name)
                logging.debug('program log [{}]has been created'.format(log_name))
            else:
                raise FileNotFoundError("There is not such a file [{}], create it or toggle on 'autocreate' option in logger settings".format(log_name))
        if append: 
            filemode = 'a'
        else:
            filemode = 'w'
        logging.basicConfig(filename=log_name, 
                            filemode=filemode, 
                            level=log_level,
                            format='%(asctime)s [%(levelname)s] [source: %(filename)s] %(message)s')
    console = logging.StreamHandler()
    console.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s [source: %(filename)s]', datefmt='%H:%M:%S')
    console.setFormatter(formatter)
    global LOG
    logging.getLogger('').addHandler(console)
    LOG = logging.getLogger(__name__)

def warning(s):
    LOG.warning(s)
def error(s):
    LOG.error(s)
def debug(s):
    LOG.debug(s)
def critical(s):
    LOG.critical(s)
def fatal(s):
    LOG.fatal(s)
def info(s):
    LOG.info(s)
def exception(s):
    LOG.exception(s)

init_logger(filename, append=appendmode, log_level=logging.WARNING)
