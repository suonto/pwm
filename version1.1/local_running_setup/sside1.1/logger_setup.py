import logging

class LoggerBuilder(object):

    def __init__(self):
        pass

    def build_logger(self, name, logfile=None, debug=False):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG if debug else logging.INFO)
        if logfile != None:
            handler=logging.FileHandler(logfile)
        else:
            handler=logging.StreamHandler()
        formatter=logging.Formatter("[%(asctime)s] %(levelname)-6s  %(name)10s: %(message)s ")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
