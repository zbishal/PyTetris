import tkinter as tk
import random
import os

BLOCK_SIZE = 32
GRID_WIDTH = 10
GRID_HEIGHT = 20
HIGH_SCORE_FILE = "tetris_highscore.txt"

GAME_TICK_RATE = 16
DAS_DELAY = 160
ARR_RATE = 32
SOFT_DROP_RATE = 48

SHAPES = [
    [[1, 1, 1, 1]],
    [[1, 1], [1, 1]],
    [[0, 1, 0], [1, 1, 1]],
    [[1, 0, 0], [1, 1, 1]],
    [[0, 0, 1], [1, 1, 1]],
    [[1, 1, 0], [0, 1, 1]],
    [[0, 1, 1], [1, 1, 0]]
]

COLORS = [
    "#00E5E5",  # I-Block: Cyan color
    "#E5E500",  # O-Block: Yellow colorrrr
    "#BE00E5",  # T-Block: Purple color
    "#0040E5",  # J-Block: Deep Blue color
    "#E58000",  # L-Block: Orange color
    "#40E500",  # S-Block: Green color
    "#E50000"   # Z-Block: Red color
]

class Tetris:
    def __init__(self, master):
        self.master = master
        self.master.title("Python Tetris - By Bishal")
        self.master.configure(bg="#1c1c1c")

        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.high_score = self.load_high_score()
        
        main_frame = tk.Frame(self.master, bg="#1c1c1c")
        main_frame.pack(padx=20, pady=20)

        self.canvas = tk.Canvas(main_frame, width=GRID_WIDTH * BLOCK_SIZE, height=GRID_HEIGHT * BLOCK_SIZE, bg="#101010", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=(0, 20))

        side_panel = tk.Frame(main_frame, bg="#1c1c1c")
        side_panel.pack(side=tk.RIGHT)
        self.setup_side_panel(side_panel)
        
        self.master.bind("<KeyPress>", self.handle_key_press)
        self.master.bind("<KeyRelease>", self.handle_key_release)
        self.master.focus_set()

        self.start_game()

    def setup_side_panel(self, parent):
        font_style = ("Consolas", 18, "bold")
        fg_color, bg_color = "#FFFFFF", "#1c1c1c"

        self.high_score_label = tk.Label(parent, text=f"High Score\n{self.high_score}", font=font_style, fg=fg_color, bg=bg_color, justify=tk.CENTER)
        self.high_score_label.pack(pady=(0, 40))
        self.score_label = tk.Label(parent, text="Score\n0", font=font_style, fg=fg_color, bg=bg_color, justify=tk.CENTER)
        self.score_label.pack(pady=(0, 40))
        self.level_label = tk.Label(parent, text="Level\n1", font=font_style, fg=fg_color, bg=bg_color, justify=tk.CENTER)
        self.level_label.pack(pady=(0, 40))

        tk.Label(parent, text="Next", font=font_style, fg=fg_color, bg=bg_color).pack()
        self.next_piece_canvas = tk.Canvas(parent, width=5 * BLOCK_SIZE, height=5 * BLOCK_SIZE, bg="#101010", highlightthickness=0)
        self.next_piece_canvas.pack(pady=10)
        
        tk.Label(parent, text='Credit: Bishal | 2025.8.v1', font=("Consolas", 9), fg="#505050", bg=bg_color).pack(side=tk.BOTTOM, pady=(60, 0))

    def start_game(self):
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.score, self.level, self.lines_cleared = 0, 1, 0
        self.gravity_speed, self.game_over = 500, False
        
        self.keys_pressed = set()
        self.das_timer_left, self.das_timer_right, self.soft_drop_timer = 0, 0, 0
        self.gravity_timer = 0

        self.score_label.config(text=f"Score\n{self.score}")
        self.level_label.config(text=f"Level\n{self.level}")
        
        self.next_piece = self.get_new_piece()
        self.new_piece()
        self.update_game()

    def handle_key_press(self, event):
        key = event.keysym
        if self.game_over:
            if key == 'r': self.start_game()
            return
        
        if key not in self.keys_pressed:
            self.keys_pressed.add(key)
            if key == 'Left':
                self.das_timer_left = 0
                self.move_piece(-1, 0)
            elif key == 'Right':
                self.das_timer_right = 0
                self.move_piece(1, 0)
        
        if key == 'Up': self.rotate_piece()
        elif key == 'space': self.hard_drop()

    def handle_key_release(self, event):
        key = event.keysym
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)
        if key == 'Left': self.das_timer_left = 0
        elif key == 'Right': self.das_timer_right = 0

    def handle_continuous_movement(self, delta_time):
        if 'Left' in self.keys_pressed:
            self.das_timer_left += delta_time
            if self.das_timer_left > DAS_DELAY:
                self.das_timer_left %= ARR_RATE
                self.move_piece(-1, 0)
        
        if 'Right' in self.keys_pressed:
            self.das_timer_right += delta_time
            if self.das_timer_right > DAS_DELAY:
                self.das_timer_right %= ARR_RATE
                self.move_piece(1, 0)
        
        if 'Down' in self.keys_pressed:
            self.soft_drop_timer += delta_time
            if self.soft_drop_timer > SOFT_DROP_RATE:
                self.soft_drop_timer %= SOFT_DROP_RATE
                if not self.move_piece(0, 1):
                    self.lock_piece()

    def load_high_score(self):
        if not os.path.exists(HIGH_SCORE_FILE): return 0
        with open(HIGH_SCORE_FILE, "r") as f:
            try: return int(f.read())
            except (ValueError, TypeError): return 0

    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            with open(HIGH_SCORE_FILE, "w") as f: f.write(str(self.high_score))
            self.high_score_label.config(text=f"High Score\n{self.high_score}")

    def get_new_piece(self):
        shape_index = random.randint(0, len(SHAPES) - 1)
        return {"shape": SHAPES[shape_index], "color": COLORS[shape_index], "x": GRID_WIDTH // 2 - len(SHAPES[shape_index][0]) // 2, "y": 0}

    def new_piece(self):
        self.current_piece = self.next_piece
        self.next_piece = self.get_new_piece()
        self.update_ghost_piece()
        self.draw_next_piece()
        if self.check_collision(self.current_piece["shape"], (self.current_piece["x"], self.current_piece["y"])):
            self.game_over = True

    def check_collision(self, shape, pos):
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_x, grid_y = pos[0] + x, pos[1] + y
                    if not (0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT and self.grid[grid_y][grid_x] is None):
                        return True
        return False

    def move_piece(self, dx, dy):
        new_x = self.current_piece["x"] + dx
        new_y = self.current_piece["y"] + dy
        if not self.check_collision(self.current_piece["shape"], (new_x, new_y)):
            self.current_piece["x"], self.current_piece["y"] = new_x, new_y
            self.update_ghost_piece()
            return True
        return False

    def rotate_piece(self):
        rotated_shape = [list(row) for row in zip(*self.current_piece["shape"][::-1])]
        if not self.check_collision(rotated_shape, (self.current_piece["x"], self.current_piece["y"])):
            self.current_piece["shape"] = rotated_shape
            self.update_ghost_piece()

    def hard_drop(self):
        self.current_piece["y"] = self.ghost_piece["y"]
        self.lock_piece()

    def lock_piece(self):
        for y, row in enumerate(self.current_piece["shape"]):
            for x, cell in enumerate(row):
                if cell: self.grid[self.current_piece["y"] + y][self.current_piece["x"] + x] = self.current_piece["color"]
        self.clear_lines()
        self.new_piece()

    def clear_lines(self):
        lines_to_clear = [i for i, row in enumerate(self.grid) if all(row)]
        cleared_count = len(lines_to_clear)
        for i in lines_to_clear:
            del self.grid[i]
            self.grid.insert(0, [None for _ in range(GRID_WIDTH)])
        if cleared_count > 0:
            self.score += [0, 100, 300, 500, 800][cleared_count] * self.level
            self.lines_cleared += cleared_count
            self.score_label.config(text=f"Score\n{self.score}")
            self.update_level()

    def update_level(self):
        new_level = (self.lines_cleared // 10) + 1
        if new_level > self.level:
            self.level = new_level
            self.gravity_speed = max(100, 500 - (self.level - 1) * 40)
            self.level_label.config(text=f"Level\n{self.level}")

    def update_ghost_piece(self):
        self.ghost_piece = self.current_piece.copy()
        while not self.check_collision(self.ghost_piece["shape"], (self.ghost_piece["x"], self.ghost_piece["y"] + 1)):
            self.ghost_piece["y"] += 1

    def draw_block(self, canvas, x, y, color, is_ghost=False):
        x1, y1, x2, y2 = x * BLOCK_SIZE, y * BLOCK_SIZE, (x + 1) * BLOCK_SIZE, (y + 1) * BLOCK_SIZE
        if is_ghost:
            canvas.create_rectangle(x1, y1, x2, y2, fill="", outline=color, width=2)
        else:
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#282828", width=2)
            canvas.create_rectangle(x1 + 3, y1 + 3, x2 - 3, y2 - 3, fill=color, outline="#FFFFFF", width=1, stipple="gray12")

    def draw_board(self):
        self.canvas.delete("all")
        for i in range(1, GRID_WIDTH): self.canvas.create_line(i * BLOCK_SIZE, 0, i * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE, fill="#181818")
        for i in range(1, GRID_HEIGHT): self.canvas.create_line(0, i * BLOCK_SIZE, GRID_WIDTH * BLOCK_SIZE, i * BLOCK_SIZE, fill="#181818")
        
        for y, row in enumerate(self.grid):
            for x, color in enumerate(row):
                if color: self.draw_block(self.canvas, x, y, color)
        
        for y, row in enumerate(self.ghost_piece["shape"]):
            for x, cell in enumerate(row):
                if cell: self.draw_block(self.canvas, self.ghost_piece["x"] + x, self.ghost_piece["y"] + y, self.ghost_piece["color"], True)

        for y, row in enumerate(self.current_piece["shape"]):
            for x, cell in enumerate(row):
                if cell: self.draw_block(self.canvas, self.current_piece["x"] + x, self.current_piece["y"] + y, self.current_piece["color"])

    def draw_next_piece(self):
        self.next_piece_canvas.delete("all")
        shape = self.next_piece["shape"]
        start_x = (5 * BLOCK_SIZE - len(shape[0]) * BLOCK_SIZE) / 2
        start_y = (5 * BLOCK_SIZE - len(shape) * BLOCK_SIZE) / 2
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell: self.draw_block(self.next_piece_canvas, start_x / BLOCK_SIZE + x, start_y / BLOCK_SIZE + y, self.next_piece["color"])

    def update_game(self):
        if not self.game_over:
            self.gravity_timer += GAME_TICK_RATE
            self.handle_continuous_movement(GAME_TICK_RATE)
            
            if self.gravity_timer > self.gravity_speed:
                self.gravity_timer %= self.gravity_speed
                if not self.move_piece(0, 1):
                    self.lock_piece()
            
            self.draw_board()
            self.master.after(GAME_TICK_RATE, self.update_game)
        else:
            self.save_high_score()
            self.canvas.create_rectangle(0, 0, GRID_WIDTH * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE, fill="#000000", stipple="gray50")
            self.canvas.create_text((GRID_WIDTH * BLOCK_SIZE) / 2, (GRID_HEIGHT * BLOCK_SIZE) / 2 - 40, text="GAME OVER", font=("Consolas", 40, "bold"), fill="white")
            self.canvas.create_text((GRID_WIDTH * BLOCK_SIZE) / 2, (GRID_HEIGHT * BLOCK_SIZE) / 2 + 20, text="Press 'R' to Restart", font=("Consolas", 16), fill="white")

if __name__ == "__main__":
    root = tk.Tk()
    game = Tetris(root)
    root.mainloop()