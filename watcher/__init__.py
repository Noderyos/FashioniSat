import os
from datetime import datetime

from common.logger import Logger
from config_loader import config

LOG_FOLDER = os.path.abspath(os.path.join(config.DATA_FOLDER, "logs"))
date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

LOGGER = Logger(file=os.path.join(LOG_FOLDER, f"watcher_{date_str}.log"))
