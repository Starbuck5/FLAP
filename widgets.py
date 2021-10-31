import pygame

import pgx


class NodeMenu:
    def __init__(self, node, machine):
        surf = pygame.Surface((120, 60))
        surf.fill("grey")
        self.background = pgx.ui.Image(surf, pygame.Vector2(0, 150))
        self.background.style.border = True
        self.background.style.cursor = pygame.SYSTEM_CURSOR_ARROW

        self.incheck = pgx.ui.CheckBox(pygame.Vector2(5, 155))
        self.intext = pgx.ui.Text("Initial State", pygame.Vector2())

        self.fincheck = pgx.ui.CheckBox(pygame.Vector2(5, 180))
        self.fintext = pgx.ui.Text("Final State", pygame.Vector2())

        self.node = node

        self.offset = machine.offset  # reference to machine offset
        self.machine = machine

        self.rect = pygame.Rect(0, 0, *surf.get_size())

        self.fincheck.checked = self.node.final
        self.incheck.checked = self.node.initial

        self.active = True

    def display(self):
        self.rect.midbottom = self.node.pos + self.offset
        self.rect.y -= 10
        self.location = pygame.Vector2(self.rect.topleft)

        self.background.set_position(self.location)
        self.background.display()

        self.incheck.set_position(self.location + pygame.Vector2(5, 5))
        self.incheck.display()

        if self.incheck.clicked:
            if not self.incheck.checked:
                self.machine.make_node_initial(self.node)
            else:
                self.machine.make_node_uninitial(self.node)

        self.intext.set_position(self.location + pygame.Vector2(25, 5))
        self.intext.display()

        self.fincheck.set_position(self.location + pygame.Vector2(5, 30))
        self.fincheck.display()

        if self.fincheck.clicked:
            self.node.final = not self.fincheck.checked

        self.fintext.set_position(self.location + pygame.Vector2(25, 30))
        self.fintext.display()

        for event in pgx.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.rect.collidepoint(event.pos):
                    self.active = False


class TestMenu:
    def __init__(self, machine):
        width = 185
        height = 300

        location = pygame.Vector2(pygame.display.get_surface().get_width() - width, 150)

        surf = pygame.Surface((width, height))
        surf.fill("grey")
        self.background = pgx.ui.Image(surf, location)
        self.background.style.border = True
        self.background.style.cursor = pygame.SYSTEM_CURSOR_ARROW

        self.title = pgx.ui.Text("Testing Menu", location + pygame.Vector2(0, 10))
        self.title.style.text_width = width
        self.title.style.text_align = "center"
        self.title.style.font_size = 20

        self.headings = pgx.ui.Text(
            "  Input         In L   Rev of L", location + pygame.Vector2(5, 30)
        )
        self.headings.style.font_size = 14

        self.inputs = []
        self.outputs = []
        self.routputs = []
        n_spaces = 6
        for n in range(n_spaces):
            input_box = pgx.ui.Input(
                "", location + pygame.Vector2(5, 50 + n * 30), groups=["iobox"]
            )
            input_box.style.text_width = 70
            self.inputs.append(input_box)

            output_box = pgx.ui.Text(
                "", location + pygame.Vector2(80, 50 + n * 30), groups=["iobox"]
            )
            output_box.style.text_width = 40
            self.outputs.append(output_box)

            routput_box = pgx.ui.Text(
                "", location + pygame.Vector2(130, 50 + n * 30), groups=["iobox"]
            )
            routput_box.style.text_width = 40
            self.routputs.append(routput_box)

        self.test_button = pgx.ui.Text(
            "Run Tests", location + pygame.Vector2(10, 260), groups=["button"]
        )

        self.machine = machine

    def display(self):
        self.background.display()

        self.title.display()
        self.headings.display()

        for input_box in self.inputs:
            input_box.display()

        for output_box in self.outputs:
            output_box.display()

        for routput_box in self.routputs:
            routput_box.display()

        self.test_button.display()
        if self.test_button.clicked:
            for i in range(len(self.inputs)):
                input_box = self.inputs[i]
                # if input_box.text:
                output = self.machine.test(input_box.text)
                output_box = self.outputs[i]
                output_box.text = str(output)

                rev = "".join(reversed(list(input_box.text)))
                routput = self.machine.test(rev)
                routput_box = self.routputs[i]
                routput_box.text = str(routput)


class InfoOutput:
    def __init__(self):
        screen = pygame.display.get_surface()
        screen_out = pgx.ui.Text("", (10, screen.get_height() - 10))
        screen_out.style.align = pygame.Vector2(0, 1)
        screen_out.style.color = "red"
        screen_out.style.font_size = 20
        self.screen_out = screen_out

        self.screen_time = 5 * 1000  # ms
        self.last_input_time = 0

    def display(self) -> None:
        if pygame.time.get_ticks() - self.last_input_time > self.screen_time:
            self.screen_out.text = ""

        self.screen_out.display()

    def print(self, arg: str) -> None:
        self.last_input_time = pygame.time.get_ticks()
        self.screen_out.text = arg
