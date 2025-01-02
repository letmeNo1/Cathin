import tkinter as tk
from platform_selection import create_platform_selection_window

def main():
    root = tk.Tk()
    root.title("Platform Selection")  # Set the window title
    root.geometry("500x200")  # Set the window size

    create_platform_selection_window(root)  # Create the platform selection window

    root.mainloop()

if __name__ == "__main__":
    main()