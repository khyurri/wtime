import tkinter
import pathlib
import pickle
import queue
import datetime
import threading
import time
import logging
from enum import StrEnum
from tkinter import font
import time_format


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class State(StrEnum):
    init = "init"
    running = "running"
    stopped = "stopped"


class Timer:
    def __init__(self) -> None:
        self.state = State.init
        self.date_start: datetime.datetime | None = None
        self.date_end: datetime.datetime | None = None

    def start(self) -> None:
        self.state = State.running
        self.date_start = datetime.datetime.now(datetime.UTC)

    def stop(self) -> None:
        self.state = State.stopped
        self.date_end = datetime.datetime.now(datetime.UTC)

    def spent(self) -> datetime.timedelta:
        if self.state != State.stopped:
            raise ValueError("Timer must be stoped")
        return self.date_end - self.date_start

    def __repr__(self) -> str:
        return f"Timer({self.state=}, {self.date_start=}, {self.date_end=})"


def sum_timers(timers: list[Timer]) -> datetime.timedelta:
    return sum([timer.spent() for timer in timers], start=datetime.timedelta(seconds=0))


class TimerHistory:

    def __init__(self, file: pathlib.Path) -> None:
        self.history = []
        self.storage = Storage(file)
        self.history = self.storage.restore()

    def add_timer(self, timer: Timer) -> None:
        self.history.append(timer)
        self.storage.store(self.history)


class Storage:
    def __init__(self, path: pathlib.Path) -> None:
        self.path = path

    def restore[T](self) -> T:
        with open(self.path, "rb") as file:
            return pickle.load(file)

    def store[T](self, timer: T) -> None:
        with open(self.path, "wb") as file:
            pickle.dump(timer, file, pickle.HIGHEST_PROTOCOL)


def pretty_spent_time(time: datetime.datetime) -> str:
    return time_format.format(time.seconds)


def pretty_date(time: datetime.datetime) -> str:
    return time.strftime("%d.%m.%Y")

def pretty_time(time: datetime.datetime) -> str:
    return f"{time.strftime("%H:%M:%S")}"

def time_start(time: datetime.datetime) -> str:
    return f"{time.strftime("%H:%M:%S")}"


class Signal(StrEnum):
    cont = "cont"
    stop = "stop"


class UICurrentTimer:

    TEXT_START = "Start"
    TEXT_STOP = "Stop"

    def __init__(self, root: tkinter.Frame, frame: tkinter.Frame, history: TimerHistory) -> None:
        self.timer: Timer | None = None
        self.timer_thread: threading.Thread | None = None
        self.root = root

        self.timer_history = history

        self.button = tkinter.Button(frame, text=self.TEXT_START, command=self.new_timer)
        self.button.pack(side=tkinter.LEFT, anchor="w", padx=16)

        self.start_label = tkinter.Label(frame, text="00:00")
        self.start_label.pack(side=tkinter.LEFT, anchor="w", padx=16)

        self.current_label = tkinter.Label(frame, text="0")
        self.current_label.pack(side=tkinter.LEFT, anchor="w", padx=16)

        self.queue = queue.Queue()

    def run_timer_until_stop(self):
        logger.warning("Run timer until stop")
        self.init_timer()
        signal = Signal.cont
        while signal == Signal.cont:
            try:
                signal = self.queue.get_nowait()
                logger.warning("Signal received: %s", signal)
            except queue.Empty:
                try:
                    # TODO: Move TKInter manipulations to main thread
                    self.current_label.configure(
                        text=pretty_spent_time(datetime.datetime.now(datetime.UTC) - self.timer.date_start)
                    )
                    time.sleep(0.1)
                except (tkinter.TclError, RuntimeError):
                    logger.warning("Main window was destroyed")
                    break # stopping timer
        logger.warning("Timer thread finished")

    def init_timer(self) -> None:
        logger.warning("Init timer")
        if self.timer is not None:
            raise ValueError("Timer is already running")
        self.timer = Timer()
        self.timer.start()
        self.button.configure(text=self.TEXT_STOP, command=self.deinit_timer)
        self.start_label.configure(text=time_start(self.timer.date_start))

    def deinit_timer(self) -> None:
        if self.timer is None: 
            raise ValueError("Timer is not initialized")
        self.delete_timer_thread()
        self.timer.stop()
        self.timer_history.add_timer(self.timer)
        self.timer = None
        self.button.configure(text=self.TEXT_START, command=self.new_timer)
        self.root.event_generate("<<history_updated>>")

    def deinit(self) -> None:
        try:
            self.deinit_timer()
        except ValueError:
            logger.warning("No timers are running")

    def new_timer(self) -> None:
        logger.info("New timer")
        self.timer_thread = threading.Thread(
            target=self.run_timer_until_stop,
            daemon=True
        )
        self.timer_thread.start()

    def delete_timer_thread(self) -> None:
        logger.warning("Sending signal to stop thread")
        self.queue.put(Signal.stop)
        logger.warning("Signal sent")
        logger.warning("Is queue empty: %s", self.queue.empty())
        logger.warning("Thread stopped")


class UITodayTimers:

    def __init__(self, root: tkinter.Frame, frame: tkinter.Frame, history: TimerHistory) -> None:
        
        self.root = root
        self.frame = frame
        self.timer_frame: tkinter.Frame | None = None
        today_label = tkinter.Label(frame, text="Last day")
        today_label.pack(side=tkinter.TOP, anchor="nw")

        self.timer_history = history
        self.init_history()

    def print_sum_row(self, last_day_timers: list[Timer]) -> None:
        row_frame = tkinter.Frame(self.timer_frame)
        sum_label = tkinter.Label(row_frame, text=str(pretty_spent_time(sum_timers(last_day_timers))), font=font.Font(family="monospaced", size=12))
        sum_label.pack(side=tkinter.LEFT, anchor="w")
        row_frame.pack(side=tkinter.TOP, anchor="w")

    def print_next_day_row(self, timer: Timer) -> None:
        row_frame = tkinter.Frame(self.timer_frame)
        next_day = tkinter.Label(row_frame, text=pretty_date(timer.date_start), font=font.Font(family="monospaced", size=12))
        next_day.pack(side=tkinter.LEFT, anchor="w")
        row_frame.pack(side=tkinter.TOP, anchor="w")

    def init_history(self):
        self.timer_frame = tkinter.Frame(self.frame)
        timer: Timer
        last_day_timers: list[Timer] = []
        day_row_number = 0
        for timer in self.timer_history.history[::-1]:
            
            if len(last_day_timers) > 0:
                last_timer = last_day_timers[-1]
                if last_timer.date_end.date() != timer.date_end.date():
                    self.print_sum_row(last_day_timers)
                    # reinit list of timers with new day
                    last_day_timers = []
                    self.print_next_day_row(timer)
                    day_row_number = 0

            last_day_timers.append(timer)
            day_row_number += 1

            row_frame = tkinter.Frame(self.timer_frame)
            number_label = tkinter.Label(row_frame, text=str(day_row_number), font=font.Font(family="monospaced", size=12))
            number_label.pack(side=tkinter.LEFT, anchor="w")

            time_from_label = tkinter.Label(row_frame, text=pretty_time(timer.date_start), font=font.Font(family="monospaced", size=12))
            time_from_label.pack(side=tkinter.LEFT, anchor="w")
            row_frame.pack(side=tkinter.TOP, anchor="w")

            time_from_label = tkinter.Label(row_frame, text=pretty_time(timer.date_end), font=font.Font(family="monospaced", size=12))
            time_from_label.pack(side=tkinter.LEFT, anchor="w")
            row_frame.pack(side=tkinter.TOP, anchor="w")

            time_from_label = tkinter.Label(row_frame, text=pretty_spent_time(timer.spent()), font=font.Font(family="monospaced", size=12))
            time_from_label.pack(side=tkinter.LEFT, anchor="w")
            row_frame.pack(side=tkinter.TOP, anchor="w")
            
        self.timer_frame.pack()

    def reload(self, *args):
        if self.timer_frame is not None:
            self.timer_frame.destroy()
            self.init_history()


class UI:
    def __init__(self) -> None:
        self.root = tkinter.Tk()
        self.root.geometry("800x600")
        
        self.top_frame = tkinter.Frame(self.root)
        self.top_frame.pack(side=tkinter.TOP, anchor="nw", padx=16, pady=16)

        self.cent_frame = tkinter.Frame(self.root)
        self.cent_frame.pack(side=tkinter.TOP, anchor="nw", padx=32, pady=16)

        self.timer_history = TimerHistory(pathlib.Path("./history.pickle"))

        # Initial widgets
        self.init_widgets()
        self.root.mainloop()

    def init_widgets(self) -> None:
        UICurrentTimer(self.root, self.top_frame, self.timer_history)
        today_timers = UITodayTimers(self.root, self.cent_frame, self.timer_history)
        self.root.bind("<<history_updated>>", today_timers.reload)


def run():
    pass
    #UI()

if __name__ == "__main__":
    run()
