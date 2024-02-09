from distutils.core import setup

setup(
    name="wtime",
    version="0.2.1",
    description="Name your task, plan duration and focus on work",
    authors=["Ruslan Khyurri <ruslan.khyurri@gmail.com>"],
    license="MIT",
    python_requires=">=3.12",
    entry_points={"console_scripts": ["wtime = wtime.wtime:run"]},
    install_requires=[
        "ttkbootstrap==1.10.1",
    ],
    extras_require={
        "dev": ["ruff==0.2.1", "mypy==0.910", "pytest==7.4.4", "isort==5.13.2"],
    },
)
