#
# Script for running timer
# [-] type task name and time in minutes
# [-] countdown to zero
#
import threading
from dataclasses import dataclass
from enum import Enum
from queue import Empty, Queue
from time import sleep


@dataclass
class Timer:
    time_left: int
    topic: str


class State(str, Enum):
    COUNT_DOWN = "count_down"
    USER_INPUT = "user_input"
    PAUSE = "pause"
    CANCEL = "cancel"


def input_listener(chan: Queue) -> None:
    while True:
        chan.put(input())
        sleep(0.3)


def tick(timer_state: Timer) -> None:
    if timer_state.time_left <= 0:
        raise AttributeError("Timer state should be bigger than 0")
    timer_state.time_left -= 1


def main(state: State):

    chan: Queue = Queue()
    threading.Thread(target=input_listener, args=(chan,), daemon=True).start()
    topic = ""
    timer = 0
    while True:
        try:
            input_ = chan.get(timeout=0)
        except Empty:
            input_ = None
        if state == State.USER_INPUT and input_ is not None:
            try:
                topic, time_seconds = input_.split(":")
            except ValueError:
                print("Usage - topic: minutes")
            else:
                timer = int(time_seconds) * 60
                state = State.COUNT_DOWN
        if state == State.COUNT_DOWN:
            timer -= 1
            sleep(1)
            if timer % 60 == 0:
                print(f"{topic}: {timer/60:.0f}")
            if timer == 0:
                state = State.USER_INPUT


def run():
    try:
        main(State.USER_INPUT)
    except BaseException:  # pylint: disable=(broad-except)
        print("Bye")


if __name__ == "__main__":
    run()
