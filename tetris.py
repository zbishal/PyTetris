import os
import random
import tkinter as tk

BLOCK_SIZE = 32
PREVIEW_BLOCK = 22
GRID_WIDTH = 10
GRID_HEIGHT = 20
NEXT_QUEUE_SIZE = 3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HIGH_SCORE_FILE = os.path.join(BASE_DIR, "tetris_highscore.txt")

TICK_MS = 16
DAS_DELAY = 150
ARR_RATE = 30
SOFT_DROP_RATE = 40
LOCK_DELAY = 500
MAX_LOCK_RESETS = 15
CLEAR_FLASH_MS = 90

BG = "#1c1c1c"
BOARD_BG = "#101010"
GRID_LINE = "#181818"
BLOCK_EDGE = "#282828"
TEXT = "#FFFFFF"
MUTED = "#7a7a7a"
FLASH = "#FFFFFF"

SHAPES = [
    [[1, 1, 1, 1]],
    [[1, 1], [1, 1]],
    [[0, 1, 0], [1, 1, 1]],
    [[1, 0, 0], [1, 1, 1]],
    [[0, 0, 1], [1, 1, 1]],
    [[1, 1, 0], [0, 1, 1]],
    [[0, 1, 1], [1, 1, 0]],
]

COLORS = [
    "#00E5E5",
    "#E5E500",
    "#BE00E5",
    "#0040E5",
    "#E58000",
    "#40E500",
    "#E50000",
]

KICKS = [(0, 0), (-1, 0), (1, 0), (0, -1), (-1, -1), (1, -1), (-2, 0), (2, 0), (0, -2)]

LINE_SCORES = [0, 100, 300, 500, 800]
TETRIS_B2B_SCORE = 1200
COMBO_SCORE = 50
SOFT_DROP_SCORE = 1
HARD_DROP_SCORE = 2


class Piece:
    def __init__(self, index):
        self.index = index
        self.shape = [list(row) for row in SHAPES[index]]
        self.color = COLORS[index]
        self.x = GRID_WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0

    def rotated(self, clockwise=True):
        if clockwise:
            return [list(row) for row in zip(*self.shape[::-1])]
        return [list(row) for row in zip(*self.shape)][::-1]


class Tetris:
    def __init__(self, master):
        self.master = master
        self.master.title("Python Tetris")
        self.master.configure(bg=BG)
        self.master.resizable(False, False)

        self.high_score = self.load_high_score()
        self.overlay_ids = []

        self.build_ui()
        self.master.bind("<KeyPress>", self.on_key_press)
        self.master.bind("<KeyRelease>", self.on_key_release)
        self.master.focus_set()

        self.start_game()
        self.loop()

    def build_ui(self):
        main = tk.Frame(self.master, bg=BG)
        main.pack(padx=20, pady=20)

        left = tk.Frame(main, bg=BG)
        left.pack(side=tk.LEFT, padx=(0, 20), anchor=tk.N)

        self.make_heading(left, "Hold")
        self.hold_canvas = tk.Canvas(
            left,
            width=5 * PREVIEW_BLOCK,
            height=4 * PREVIEW_BLOCK,
            bg=BOARD_BG,
            highlightthickness=0,
        )
        self.hold_canvas.pack(pady=(4, 28))

        self.score_value = self.make_stat(left, "Score")
        self.level_value = self.make_stat(left, "Level")
        self.lines_value = self.make_stat(left, "Lines")
        self.high_value = self.make_stat(left, "Best")

        self.canvas = tk.Canvas(
            main,
            width=GRID_WIDTH * BLOCK_SIZE,
            height=GRID_HEIGHT * BLOCK_SIZE,
            bg=BOARD_BG,
            highlightthickness=0,
        )
        self.canvas.pack(side=tk.LEFT)

        right = tk.Frame(main, bg=BG)
        right.pack(side=tk.LEFT, padx=(20, 0), anchor=tk.N)

        self.make_heading(right, "Next")
        self.next_canvas = tk.Canvas(
            right,
            width=5 * PREVIEW_BLOCK,
            height=(NEXT_QUEUE_SIZE * 3 + 1) * PREVIEW_BLOCK,
            bg=BOARD_BG,
            highlightthickness=0,
        )
        self.next_canvas.pack(pady=(4, 28))

        controls = (
            "Left / Right  Move\n"
            "Down          Soft drop\n"
            "Space         Hard drop\n"
            "Up / X        Rotate CW\n"
            "Z             Rotate CCW\n"
            "C / Shift     Hold\n"
            "P / Esc       Pause\n"
            "R             Restart"
        )
        tk.Label(
            right,
            text=controls,
            font=("Consolas", 9),
            fg=MUTED,
            bg=BG,
            justify=tk.LEFT,
        ).pack(anchor=tk.W)

        self.build_board_cells()

    def make_heading(self, parent, text):
        label = tk.Label(parent, text=text, font=("Consolas", 14, "bold"), fg=TEXT, bg=BG)
        label.pack(anchor=tk.W)
        return label

    def make_stat(self, parent, title):
        tk.Label(parent, text=title, font=("Consolas", 11), fg=MUTED, bg=BG).pack(anchor=tk.W)
        value = tk.Label(parent, text="0", font=("Consolas", 20, "bold"), fg=TEXT, bg=BG)
        value.pack(anchor=tk.W, pady=(0, 14))
        return value

    def build_board_cells(self):
        board_w = GRID_WIDTH * BLOCK_SIZE
        board_h = GRID_HEIGHT * BLOCK_SIZE
        for i in range(1, GRID_WIDTH):
            self.canvas.create_line(i * BLOCK_SIZE, 0, i * BLOCK_SIZE, board_h, fill=GRID_LINE)
        for i in range(1, GRID_HEIGHT):
            self.canvas.create_line(0, i * BLOCK_SIZE, board_w, i * BLOCK_SIZE, fill=GRID_LINE)

        self.cells = []
        self.cell_state = []
        for y in range(GRID_HEIGHT):
            row = []
            state_row = []
            for x in range(GRID_WIDTH):
                x1 = x * BLOCK_SIZE
                y1 = y * BLOCK_SIZE
                x2 = x1 + BLOCK_SIZE
                y2 = y1 + BLOCK_SIZE
                outer = self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill="", outline="", width=2, state=tk.HIDDEN
                )
                inner = self.canvas.create_rectangle(
                    x1 + 3, y1 + 3, x2 - 3, y2 - 3,
                    fill=TEXT, outline="", stipple="gray12", state=tk.HIDDEN,
                )
                row.append((outer, inner))
                state_row.append(None)
            self.cells.append(row)
            self.cell_state.append(state_row)

    def start_game(self):
        self.grid = [[None] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
        self.score = 0
        self.level = 1
        self.lines = 0
        self.combo = -1
        self.back_to_back = False
        self.game_over = False
        self.paused = False

        self.keys = set()
        self.das = {"Left": 0, "Right": 0}
        self.arr = {"Left": 0, "Right": 0}
        self.soft_timer = 0
        self.gravity_timer = 0
        self.gravity_ms = self.gravity_for_level(1)

        self.lock_timer = 0
        self.lock_resets = 0
        self.lowest_y = 0

        self.clearing_rows = []
        self.clear_timer = 0

        self.bag = []
        self.queue = [self.draw_from_bag() for _ in range(NEXT_QUEUE_SIZE)]
        self.held = None
        self.can_hold = True
        self.current = None
        self.ghost_y = 0

        self.clear_overlay()
        self.hold_canvas.delete("all")
        self.dirty = True
        self.update_stats()
        self.spawn_piece()

    def gravity_for_level(self, level):
        return max(60, int(600 * (0.85 ** (level - 1))))

    def draw_from_bag(self):
        if not self.bag:
            self.bag = list(range(len(SHAPES)))
            random.shuffle(self.bag)
        return self.bag.pop()

    def spawn_piece(self, index=None):
        if index is None:
            index = self.queue.pop(0)
            self.queue.append(self.draw_from_bag())
            self.can_hold = True
        self.current = Piece(index)
        self.gravity_timer = 0
        self.lock_timer = 0
        self.lock_resets = 0
        self.lowest_y = 0
        self.update_ghost()
        self.draw_preview(self.next_canvas, self.queue)
        self.dirty = True
        if self.collides(self.current.shape, self.current.x, self.current.y):
            self.end_game()

    def collides(self, shape, px, py):
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if not cell:
                    continue
                gx = px + x
                gy = py + y
                if gx < 0 or gx >= GRID_WIDTH or gy < 0 or gy >= GRID_HEIGHT:
                    return True
                if self.grid[gy][gx] is not None:
                    return True
        return False

    def on_ground(self):
        return self.collides(self.current.shape, self.current.x, self.current.y + 1)

    def update_ghost(self):
        y = self.current.y
        while not self.collides(self.current.shape, self.current.x, y + 1):
            y += 1
        self.ghost_y = y

    def after_successful_move(self, vertical):
        self.update_ghost()
        self.dirty = True
        if vertical:
            if self.current.y > self.lowest_y:
                self.lowest_y = self.current.y
                self.lock_resets = 0
                self.lock_timer = 0
        elif self.on_ground() and self.lock_resets < MAX_LOCK_RESETS:
            self.lock_timer = 0
            self.lock_resets += 1

    def try_move(self, dx, dy):
        nx = self.current.x + dx
        ny = self.current.y + dy
        if self.collides(self.current.shape, nx, ny):
            return False
        self.current.x = nx
        self.current.y = ny
        self.after_successful_move(dy != 0)
        return True

    def rotate(self, clockwise):
        shape = self.current.rotated(clockwise)
        for kx, ky in KICKS:
            nx = self.current.x + kx
            ny = self.current.y + ky
            if not self.collides(shape, nx, ny):
                self.current.shape = shape
                self.current.x = nx
                self.current.y = ny
                self.after_successful_move(False)
                return True
        return False

    def hard_drop(self):
        distance = self.ghost_y - self.current.y
        self.current.y = self.ghost_y
        if distance > 0:
            self.add_score(distance * HARD_DROP_SCORE)
        self.lock_piece()

    def hold(self):
        if not self.can_hold:
            return
        previous = self.held
        self.held = self.current.index
        self.draw_preview(self.hold_canvas, [self.held])
        if previous is None:
            self.spawn_piece()
        else:
            self.spawn_piece(previous)
        self.can_hold = False

    def on_key_press(self, event):
        key = event.keysym
        if len(key) == 1:
            key = key.lower()
        if key in self.keys:
            return
        self.keys.add(key)

        if self.game_over:
            if key == "r":
                self.start_game()
            return

        if key in ("p", "Escape"):
            self.toggle_pause()
            return

        if self.paused or self.current is None or self.clearing_rows:
            return

        if key == "Left":
            self.das["Left"] = 0
            self.arr["Left"] = ARR_RATE
            self.try_move(-1, 0)
        elif key == "Right":
            self.das["Right"] = 0
            self.arr["Right"] = ARR_RATE
            self.try_move(1, 0)
        elif key == "Down":
            self.soft_timer = SOFT_DROP_RATE
        elif key in ("Up", "x"):
            self.rotate(True)
        elif key == "z":
            self.rotate(False)
        elif key == "space":
            self.hard_drop()
        elif key in ("c", "Shift_L", "Shift_R"):
            self.hold()

    def on_key_release(self, event):
        key = event.keysym
        if len(key) == 1:
            key = key.lower()
        self.keys.discard(key)
        if key in self.das:
            self.das[key] = 0
            self.arr[key] = 0

    def handle_held_keys(self):
        for side, dx in (("Left", -1), ("Right", 1)):
            if side not in self.keys:
                continue
            self.das[side] += TICK_MS
            if self.das[side] < DAS_DELAY:
                continue
            self.arr[side] += TICK_MS
            if self.arr[side] >= ARR_RATE:
                self.arr[side] -= ARR_RATE
                self.try_move(dx, 0)

        if "Down" in self.keys:
            self.soft_timer += TICK_MS
            if self.soft_timer >= SOFT_DROP_RATE:
                self.soft_timer -= SOFT_DROP_RATE
                if self.try_move(0, 1):
                    self.add_score(SOFT_DROP_SCORE)

    def lock_piece(self):
        for y, row in enumerate(self.current.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.grid[self.current.y + y][self.current.x + x] = self.current.color
        self.current = None
        self.dirty = True

        full_rows = [y for y, row in enumerate(self.grid) if all(row)]
        if full_rows:
            self.clearing_rows = full_rows
            self.clear_timer = 0
        else:
            self.combo = -1
            self.spawn_piece()

    def finish_clear(self):
        count = len(self.clearing_rows)
        for y in sorted(self.clearing_rows):
            del self.grid[y]
            self.grid.insert(0, [None] * GRID_WIDTH)
        self.clearing_rows = []

        self.combo += 1
        points = LINE_SCORES[count]
        if count == 4:
            if self.back_to_back:
                points = TETRIS_B2B_SCORE
            self.back_to_back = True
        else:
            self.back_to_back = False
        points *= self.level
        if self.combo > 0:
            points += COMBO_SCORE * self.combo * self.level
        self.add_score(points)

        self.lines += count
        new_level = self.lines // 10 + 1
        if new_level > self.level:
            self.level = new_level
            self.gravity_ms = self.gravity_for_level(self.level)

        self.update_stats()
        self.spawn_piece()

    def add_score(self, points):
        self.score += points
        self.score_value.config(text=str(self.score))

    def update_stats(self):
        self.score_value.config(text=str(self.score))
        self.level_value.config(text=str(self.level))
        self.lines_value.config(text=str(self.lines))
        self.high_value.config(text=str(self.high_score))

    def load_high_score(self):
        if not os.path.exists(HIGH_SCORE_FILE):
            return 0
        try:
            with open(HIGH_SCORE_FILE, "r") as f:
                return int(f.read().strip() or 0)
        except (ValueError, OSError):
            return 0

    def save_high_score(self):
        if self.score <= self.high_score:
            return
        self.high_score = self.score
        try:
            with open(HIGH_SCORE_FILE, "w") as f:
                f.write(str(self.high_score))
        except OSError:
            pass
        self.high_value.config(text=str(self.high_score))

    def draw_preview(self, canvas, indices):
        canvas.delete("all")
        canvas_w = int(canvas["width"])
        slot_h = 3 * PREVIEW_BLOCK
        for slot, index in enumerate(indices):
            shape = SHAPES[index]
            color = COLORS[index]
            w = len(shape[0]) * PREVIEW_BLOCK
            h = len(shape) * PREVIEW_BLOCK
            ox = (canvas_w - w) / 2
            oy = slot * slot_h + (slot_h - h) / 2 + PREVIEW_BLOCK / 2
            for y, row in enumerate(shape):
                for x, cell in enumerate(row):
                    if not cell:
                        continue
                    x1 = ox + x * PREVIEW_BLOCK
                    y1 = oy + y * PREVIEW_BLOCK
                    x2 = x1 + PREVIEW_BLOCK
                    y2 = y1 + PREVIEW_BLOCK
                    canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=BLOCK_EDGE, width=2)
                    canvas.create_rectangle(
                        x1 + 2, y1 + 2, x2 - 2, y2 - 2,
                        fill=TEXT, outline="", stipple="gray12",
                    )

    def render(self):
        if not self.dirty:
            return
        self.dirty = False

        desired = [[("empty", None) for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        for y, row in enumerate(self.grid):
            for x, color in enumerate(row):
                if color is not None:
                    desired[y][x] = ("block", color)

        for y in self.clearing_rows:
            for x in range(GRID_WIDTH):
                desired[y][x] = ("block", FLASH)

        if self.current is not None:
            piece = self.current
            for y, row in enumerate(piece.shape):
                for x, cell in enumerate(row):
                    if not cell:
                        continue
                    gx = piece.x + x
                    gy = self.ghost_y + y
                    if 0 <= gy < GRID_HEIGHT and desired[gy][gx][0] == "empty":
                        desired[gy][gx] = ("ghost", piece.color)
            for y, row in enumerate(piece.shape):
                for x, cell in enumerate(row):
                    if cell:
                        desired[piece.y + y][piece.x + x] = ("block", piece.color)

        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                state = desired[y][x]
                if state != self.cell_state[y][x]:
                    self.cell_state[y][x] = state
                    self.apply_cell(y, x, state)

    def apply_cell(self, y, x, state):
        outer, inner = self.cells[y][x]
        kind, color = state
        if kind == "block":
            self.canvas.itemconfig(outer, fill=color, outline=BLOCK_EDGE, state=tk.NORMAL)
            self.canvas.itemconfig(inner, state=tk.NORMAL)
        elif kind == "ghost":
            self.canvas.itemconfig(outer, fill="", outline=color, state=tk.NORMAL)
            self.canvas.itemconfig(inner, state=tk.HIDDEN)
        else:
            self.canvas.itemconfig(outer, state=tk.HIDDEN)
            self.canvas.itemconfig(inner, state=tk.HIDDEN)

    def show_overlay(self, title, subtitle):
        self.clear_overlay()
        w = GRID_WIDTH * BLOCK_SIZE
        h = GRID_HEIGHT * BLOCK_SIZE
        self.overlay_ids.append(
            self.canvas.create_rectangle(0, 0, w, h, fill="#000000", outline="", stipple="gray50")
        )
        self.overlay_ids.append(
            self.canvas.create_text(w / 2, h / 2 - 30, text=title, font=("Consolas", 36, "bold"), fill=TEXT)
        )
        self.overlay_ids.append(
            self.canvas.create_text(w / 2, h / 2 + 24, text=subtitle, font=("Consolas", 14), fill=TEXT)
        )

    def clear_overlay(self):
        for item in self.overlay_ids:
            self.canvas.delete(item)
        self.overlay_ids = []

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.show_overlay("PAUSED", "Press P to resume")
        else:
            self.clear_overlay()

    def end_game(self):
        self.game_over = True
        self.save_high_score()
        self.show_overlay("GAME OVER", "Press R to restart")

    def step(self):
        if self.clearing_rows:
            self.clear_timer += TICK_MS
            if self.clear_timer >= CLEAR_FLASH_MS:
                self.finish_clear()
            return

        self.handle_held_keys()
        if self.current is None:
            return

        self.gravity_timer += TICK_MS
        if self.gravity_timer >= self.gravity_ms:
            self.gravity_timer -= self.gravity_ms
            self.try_move(0, 1)

        if self.current is None:
            return

        if self.on_ground():
            self.lock_timer += TICK_MS
            if self.lock_timer >= LOCK_DELAY:
                self.lock_piece()
        else:
            self.lock_timer = 0

    def loop(self):
        if not self.game_over and not self.paused:
            self.step()
        self.render()
        self.master.after(TICK_MS, self.loop)


if __name__ == "__main__":
    root = tk.Tk()
    Tetris(root)
    root.mainloop()
