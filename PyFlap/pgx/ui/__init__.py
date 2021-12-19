import numbers
import json

import pygame

import pgx
from pgx.File import WrappedSequence

# https://docs.python.org/3/library/html.parser.html
# could be very handy


class Backend:

    # CURSOR HANDLING

    cursor_default = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW)
    cursor_requested = None
    cursor_visible = True

    _pygame_set_cursor = pygame.mouse.set_cursor

    def _pgx_set_cursor(*args):
        res = Backend._pygame_set_cursor(*args)
        Backend.cursor_default = pygame.cursors.Cursor(*args)
        return res

    pygame.mouse.set_cursor = _pgx_set_cursor

    @staticmethod
    def request_cursor(cursor):
        if cursor is False:
            Backend.cursor_visible = False

        if cursor is None:
            cursor = Backend.cursor_default

        Backend.cursor_requested = pygame.cursors.Cursor(cursor)

    # DEFAULT SCREEN HANDLING

    screen = None

    # monkey patch set_mode() to guarantee UI always has current screen surface
    _pygame_set_mode = pygame.display.set_mode

    def _pgx_set_mode(*args):
        res = Backend._pygame_set_mode(*args)
        Backend.screen = res
        return res

    pygame.display.set_mode = _pgx_set_mode

    # TICK SPECIFIC HANDLING

    @staticmethod
    def _tick():
        if Backend.cursor_requested:
            Backend._pygame_set_cursor(Backend.cursor_requested)
        else:
            Backend._pygame_set_cursor(Backend.cursor_default)

        Backend.cursor_requested = None

        pygame.mouse.set_visible(Backend.cursor_visible)
        Backend.cursor_visible = True

    REGENERATIVE_TAGS = frozenset(
        {
            "color",
            "bgcolor",
            "font",
            "font_size",
            "text_align",
            "text_width",
            "line_height",
            "scale",
            "margin",
        }
    )

    SCALE_TAGS = frozenset({"font_size", "border_width", "text_width", "margin"})

    STYLE_DEFAULTS = {
        "color": (0, 0, 0),
        "bgcolor": (0, 0, 0, 0),
        "font": "opensans",
        "font_size": 16,
        "font_style": pygame.freetype.STYLE_DEFAULT,
        "border": False,
        "border_width": 2,
        "border_color": (0, 0, 0),
        "text_align": "left",
        "text_width": False,
        "line_height": 1.2,
        "align": pygame.Vector2(0, 0),
        "cursor": pygame.SYSTEM_CURSOR_IBEAM,
        "scale": 1,
        "margin": 0,
        "display": True,
    }

    ELEM_TYPES = frozenset({"Text", "Image", "Input", "CheckBox"})

    # stores group names and element names to prevent conflicts
    ALL_NAMES = set()

    # just stores element names
    NAME_NAMES = set()

    @staticmethod
    def validate_groups(groups):
        if not isinstance(groups, (list, tuple)):
            raise TypeError("groups must be a list or tuple")

        for group in groups:
            if not isinstance(group, str):
                raise TypeError("group must be a string")
            if group in Backend.NAME_NAMES or group in Backend.ELEM_TYPES:
                raise ValueError(
                    "group names cannot conflict with element names or element types"
                )
            Backend.ALL_NAMES.add(group)

    @staticmethod
    def validate_name(name):
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        if name in Backend.ALL_NAMES or name in Backend.ELEM_TYPES:
            raise ValueError("Conflicting names not allowed")
        Backend.NAME_NAMES.add(name)
        Backend.ALL_NAMES.add(name)


TEXT_ALIGNS = frozenset({"left", "center", "right"})


class Style:
    def __init__(self, base=False):
        self._slots = ["inline_style"]
        self.inline_style = Backend.STYLE_DEFAULTS.copy() if base else dict()

    def _set_color(self, color):
        self.inline_style["color"] = pygame.Color(color)

    def _set_bgcolor(self, bgcolor):
        self.inline_style["bgcolor"] = pygame.Color(bgcolor)

    def _set_font(self, font):
        if isinstance(font, str):
            try:
                getattr(pgx.font, font)
            except AttributeError:
                raise ValueError(
                    "font property string names must correspond to a pgx.font attribute"
                )
        else:
            raise TypeError(
                "font property must be a string key to a pgx.font.Font-like object"
            )

        self.inline_style["font"] = font

    def _set_font_size(self, size):
        if not isinstance(size, numbers.Real):
            raise TypeError("font_size property must be a number")
        self.inline_style["font_size"] = size

    def _set_font_style(self, style):
        # TODO check validity
        self.inline_style["font_style"] = style

    def _set_border(self, border):
        if not isinstance(border, bool):
            raise TypeError("border property must a Boolean")
        self.inline_style["border"] = border

    def _set_border_width(self, border_width):
        if not isinstance(border_width, int):
            raise TypeError("border_width property must be an integer")
        self.inline_style["border_width"] = border_width

    def _set_border_color(self, border_color):
        self.inline_style["border_color"] = pygame.Color(border_color)

    def _set_text_align(self, text_align):
        if text_align not in TEXT_ALIGNS:
            raise ValueError(f"text_align property must be in {TEXT_ALIGNS}")
        self.inline_style["text_align"] = text_align

    def _set_text_width(self, text_width):
        if text_width is not False and not isinstance(text_width, int):
            raise TypeError("text_width property must be an integer or False")
        self.inline_style["text_width"] = text_width

    def _set_line_height(self, line_height):
        if not isinstance(line_height, numbers.Real):
            raise TypeError("line_height property must be a number")
        self.inline_style["line_height"] = line_height

    def _set_align(self, align):
        # TODO parse string keys - "center" and such
        self.inline_style["align"] = pygame.Vector2(align)

    def _set_cursor(self, cursor):
        if cursor in [None, False]:
            self.inline_style["cursor"] = cursor
        self.inline_style["cursor"] = pygame.cursors.Cursor(cursor)

    def _set_scale(self, scale):
        if not isinstance(scale, numbers.Real):
            raise TypeError("scale property must be a number")
        self.inline_style["scale"] = scale

    def _set_margin(self, margin):
        if not isinstance(margin, int):
            raise TypeError("margin property must be an integer")
        self.inline_style["margin"] = margin

    def _set_display(self, display):
        if not isinstance(display, bool):
            raise TypeError("display property must be a boolean")
        self.inline_style["display"] = display

    def _make_getter(name):
        return lambda x: x.inline_style.get(name)

    def __setattr__(self, attr, value):
        if attr not in Backend.STYLE_DEFAULTS:
            if attr not in ["_slots"] + getattr(self, "_slots", []):
                print(self._slots)
                raise AttributeError(f"There is no style tag named '{attr}'")
        super().__setattr__(attr, value)
        # print(attr, value)

    color = property(_make_getter("color"), _set_color)
    bgcolor = property(_make_getter("bgcolor"), _set_bgcolor)
    font = property(_make_getter("font"), _set_font)
    font_size = property(_make_getter("font_size"), _set_font_size)
    font_style = property(_make_getter("font_style"), _set_font_style)
    border = property(_make_getter("font_style"), _set_border)
    border_width = property(_make_getter("border_width"), _set_border_width)
    border_color = property(_make_getter("border_color"), _set_border_color)
    text_align = property(_make_getter("text_align"), _set_text_align)
    text_width = property(_make_getter("text_width"), _set_text_width)
    line_height = property(_make_getter("line_height"), _set_line_height)
    align = property(_make_getter("align"), _set_align)
    cursor = property(_make_getter("cursor"), _set_cursor)
    scale = property(_make_getter("scale"), _set_scale)
    margin = property(_make_getter("margin"), _set_margin)
    display = property(_make_getter("display"), _set_display)


class StyleSheet:
    def __init__(self):
        self.Text = Style(True)
        self.Image = Style(True)
        self.Input = Style(True)
        self.CheckBox = Style(True)

    def __getattr__(self, attr):
        setattr(self, attr, Style())
        return getattr(self, attr)


STYLESHEET = StyleSheet()


def use_stylesheet(path):
    path = pgx.path.handle(path)

    preferences = []
    with open(path) as f:
        preferences = json.load(f)

    for preference in preferences:
        relevant = getattr(STYLESHEET, preference)

        for value in preferences[preference]:
            setattr(relevant, value, preferences[preference][value])


class StyleManager(Style):
    def __init__(self, inline_style, elemtype, groups, name):
        self._slots = ["inline_style", "managers", "last_dict"]
        self.inline_style = inline_style
        self.update_groupings(elemtype, groups, name)
        self.last_dict = dict()

    def update_groupings(self, elemtype, groups, name):
        self.managers = [getattr(STYLESHEET, elemtype)]

        if groups:
            for group in groups:
                self.managers.append(getattr(STYLESHEET, group))

        if name:
            self.managers.append(getattr(STYLESHEET, name))

        self.managers.append(self)

    def tick(self):
        style = dict()
        regenerate = False
        for manager in self.managers:
            style.update(manager.inline_style)

        for tag in Backend.REGENERATIVE_TAGS:
            try:
                if style[tag] != self.last_dict.get(tag):
                    regenerate = True
                    break
            except KeyError:
                print(style)
                print(self.last_dict)
                1 / 0

        self.last_dict = style

        return style, regenerate


def _group_cb(groups, element):
    element._update_style_manager()


def _create_group_cb(element):
    return lambda x: _group_cb(x, element)


class Element:
    def __init__(self, location, **kwargs):
        self.location = pygame.Vector2(location)

        self.groups = kwargs.get("groups", [])
        Backend.validate_groups(self.groups)
        self.groups = WrappedSequence(self.groups, _create_group_cb(self))

        self.name = kwargs.get("name")
        if self.name:
            Backend.validate_name(self.name)

        inline_style = kwargs.get("style", {})

        self.style = StyleManager(
            inline_style, self.__class__.__name__, self.groups, self.name
        )

        # should error on unrecognized kwargs

        # self.size, #self.rect should be set in _generate()
        self.REGENERATE = False

        self.hovered = False
        self.just_hovered = False
        self.just_unhovered = False

        self.clicked = False
        self._clicked_inside = False

        self.selected = False

    def _update_style_manager(self):
        self.style.update_groupings(self.__class__.__name__, self.groups, self.name)

    def _make_rect(self):
        style = self.style_dict
        align = style["align"]
        x = self.location.x - self.size.x * align.x
        y = self.location.y - self.size.y * align.y
        self.rect = pygame.Rect(x, y, *self.size)

        inflation = style["margin"] * 2 * style["scale"]
        self.margin_rect = self.rect.inflate((inflation, inflation))

    def _generate(self):
        self._elem_generate()  # must call self._make_rect()
        self.REGENERATE = False

    # Just trying something out
    def set_position(self, pos):
        self.location = pygame.Vector2(pos)
        self.REGENERATE = True
        # self._make_rect()

    def display(self, screen=None):
        self.style_dict, style_regen = self.style.tick()

        if not self.style_dict["display"]:
            return

        if self.REGENERATE or style_regen:  # style_regen triggers first generation
            self._generate()

        if screen is None:
            screen = Backend.screen
        self._elem_display(screen)

        style = self.style_dict
        border_width = round(style["border_width"] * style["scale"])
        if style["border_width"]:
            border_width = max(1, border_width)
        if style["border"]:
            pygame.draw.rect(
                screen, style["border_color"], self.margin_rect, border_width
            )

        moused_over = self.margin_rect.collidepoint(pygame.mouse.get_pos())

        if not moused_over and pygame.mouse.get_pressed()[0]:
            self.selected = False

        self.just_hovered = False
        if moused_over and not self.hovered:
            self.just_hovered = True

        self.just_unhovered = False
        if not moused_over and self.hovered:
            self.just_unhovered = True

        self.hovered = False
        if moused_over:
            Backend.request_cursor(style["cursor"])
            self.hovered = True
            if pygame.mouse.get_pressed()[0]:
                self.selected = True

        self.clicked = False
        for event in pgx.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if moused_over:
                    self._clicked_inside = True
            if event.type == pygame.MOUSEBUTTONUP:
                if moused_over and self._clicked_inside:
                    self.clicked = True
                self._clicked_inside = False


class Text(Element):
    def __init__(self, string, location, **kwargs):
        self._text = string
        super().__init__(location, **kwargs)

    def _elem_generate(self):
        style = self.style_dict

        font_size = style["font_size"] * style["scale"]
        text_width = (
            style["text_width"] * style["scale"] if style["text_width"] else False
        )

        self._textobj = pgx.Text(
            self._text,
            font_size,
            color=style["color"],
            style=style["font_style"],
            align=style["text_align"],
            spacing=style["line_height"],
            font=getattr(pgx.font, style["font"]),
            limit=text_width,
        )
        self.size = pygame.Vector2(self._textobj.get_rect().size)
        self._make_rect()

        self._text_surf = pygame.Surface(self.margin_rect.size, pygame.SRCALPHA)
        self._text_surf.fill(style["bgcolor"])
        x = y = self.style_dict["margin"] * style["scale"]
        self._text_surf.blit(self._textobj.get_image(), (x, y))

    def _elem_display(self, screen):
        screen.blit(self._text_surf, self.margin_rect.topleft)

    def _get_text(self):
        return self._text

    def _set_text(self, text):
        self._text = str(text)
        self.REGENERATE = True

    text = property(_get_text, _set_text)


# helper for tracking changes for ctrl-z and ctrl-y in inputgetters
class ChangesTracker:
    def __init__(self, start):
        self.values = [start]
        self.index = 0

    def add(self, val):
        self.index += 1
        del self.values[self.index :]
        self.values.append(val)

    def forward(self):
        self.index += 1
        if self.index > len(self.values) - 1:
            self.index = len(self.values) - 1
        return self.values[self.index]

    def back(self):
        self.index -= 1
        if self.index < 0:
            self.index = 0
        return self.values[self.index]

    def see_current(self):
        return self.values[self.index]


class Input(Text):
    def __init__(self, string, location, **kwargs):
        super().__init__(string, location, **kwargs)

        self.length_limit = False
        # needs to be updated by set_text() as well
        self.changes = ChangesTracker(self._text)
        self.allowed_chars = False

        self.blink_time = 0.7
        self.blink_timer = 0
        self.blink = False

    def _elem_display(self, screen):
        if not self.selected:
            super()._elem_display(screen)
            return

        self.blink_timer += pgx.time.delta_time
        for event in pgx.key.get_text_input_events():
            char = event.unicode
            mod = event.mod
            regen = True

            # with any input it deletes what it has
            # if self.del_after_input:
            #    self.del_after_input = False
            #    self.text.text = ""

            # paste support (ctrl-v)
            # if char == "\x16" and mod & pgx.key.MOD:
            #    k = scrap.get(pygame.SCRAP_TEXT)
            #    for letter in k:
            #        self._handle_text(letter)

            # undo support (ctrl-z)
            if char == "\x1a" and mod & pgx.key.MOD:
                self._text = self.changes.back()

            # redo support (ctrl-y)
            elif char == "\x19" and mod & pgx.key.MOD:
                self._text = self.changes.forward()

            # deleting text on backspace
            elif char == "\b" and len(self.text) != 0:
                self._text = self._text[:-1]

            # else:
            elif not self.length_limit or len(self._text) < self.length_limit:
                is_textchar = (
                    char not in ["\b", "\t", "\r", "\n"] and not mod & pgx.key.MOD
                )
                is_allowedchar = (
                    self.allowed_chars == False or char in self.allowed_chars
                )
                if is_textchar and is_allowedchar:
                    self._text += char

            else:
                regen = False

            # on ENTER/RETURN, stop being selected (should be a setting)
            if event.key == pygame.K_RETURN:
                self.selected = False

            if regen:
                self.REGENERATE = True

        if self.changes.see_current() != self._text:
            self.changes.add(self._text)

        super()._elem_display(screen)
        if self.blink_timer > self.blink_time:
            self.blink_timer = 0
            self.blink = not self.blink

        if self.blink:
            blink = pygame.Surface((2, self.rect.h))
            blink.fill((0, 0, 0))
            x, y = self.rect.topright
            y += 2
            screen.blit(blink, (x, y))

    def _set_text(self, text):
        super()._set_text(text)
        self.changes.add(self._text)


class Image(Element):
    def __init__(self, surface, location, **kwargs):
        self._surface_orig = surface.copy()
        self._surface = surface.copy()
        super().__init__(location, **kwargs)

    def _elem_generate(self):
        style = self.style_dict

        if style["scale"] != 1:
            self._surface = pgx.image.scale(self._surface_orig, style["scale"])

        self.size = pygame.Vector2(self._surface.get_size())
        self._make_rect()

    def _elem_display(self, screen):
        screen.blit(self._surface, self.rect.topleft)

    def _set_surface(self, surf):
        self._surface_orig = surf.copy()
        self._surface = surf.copy()
        self.REGENERATE = True

    def _get_surface(self):
        return self._surface_orig

    # untested
    surface = property(_get_surface, _set_surface)


class CheckBox(Element):
    def __init__(self, location, checked=False, **kwargs):
        self.checked = checked
        super().__init__(location, **kwargs)
        self.style.border = True
        self.style.cursor = pygame.SYSTEM_CURSOR_HAND

    def _elem_generate(self):
        style = self.style_dict
        self.size = pygame.Vector2(15, 15) * style["scale"]
        self._make_rect()

    def _elem_display(self, screen):
        if self.clicked:
            self.checked = not self.checked

        if self.checked:
            pygame.draw.rect(screen, "blue", self.rect)
