import sys
from pathlib import Path
root = Path(__file__).parent.parent
sys.path.append(str(root))
import src.logger as logger

logger.init_logger(logger.filename)

logger.warning('Houston, we have a problem')
logger.info('This is Houston. Say again, please')
logger.debug('We ve had a Main B Bus Undervolt')
logger.critical('some big problem!')
logger.fatal('some huge problem!')
logger.debug('new line')
logger.info('extra new line')
