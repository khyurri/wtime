#
# Script for running timer
# [-] type task name and time in minutes
# [-] countdown to zero
#
from dataclasses import dataclass
from enum import Enum
from time import monotonic, sleep


@dataclass
class Timer:
    time_end: int
    topic: str

    @property
    def time_left(self) -> float:
        return self.time_end - monotonic()

    def print_time(self) -> None:
        print(f"{self.topic}: {(self.time_end-monotonic())/60:.0f}")


class State(str, Enum):
    COUNT_DOWN = "count_down"
    USER_INPUT = "user_input"
    PAUSE = "pause"
    CANCEL = "cancel"


def main(state: State):

    timer = Timer(topic="", time_end=0)
    while True:
        if state == State.USER_INPUT:
            input_ = input("> ")
            try:
                topic, time_seconds = input_.split(":")
            except ValueError:
                print("Usage - topic: minutes")
            else:
                timer.time_end = int(monotonic()) + int(time_seconds) * 60
                timer.topic = topic
                state = State.COUNT_DOWN
        if state == State.COUNT_DOWN:
            timer.print_time()
            if timer.time_left <= 0:
                state = State.USER_INPUT
        sleep(1)


def run():
    try:
        main(State.USER_INPUT)
    except KeyboardInterrupt:
        print("Bye")


if __name__ == "__main__":
    run()
