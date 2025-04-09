import socket
import threading
import curses
from curses.textpad import Textbox, rectangle
import sys
import platform

BUFFER_SIZE = 1024
DEFAULT_PORT = 6791  # Fixed port number

# Global flag for thread control
running = True

def clear_screen():
    """Cross-platform screen clearing"""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def receive_messages(sockfd, message_display_win):
    """Thread to receive messages from the server."""
    while running:
        try:
            # Set timeout to prevent blocking indefinitely
            sockfd.settimeout(1.0)
            response, _ = sockfd.recvfrom(BUFFER_SIZE)
            message = response.decode('utf-8')
            
            # Safely update the display window
            try:
                message_display_win.addstr(f"{message}\n")
                message_display_win.scrollok(True)
                message_display_win.refresh()
            except curses.error:
                pass  # Handle curses display errors silently
            
        except socket.timeout:
            continue  # Normal timeout, continue listening
        except socket.error as e:
            if running:  # Only display error if we're not shutting down
                try:
                    message_display_win.addstr(f"\nNetwork error: {e}\n")
                    message_display_win.refresh()
                except curses.error:
                    pass
            break
        except Exception as e:
            if running:
                try:
                    message_display_win.addstr(f"\nUnexpected error: {e}\n")
                    message_display_win.refresh()
                except curses.error:
                    pass
            break

def main(stdscr):
    """Main function to set up the client with a bordered interface."""
    global running
    
    try:
        # Initialize color pairs
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)

        # Clear the screen
        stdscr.clear()

        # Set up the window size (80x24)
        height, width = 24, 80
        start_y, start_x = 0, 0

        # Create a new window with a border
        win = curses.newwin(height, width, start_y, start_x)
        win.border()

        # Create a white top bar inside the border
        win.attron(curses.color_pair(1))
        win.addstr(0, 2, " PacketChat Client ", curses.A_BOLD)
        win.attroff(curses.color_pair(1))

        # Refresh the window to display the border and top bar
        win.refresh()

        # Create a subwindow for displaying messages
        message_display_win = curses.newwin(14, 76, 2, 2)
        rectangle(win, 1, 1, 16, 78)
        message_display_win.scrollok(True)
        message_display_win.refresh()

        # Get username
        curses.curs_set(1)
        win.addstr(17, 2, "Enter your username: ")
        rectangle(win, 18, 2, 20, 40)
        win.refresh()

        username_win = curses.newwin(1, 37, 19, 3)
        username_box = Textbox(username_win)
        username_box.edit()
        username = username_box.gather().strip()

        if not username:
            win.addstr(21, 2, "Username cannot be empty.")
            win.refresh()
            curses.napms(2000)
            return

        # Clear and redraw interface
        win.clear()
        win.border()
        win.addstr(0, 2, " PacketChat Client ", curses.A_BOLD)
        rectangle(win, 1, 1, 16, 78)
        win.refresh()

        # Get server hostname
        win.addstr(17, 2, "Enter server hostname or IP: ")
        rectangle(win, 18, 2, 20, 40)
        win.refresh()

        server_host_win = curses.newwin(1, 37, 19, 3)
        server_host_box = Textbox(server_host_win)
        server_host_box.edit()
        server_host = server_host_box.gather().strip()

        server_port = DEFAULT_PORT
        win.addstr(21, 2, f"Using fixed port: {server_port}")
        win.refresh()

        # Create UDP socket with proper error handling
        try:
            sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sockfd.settimeout(1.0)  # Set initial timeout
            
            # Platform-specific socket options
            if platform.system() == 'Windows':
                sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            else:
                sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            
            win.addstr(22, 2, "Socket created successfully.")
            win.refresh()
        except socket.error as e:
            win.addstr(22, 2, f"Socket creation failed: {e}")
            win.refresh()
            return

        server_addr = (server_host, server_port)

        # Clear and redraw interface
        win.clear()
        win.border()
        win.addstr(0, 2, " PacketChat Client ", curses.A_BOLD)
        rectangle(win, 1, 1, 16, 78)
        win.refresh()

        # Recreate message display window
        message_display_win = curses.newwin(14, 76, 2, 2)
        message_display_win.scrollok(True)
        message_display_win.refresh()

        # Start receive thread
        receive_thread = threading.Thread(
            target=receive_messages,
            args=(sockfd, message_display_win),
            daemon=True
        )
        receive_thread.start()

        # Message input loop
        while True:
            try:
                win.addstr(17, 2, "Enter Text: ")
                rectangle(win, 18, 2, 20, 77)
                win.refresh()

                message_win_input = curses.newwin(1, 74, 19, 3)
                message_box = Textbox(message_win_input)
                message_box.edit()
                message = message_box.gather().strip()

                if not message:
                    win.addstr(21, 2, "Message cannot be empty. Please try again.")
                    win.refresh()
                    curses.napms(2000)
                    win.addstr(21, 2, " " * 50)
                    win.refresh()
                    continue

                message_with_username = f"[{username}]: {message}"

                # Display your own message immediately
                try:
                    message_display_win.addstr(f"{message_with_username}\n")
                    message_display_win.refresh()
                except curses.error:
                    pass  # Handle display errors

                # Then send to server
                try:
                    sockfd.sendto(message_with_username.encode('utf-8'), server_addr)
                except socket.error as e:
                    win.addstr(21, 2, f"\nError sending message: {e}")
                    win.refresh()
                    break

            except KeyboardInterrupt:
                win.addstr(21, 2, "Exiting...")
                win.refresh()
                break
            except Exception as e:
                win.addstr(21, 2, f"\nUnexpected error: {e}")
                win.refresh()
                break

    finally:
        # Clean up
        running = False
        if 'sockfd' in locals():
            sockfd.close()
        if 'receive_thread' in locals():
            receive_thread.join(timeout=1.0)
        curses.endwin()

if __name__ == "__main__":
    # Initialize platform-specific settings
    if platform.system() == 'Windows':
        import os
        os.system('color')  # Enable ANSI colors on Windows
    
    curses.wrapper(main)