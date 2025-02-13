import pygetwindow as gw

def getWindowsWithHandle(handle):
    for win in gw.getAllWindows():
        if int(win._hWnd) == int(handle):
            return win

def get_win_windows():
    windows = gw.getAllWindows()

    # Create a list to store the title and handle of each window
    titles_and_handles = []

    for window in windows:
        # Get the window title and handle
        title = window.title
        hwnd = window._hWnd
        # Combine the title and handle into a string and add it to the list
        titles_and_handles.append(f"{title},{hwnd}")
    return titles_and_handles

def get_mac_windows():
    windows = gw.getWindowsWithTitle('')
    window_titles = [title for title in windows if title]
    return window_titles