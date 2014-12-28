import datetime
import logging

logger = logging.getLogger(__name__)

class Task(object):
    def __init__(self,
                 name,
                 backupmodule,
                 storagemodule,
                 sources,
                 timers):
        self._backupmodule = backupmodule
        self._storagemodule = storagemodule
        self._name = name
        self._sources=sources
        self._timers = timers

        self._initialize_timers()

    def _initialize_timers(self):
        for timer in self._timers:
            logger.debug(
                "Subscribing task \"%s\" to timer \"%s\".",
                self._name,
                timer.get_name())

            timer.subscribe(self._on_timer)
            logger.debug("Starting timer \"%s\".", timer.get_name())
            timer.start()

    def _on_timer(self, *args, **kwargs):
        timer = args[0]
        timestamp = datetime.datetime.now()
        logger.debug("Received trigger from timer \"%s\".", timer.get_name())
        self._create_backup(timer, timestamp)

    def _create_backup(self, timer, timestamp):
        logger.debug(
            "Triggering new backup creation with module \"%s\".",
            self._backupmodule.get_name())
        self._backupmodule.create(
            sources=self._sources,
            storage=self._storagemodule,
            name=self._get_backup_name(timer, timestamp),
            metadata={"timer": timer, "timestamp": timestamp})

    def _get_backup_name(self, timer, timestamp):
        return "{0}_{1}_{2}".format(
            self._name,
            str(timestamp),
            timer.get_name())
