import socket
import threading
import curses
from curses.textpad import Textbox, rectangle

BUFFER_SIZE = 1024
DEFAULT_PORT = 6791  # Fixed port number

def receive_messages(sockfd, message_display_win):
    """Thread to receive messages from the server."""
    while True:
        try:
            response, _ = sockfd.recvfrom(BUFFER_SIZE)
            message = response.decode('utf-8')
            message_display_win.addstr(f"{message}\n")
            message_display_win.scrollok(True)
            message_display_win.refresh()
        except socket.error as e:
            message_display_win.addstr(f"\nError receiving message: {e}\n")
            message_display_win.refresh()
            break

def main(stdscr):
    """Main function to set up the client with a bordered interface."""
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
    win.refresh()

    # Create a subwindow for displaying messages
    message_display_win = curses.newwin(14, 76, 2, 2)
    rectangle(win, 1, 1, 16, 78)
    message_display_win.scrollok(True)
    message_display_win.refresh()

    # Get username using a Textbox
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

    # Clear the username prompt and refresh for the next input
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

    # Use the fixed port
    server_port = DEFAULT_PORT
    win.addstr(21, 2, f"Using fixed port: {server_port}")
    win.refresh()

    # Create UDP socket
    try:
        sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        win.addstr(22, 2, "Socket created successfully.")
        win.refresh()
    except socket.error as e:
        win.addstr(22, 2, f"Socket creation failed: {e}")
        win.refresh()
        return

    server_addr = (server_host, server_port)

    # Clear the window and redraw the border for the messaging interface
    win.clear()
    win.border()
    win.addstr(0, 2, " PacketChat Client ", curses.A_BOLD)
    rectangle(win, 1, 1, 16, 78)
    win.refresh()

    # Redraw the message display window after clearing the main window
    message_display_win = curses.newwin(14, 76, 2, 2)
    message_display_win.scrollok(True)
    message_display_win.refresh()

    # Start a thread to listen for incoming messages
    threading.Thread(target=receive_messages, args=(sockfd, message_display_win), daemon=True).start()

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

            # Prepend the username to the message
            message_with_username = f"[{username}]: {message}"
            
            # Display your own message immediately
            message_display_win.addstr(f"{message_with_username}\n")
            message_display_win.refresh()
            
            # Send the message to the server
            sockfd.sendto(message_with_username.encode('utf-8'), server_addr)

        except KeyboardInterrupt:
            win.addstr(21, 2, "\nExiting...")
            win.refresh()
            break
        except Exception as e:
            win.addstr(21, 2, f"\nError sending message: {e}")
            win.refresh()
            break

    sockfd.close()

if __name__ == "__main__":
    curses.wrapper(main)