import math
from collections import defaultdict
from typing import Union

import pygame
import pygame.freetype

import pgx

from widgets import NodeMenu, TestMenu, InfoOutput

pygame.init()
pygame.freetype.init()

FONT = pygame.freetype.Font(pgx.font.roboto.path)

pgx.path.set_projectpath("assets")
pgx.ui.use_stylesheet("style.json")

try:
    BG_COLOR = pgx.ui.STYLESHEET.general_config.bgcolor
except AttributeError:
    BG_COLOR = [85, 110, 85]

try:
    NODE_COLOR = pgx.ui.STYLESHEET.general_config.color
except AttributeError:
    NODE_COLOR = "yellow"

screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("PyFlap")
pygame.display.set_icon(pgx.image.load("node.png"))


class NFAError(NotImplementedError):
    pass


class DFA:
    def __init__(self):
        self.nodes = []

        self.initial_node = None

        self.pending_connection = False
        self.pending_connection_input = pgx.ui.Input("", (50, 50), groups=["iobox"])

        self.offset = pygame.Vector2()

        self.node_menu = False

    def move(self, x: float, y: float) -> None:
        self.offset.x += x
        self.offset.y += y

    def draw(self, screen: pygame.Surface) -> None:
        for node in self.nodes:
            node.draw(screen, self.offset)

        if self.pending_connection:
            node1, node2 = self.pending_connection
            middle, _ = self.draw_connection_to_pos(
                screen, node1, node2.pos + self.offset, True
            )
            self.pending_connection_input.location = middle
            self.pending_connection_input.display()
            if not self.pending_connection_input.selected:
                text = self.pending_connection_input.text
                if not text:
                    text = "λ"
                node1, node2 = self.pending_connection
                try:
                    node1.add_connection(text, node2)
                    self.pending_connection = False
                except NFAError:
                    self.pending_connection_input.selected = True
                    print("We don't do NFA's here!")

        if self.node_menu:
            self.node_menu.display()
            if not self.node_menu.active:
                self.node_menu = None

    def add_node_at(self, pos: pygame.Vector2) -> None:
        pos -= self.offset

        self.nodes.append(Node(pos))

        if len(self.nodes) == 1:  # if this is the first node
            self.nodes[0].initial = True
            self.initial_node = self.nodes[0]
            # could be pretty error prone to store the initial_ness two separate places

    def get_node_at(self, pos: pygame.Vector2) -> "Node":
        pos -= self.offset

        for node in self.nodes:
            if (pos - node.pos).length_squared() < node.radius ** 2:
                return node
        return False

    def move_node_to(self, node: "Node", pos: pygame.Vector2) -> None:
        pos -= self.offset
        node.pos = pos

    def move_node_by(self, node: "Node", off: pygame.Vector2) -> None:
        node.pos += off

    def make_node_initial(self, node: "Node") -> None:
        if self.initial_node:
            self.initial_node.initial = False

        self.initial_node = node
        self.initial_node.initial = True

    def make_node_uninitial(self, node: "Node") -> None:
        node.initial = False
        if node == self.initial_node:
            self.initial_node = None

    def draw_connection_to_pos(
        self,
        screen: pygame.Surface,
        node: "Node",
        pos: pygame.Vector2,
        adjust_radius: bool = False,
    ):
        position = node.pos + self.offset
        pos -= self.offset
        return node.draw_connection_to_pos(screen, position, pos, adjust_radius)

    def connect_query(self, node1: "Node", node2: "Node") -> None:
        self.pending_connection_input.selected = True
        self.pending_connection_input.text = ""
        self.pending_connection = (node1, node2)

    def delete_node(self, node: "Node") -> None:
        node.exists = False
        self.nodes.remove(node)

        if self.initial_node == node:
            self.initial_node = None

    def open_node_menu(self, node: "Node") -> None:
        self.node_menu = NodeMenu(node, self)

    def test(self, walk: str) -> bool:
        n = self.initial_node

        if not n:
            print("Languages without initial states are very intolerant...")
            return False

        for char in walk:
            n = n.get_connection(char)
            if not n:
                return False

        if n.final:
            return True
        return False


class Node:
    radius = 25

    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.connections = {}
        self.initial = False
        self.final = False
        self.exists = True

    def add_connection(self, char, node) -> None:
        if char in self.connections:
            raise NFAError("We don't do NFAs here")
        if not isinstance(char, str):
            raise TypeError("char should be a string!")
        self.connections[char] = node

    def get_connection(self, char) -> Union["Node", None]:
        if char in self.connections:
            return self.connections[char]
        # else:
        #    raise NotImplementedError("We don't do NFAs here")
        return None  # it can be lenient about barely NFA NFAs

    def draw_connection_to_pos(
        self,
        screen: pygame.Surface,
        position: pygame.Vector2,
        other_pos: pygame.Vector2,
        adjust_for_radius: bool = True,
    ) -> (pygame.Vector2, int):
        radius = Node.radius

        direct = self.pos - other_pos
        if not direct:  # zero length vector, don't draw anything
            return position, 0  # default return args?

        direction = direct.normalize() * radius

        start = position - direction
        end = position - direct  # + direction #other.pos + direction
        if adjust_for_radius:
            end += direction

        direction /= 2

        arrow_direction = direction.rotate(320)
        pygame.draw.aaline(screen, "black", end, end + arrow_direction)

        arrow_direction = direction.rotate(-320)
        pygame.draw.aaline(screen, "black", end, end + arrow_direction)

        pygame.draw.aaline(screen, "black", start, end)

        rot = int(180 - direction.as_polar()[1])

        middle = start.lerp(end, 0.5)

        return middle, rot

    def _draw_connection(self, screen, position, char, other):
        radius = Node.radius

        if other == self:
            rect = pygame.Rect([0, 0, radius * 1.2, radius * 2.8])
            rect.centerx = position.x
            rect.top = position.y - radius * 2.3
            # pygame.draw.rect(screen, "orange", rect)

            pygame.draw.arc(screen, "black", rect, 0.01, math.pi)
            end = rect.midleft
            direction = pygame.Vector2(0, -radius / 2)

            arrow_direction = direction.rotate(320)
            pygame.draw.aaline(screen, "black", end, end + arrow_direction)

            arrow_direction = direction.rotate(-320)
            pygame.draw.aaline(screen, "black", end, end + arrow_direction)

            FONT.rotation = 0
            FONT.size = 16

            surf, trect = FONT.render(char)
            trect.midbottom = rect.midtop
            screen.blit(surf, trect)

        else:
            middle, rot = self.draw_connection_to_pos(screen, position, other.pos)

            # adjust backwards facing connections to be more "up" facing
            if 90 < rot < 270:
                rot = 180 + rot

            FONT.rotation = rot

            FONT.size = 16

            surf, rect = FONT.render(char)
            rect.topleft = (200, 200)

            rect.bottomright = middle

            # pygame.draw.rect(screen, "orange", rect)
            screen.blit(surf, rect)

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        radius = Node.radius
        position = self.pos + offset

        if self.initial:
            point1 = pygame.Vector2(position)
            point1.x -= radius
            point2 = pygame.Vector2(point1)
            point2.x -= 15
            point2.y += 15
            point3 = pygame.Vector2(point1)
            point3.x -= 15
            point3.y -= 15

            pygame.draw.polygon(screen, "blue", [point1, point2, point3])

        # invalid keys is the runtime way of removing invalidated connections
        # from deleted nodes
        invalid_keys = []
        # draw_dict groups them by destination node, allowing the connections
        # to be grouped properly
        draw_dict = defaultdict(list)
        for char in self.connections:
            if not self.connections[char].exists:
                invalid_keys.append(char)
            else:
                draw_dict[self.connections[char]].append(char)

        for key in invalid_keys:
            del self.connections[key]

        for node in draw_dict:
            text = ", ".join(draw_dict[node])
            self._draw_connection(screen, position, text, node)

        pygame.draw.circle(screen, NODE_COLOR, position, radius)
        pygame.draw.circle(screen, "black", position, radius, 2)

        if self.final:
            pygame.draw.circle(screen, "black", position, radius * 0.8, 2)


machine = DFA()

surf = pgx.image.load("node.png")
place_button = pgx.ui.Image(surf, (10, 5), groups=["button"])

surf = pgx.image.load("arrow.png")
connect_button = pgx.ui.Image(surf, (60, 5), groups=["button"])

surf = pgx.image.load("x.png")
del_button = pgx.ui.Image(surf, (110, 5), groups=["button"])

welcome = pgx.ui.Text("Welcome to PyFlap!", (screen.get_width() / 2, 5))
welcome.style.align = pygame.Vector2(0.5, 0)
welcome.style.font_size = 26

info = InfoOutput()
print = info.print

testmenu = TestMenu(machine)

mode = "free"
connection_root = False
move_node = False
hovered_node = False

SCROLL_SPEED = 100
MOUSE_HELD = False

while True:
    hovered_node = machine.get_node_at(pygame.mouse.get_pos())

    for event in pgx.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit

        if event.type == pygame.MOUSEBUTTONDOWN:
            if mode == "place":
                machine.add_node_at(event.pos)
                mode = "free"
            elif mode == "connect":
                connection_root = hovered_node
                if not connection_root:
                    mode = "free"
            elif mode == "delete":
                _del_node = hovered_node
                if _del_node:
                    machine.delete_node(_del_node)
                    mode = "free"
            else:
                if event.button == 1:
                    move_node = hovered_node
                if event.button == 3:
                    _node = hovered_node
                    if _node:
                        machine.open_node_menu(_node)
                mode = "free"
            MOUSE_HELD = True

        if event.type == pygame.MOUSEMOTION:
            if move_node:
                machine.move_node_by(move_node, pygame.Vector2(event.rel))
            elif MOUSE_HELD and mode == "free":
                machine.move(*event.rel)

        if event.type == pygame.MOUSEBUTTONUP:
            if mode == "connect" and connection_root:
                connection = hovered_node
                if connection:
                    machine.connect_query(connection_root, connection)
                    mode = "free"
            move_node = False
            MOUSE_HELD = False

    if pgx.key.is_pressed(pygame.K_w):
        machine.move(0, -SCROLL_SPEED * pgx.time.delta_time)
    if pgx.key.is_pressed(pygame.K_s):
        machine.move(0, SCROLL_SPEED * pgx.time.delta_time)
    if pgx.key.is_pressed(pygame.K_a):
        machine.move(-SCROLL_SPEED * pgx.time.delta_time, 0)
    if pgx.key.is_pressed(pygame.K_d):
        machine.move(SCROLL_SPEED * pgx.time.delta_time, 0)

    screen.fill(BG_COLOR)

    machine.draw(screen)

    pygame.draw.rect(screen, "grey", [0, 0, screen.get_width(), 40])

    if mode == "connect" and connection_root:
        machine.draw_connection_to_pos(screen, connection_root, pygame.mouse.get_pos())

    welcome.display()

    testmenu.display()

    place_button.display()
    if place_button.clicked:
        mode = "place"

    connect_button.display()
    if connect_button.clicked:
        mode = "connect"
        connection_root = False

    del_button.display()
    if del_button.clicked:
        mode = "delete"

    info.display()

    pygame.display.flip()
    pgx.tick(144)
