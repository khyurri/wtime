def seconds(time_seconds: int) -> str:
    return f"{time_seconds}s"


def minutes(time_seconds: int) -> str:
    time_minutes = time_seconds // 60
    time_seconds_left = time_seconds - time_minutes * 60
    return f"{time_minutes}m {seconds(time_seconds_left)}"


def hours(time_seconds: int) -> str:
    time_hours = time_seconds // 3600
    time_seconds_left = time_seconds - time_hours * 3600
    return f"{time_hours}h {minutes(time_seconds_left)}"


def format(time_seconds: int) -> str:
    if time_seconds < 60:
        return seconds(time_seconds)
    if time_seconds < 3600:
        return minutes(time_seconds)
    return hours(time_seconds)
