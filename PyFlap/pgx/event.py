import pygame

"""
cool if there was a remove_next(type), which waits until it sees something and removes it
maybe a remove(event)
and a post(event)

do we need to emulate more of pygame.event?
"""

# allows multiple locations to peek at what the event queue had to say since last tick
# the event queue kicks up keydown events, keyup events, and exit events, along with other things
class event:
    CLICK_ADD_DELAY = 500  # msec

    _tickevents = []  # used to store event queue offloads

    _last_click_msec = 0
    _clickcount = 1

    # called every tick by pgx.tick()
    @staticmethod
    def _update():
        event._tickevents.clear()
        for pg_event in pygame.event.get():
            event._tickevents.append(pg_event)

            # left click events are given a clickcount variable to see whether
            # it is a double or triple or arbitrary number click
            if pg_event.type == pygame.MOUSEBUTTONDOWN:
                if pg_event.button == 1:
                    ct = pygame.time.get_ticks()
                    lt = event._last_click_msec
                    if ct - lt < event.CLICK_ADD_DELAY:
                        event._clickcount += 1
                    else:
                        event._clickcount = 1

                    event._last_click_msec = ct
                    pg_event.clickcount = event._clickcount
                else:
                    pg_event.clickcount = 1

    # public method to access the updated list of events
    @staticmethod
    def get() -> list:
        """Returns the previous tick’s events."""
        return event._tickevents.copy()
