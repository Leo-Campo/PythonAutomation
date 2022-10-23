from pathlib import Path
import shutil
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import os
import settings

logging.basicConfig(
    filename="WatcherLog.log",
    format="%(asctime)s %(name)-12s %(levelname)-4s %(message)s",
    filemode="w",
    level=logging.DEBUG,
)
watcher_to_console = logging.StreamHandler()
watcher_to_console.setLevel(logging.INFO)
watcher_to_console.setFormatter(
    logging.Formatter("%(name)-12s %(levelname)-4s %(message)s")
)
logging.getLogger("").addHandler(watcher_to_console)
logger = logging.getLogger("downloadwatcher")


class Watcher:
    DIRECTORY_TO_WATCH = Path.home() / "Downloads"

    def __init__(self):
        self.observer = Observer()

    def run(self):
        logger.debug(f"Watcher running on {self.DIRECTORY_TO_WATCH}")

        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            logger.debug("Watcher Stopped")

        self.observer.join()


class Handler(FileSystemEventHandler):
    @staticmethod
    def wait_for_file_to_finish_downloading(source_path):
        historical_size = -1
        actual_size = 0
        while historical_size != actual_size:
            try:
                historical_size = os.path.getsize(source_path)
                logger.debug(
                    f"Waiting for file to finish download. Current size: {historical_size}"
                )
                actual_size = os.path.getsize(source_path)
                time.sleep(1)
            except FileNotFoundError:
                actual_size = 0
                # logger.debug(f"File not yet downloaded")
                continue
        logger.debug(f"File is complete. Total size {actual_size}. Moving.")

    @staticmethod
    def select_destination_dir(file_path):
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
        filename = file_path.name
        if len(filename) == 0 or filename is None:
            logger.debug(f"File path given has no filename: {file_path}")
            return None
        extension = filename.split(".")[-1].lower()
        return settings.EXTENSION_DIRECTORY_MAP.get(extension, None)

    @staticmethod
    def on_created(event):
        if event.is_directory:
            return None

        logger.debug(f"Received {event.event_type} event {event.src_path}.")

        if not ".tmp" in event.src_path:
            Handler.wait_for_file_to_finish_downloading(event.src_path)
            destination_folder = Handler.select_destination_dir(event.src_path)
            if destination_folder is None:
                logger.warning(f"Unsupported file extension: {event.src_path}")
                return
            shutil.move(Path(event.src_path), Path(Path.home(), destination_folder))
            logger.info(
                f"{event.src_path} recognized and moved to {destination_folder}"
            )
        else:
            logger.info(f"{event.src_path} recognized but not moved")


if __name__ == "__main__":
    w = Watcher()
    w.run()
