import curses

def main(stdscr):
    # Start colors in curses
    curses.start_color()
    
    # Define a new color for gray if the terminal supports it
    if curses.can_change_color():
        # RGB values for gray (in range 0-1000)
        curses.init_color(8, 500, 500, 500)  # 8 is the index for gray
    
    # Initialize color pair for gray on black
    curses.init_pair(1, 8, curses.COLOR_BLACK)
    
    # Use the color pair
    stdscr.addstr(0, 0, "This is gray on black", curses.color_pair(1) | curses.A_REVERSE)
    
    stdscr.refresh()
    stdscr.getch()

# Initialize curses
curses.wrapper(main)
