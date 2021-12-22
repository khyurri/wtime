from distutils.core import setup

setup(
    name="wtime",
    version="0.1.1",
    description="Name your task, plan duration and focus on work",
    authors=["Ruslan Khyurri <ruslan.khyurri@gmail.com>"],
    license="MIT",
    python_requires=">=3.8",
    entry_points={"console_scripts": ["wtime = wtime.wtime:run"]},
    extras_require={
        "dev": [
            "black>=21.12b0",
            "pylint>=2.11.1",
            "mypy>=0.910",
        ],
    },
)
