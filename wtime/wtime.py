import datetime
import json
import logging
import pathlib
import tkinter
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterator, Optional, TypedDict

import time_format
import ttkbootstrap as ttk

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class InconsistentTimerState(Exception):
    pass


class State(StrEnum):
    init = "init"
    running = "running"
    stopped = "stopped"


@dataclass
class Timer:
    state: State = State.init
    date_start: Optional[datetime.datetime] = None
    date_end: Optional[datetime.datetime] = None

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
    return sum(
        [timer.spent() for timer in timers],
        start=datetime.timedelta(seconds=0),
    )


class HistoryDict(TypedDict):
    date_start: str  # isoformat
    date_end: str  # isoformat


class TimerHistory:
    def __init__(self, file: pathlib.Path) -> None:
        self.storage = Storage(file)
        self.history: list[Timer] = list(self._restore_history())

    def add_timer(self, timer: Timer) -> None:
        self.history.append(timer)
        self._save_history()

    def group_by_day(self) -> list[list[Timer]]:
        grouped = []
        last_time = None
        for time in self.history:
            current_date = pretty_date(time.date_start)
            if last_time is None or last_time != current_date:
                last_time = current_date
                grouped.append([])
            grouped[-1].append(time)
        return grouped

    def _restore_history(self) -> Iterator[Timer]:
        json_restored: list[HistoryDict]
        for json_restored in self.storage.restore():
            yield Timer(
                state=State.stopped,  # todo: maybe we could store running timers
                date_start=datetime.datetime.fromisoformat(
                    json_restored["date_start"]
                ),
                date_end=datetime.datetime.fromisoformat(
                    json_restored["date_end"]
                ),
            )

    def _save_history(self) -> None:
        store_list: list[HistoryDict] = []
        for timer in self.history:
            store_list.append(
                {
                    "date_start": timer.date_start.isoformat(),  # type: ignore
                    "date_end": timer.date_end.isoformat(),  # type: ignore
                }
            )
        self.storage.store(store_list)


class Storage:
    def __init__(self, path: pathlib.Path) -> None:
        self.path = path

    def restore(self) -> list[HistoryDict]:
        try:
            with open(self.path, "rb") as file:
                return json.load(file)  # type: ignore
        except FileNotFoundError:
            return []

    def store(self, timer: list[HistoryDict]) -> None:
        with open(self.path, "w") as file:
            json.dump(timer, file)


def pretty_spent_time(time: datetime.timedelta) -> str:
    return str(time_format.format(time.seconds))


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

    TIMER_INIT_VALUE = "0s"
    START_TIMER_INIT_VALUE = "00:00:00"

    def __init__(
        self, root: tkinter.Tk, frame: tkinter.Frame, history: TimerHistory
    ) -> None:
        self.timer: Timer | None = None
        self.root = root
        self.timer_value = tkinter.StringVar(value=self.TIMER_INIT_VALUE)
        self.start_time_value = tkinter.StringVar(
            value=self.START_TIMER_INIT_VALUE
        )

        self.timer_history = history

        self.button = ttk.Button(
            frame, text=self.TEXT_START, command=self.init_timer
        )
        self.button.pack(side=tkinter.LEFT, padx=16)

        self.start_label = ttk.Label(frame, textvariable=self.start_time_value)
        self.start_label.pack(side=tkinter.LEFT, padx=16)

        self.current_label = ttk.Label(frame, textvariable=self.timer_value)
        self.current_label.pack(side=tkinter.LEFT, padx=16)

    def init_timer(self) -> None:
        if self.timer is not None:
            raise ValueError("Timer is already running")

        self.timer = Timer()
        self.timer.start()
        self.button.configure(text=self.TEXT_STOP, command=self.deinit_timer)
        if self.timer.date_start is None:
            raise InconsistentTimerState("timer must have date_start: {timer}")
        self.start_time_value.set(time_start(self.timer.date_start))
        self.run_loop()

    def run_loop(self) -> None:
        if self.timer and self.timer.state == State.running:
            if self.timer.date_start is None:
                raise InconsistentTimerState(
                    "timer must have date_start: {timer}"
                )

            self.timer_value.set(
                pretty_spent_time(
                    datetime.datetime.now(datetime.UTC) - self.timer.date_start
                )
            )
            self.root.after(100, self.run_loop)
        else:
            self.timer_value.set(self.TIMER_INIT_VALUE)
            self.start_time_value.set(self.START_TIMER_INIT_VALUE)

    def deinit_timer(self) -> None:
        if self.timer is None:
            raise ValueError("Timer is not initialized")
        self.timer.stop()
        self.timer_history.add_timer(self.timer)
        self.timer = None
        self.button.configure(text=self.TEXT_START, command=self.init_timer)
        self.root.event_generate("<<history_updated>>")


class UITimers:
    def __init__(
        self, root: ttk.Frame, frame: ttk.Frame, history: TimerHistory
    ) -> None:
        self.root = root
        self.frame = frame
        self.parent_rows: dict[str, str] = {}

        columns = {"date_start": "Date Start", "spent": "Time spent"}
        self.history_table = ttk.Treeview(
            frame,
            columns=tuple(columns.keys()),
            show="headings",
        )
        self.history_table.pack(expand=True, fill="both")
        for col, name in columns.items():
            self.history_table.heading(col, text=name)
            self.history_table.heading(col, text=name)

        self.timer_history = history
        self.init_history()

    def new_day_parent(self, timer: Timer, previous: list[Timer]) -> str:
        if timer.date_start is None:
            raise InconsistentTimerState("timer must have date_start: {timer}")
        new_parent = str(
            self.history_table.insert(
                parent="",
                index=0,
                values=(
                    pretty_date(timer.date_start),
                    pretty_spent_time(sum_timers(previous)),
                ),
            )
        )
        self.parent_rows[pretty_date(timer.date_start)] = new_parent
        return new_parent

    def update_day_parent(self, iid: str, previous: list[Timer]) -> None:
        row = self.history_table.item(iid)
        values = list(row["values"])
        values[1] = pretty_spent_time(sum_timers(previous))
        self.history_table.item(iid, values=values)

    def insert_time(self, parent: str, timer: Timer) -> None:
        if timer.date_start is None:
            raise InconsistentTimerState("timer must have date_start: {timer}")
        self.history_table.insert(
            parent=parent,
            index="end",
            values=(
                pretty_time(timer.date_start),
                pretty_spent_time(timer.spent()),
            ),
        )

    def init_history(self) -> None:
        group: list[Timer]
        timer: Timer
        for group in self.timer_history.group_by_day():
            current_parent = self.new_day_parent(group[0], group)
            for timer in group:
                self.insert_time(current_parent, timer)

    def reload(self, _) -> None:  # type: ignore
        last_time = self.timer_history.history[-1]
        if last_time.date_start is None:
            raise InconsistentTimerState(
                "last_timer must have date_start: {last_time}"
            )

        last_time_date = pretty_date(last_time.date_start)
        today_timers = self.timer_history.group_by_day()[-1]

        if last_time_date in self.parent_rows:
            self.update_day_parent(
                self.parent_rows[last_time_date], today_timers
            )
            self.history_table.insert(
                parent=self.parent_rows[last_time_date],
                index=0,
                values=(
                    pretty_time(last_time.date_start),
                    pretty_spent_time(last_time.spent()),
                ),
            )
        else:
            parent = self.new_day_parent(last_time, [last_time])
            self.insert_time(parent, last_time)


class UI:
    def __init__(self) -> None:
        self.root = tkinter.Tk()
        style = ttk.Style(theme="pulse")
        style.master.geometry("600x300")
        self.root.resizable(False, False)

        self.top_frame = ttk.Frame(self.root)
        self.top_frame.pack(fill="x", expand=True)

        self.cent_frame = ttk.Frame(self.root)
        self.cent_frame.pack(fill="x", expand=True)

        self.timer_history = TimerHistory(pathlib.Path("./history.json"))

        # Initial widgets
        self.init_widgets()
        self.root.mainloop()

    def init_widgets(self) -> None:
        UICurrentTimer(self.root, self.top_frame, self.timer_history)
        today_timers = UITimers(self.root, self.cent_frame, self.timer_history)
        self.root.bind("<<history_updated>>", today_timers.reload)


def run() -> None:
    UI()


if __name__ == "__main__":
    run()
