import pygame
import pygame.freetype

# General utilities
from pgx.path import path

path._init()  # init pathing asap

from pgx.event import event
from pgx.time import time
from pgx.key import key
from pgx.File import File
from pgx.Rect import Rect
import pgx.image

# Rarely used, but hopefully useful utilities
from pgx.compiler import compiler

# UI system
from pgx.font import font
from pgx.Text import Text
import pgx.ui

# Experimental
from pgx.handle_error import handle_error


class VersionType(type):
    major = 0
    minor = 8
    patch = 1
    vernum = (major, minor, patch)
    ver = ".".join([str(i) for i in vernum])

    def __str__(cls):
        return f"pgx version: {cls.vernum}"


class version(metaclass=VersionType):
    pass


__version__ = version.ver


def init() -> None:
    pygame.mixer.init()
    pygame.key.set_repeat(500, 20)


def tick(*args) -> None:
    # fps limiter - optional
    time._tick(*args)

    # gets the event stuff updated
    event._update()

    # gets the keyboard ready to respond
    key._prepare()

    # all the sticky UI "global" UI stuff (right now: just cursors)
    ui.Backend._tick()
