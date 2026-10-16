# Python Tetris

A clean, fast Tetris built in pure Python with tkinter. No pip installs, no extra files, just run it and play.

## Running it

You need Python 3 with tkinter, which ships with the standard Windows and macOS installers.

```
python tetris.py
```

Your best score is saved next to the script in `tetris_highscore.txt` and loads automatically the next time you open the game.

## How it plays

This is not a bare bones clone. It follows the conventions you would expect from a modern Tetris:

* Pieces come from a shuffled seven piece bag, so you never get starved of an I piece or flooded with the same shape.
* Rotation uses wall kicks. If a rotation would clip the wall or the stack, the game nudges the piece into a spot where it fits instead of refusing to turn.
* Pieces have a short lock delay after they touch down, giving you time to slide or spin before they settle. Moving the piece resets the delay, up to a limit so you cannot stall forever.
* You can hold one piece and swap it back in later, once per drop.
* The next three pieces are shown on the right so you can plan ahead.
* A ghost outline shows exactly where the current piece will land.
* Holding Left or Right moves the piece once, pauses briefly, then repeats quickly. Holding Down soft drops at a steady pace.
* Cleared lines flash white for a moment before they disappear.
* Pause any time with P or Escape.

## Scoring

Line clears pay 100, 300, 500 or 800 points for one through four lines, multiplied by your current level. A Tetris immediately after another Tetris pays 1200 instead of 800. Clearing lines on consecutive pieces builds a combo that adds a bonus on top. Soft dropping earns 1 point per row and hard dropping earns 2 per row.

You level up every ten lines and gravity speeds up with each level.

## Controls

Left and Right arrows move the piece.
Down arrow soft drops.
Space hard drops.
Up arrow or X rotates clockwise.
Z rotates counterclockwise.
C or Shift holds the current piece.
P or Escape pauses.
R restarts after a game over.

## Under the hood

The board is drawn once as a fixed grid of canvas rectangles and only the cells that actually change get updated each frame. That keeps the game smooth at high levels where a full redraw every tick would start to stutter.

Made by Bishal.
