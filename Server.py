import socket
import sys

BUFFER_SIZE = 1024
MAX_CLIENTS = 100
SERVER_PORT = 6791  # Define the port the server will listen on

clients = []  # List to store client addresses


def add_client(client_addr):
    """Add a client to the list of known clients if not already present."""
    if client_addr not in clients:
        if len(clients) < MAX_CLIENTS:
            clients.append(client_addr)
            print(f"Added new client: {client_addr[0]}:{client_addr[1]}")
        else:
            print(f"Max clients reached. Cannot add client: {client_addr[0]}:{client_addr[1]}")


def broadcast_message(sockfd, message, sender_addr):
    """Send a message to all clients except the sender."""
    for client in clients:
        # Skip sending the message back to the sender
        if client == sender_addr:
            continue

        try:
            sockfd.sendto(message.encode('utf-8'), client)
            print(f"Message sent to client {client[0]}:{client[1]}")
        except Exception as e:
            print(f"Failed to send message to client {client[0]}:{client[1]}: {e}")
            # Remove dead clients
            if sys.platform == 'win32' and isinstance(e, socket.error) and e.winerror == 10054:
                print(f"Removing disconnected client: {client[0]}:{client[1]}")
                clients.remove(client)


def main():
    """Main function to set up the server and handle incoming messages."""
    try:
        # Create UDP socket
        sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set socket options for better behavior
        sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if sys.platform != 'win32':
            sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sockfd.bind(('', SERVER_PORT))  # Bind to all available interfaces
        print(f"Server is running and listening on port {SERVER_PORT}...")
    except socket.error as e:
        print(f"Socket creation or binding failed: {e}")
        return

    # Continuously receive and handle messages
    try:
        while True:
            try:
                # Set timeout for recvfrom to make KeyboardInterrupt responsive
                sockfd.settimeout(1.0)
                
                # Receive a message from a client
                message, client_addr = sockfd.recvfrom(BUFFER_SIZE)
                message = message.decode('utf-8')  # Decode the received message
                print(f"Received message from {client_addr[0]}:{client_addr[1]}: {message}")

                # Add the client to the list of known clients
                add_client(client_addr)

                # Broadcast the message to all clients except the sender
                broadcast_message(sockfd, message, client_addr)
                
            except socket.timeout:
                continue  # Timeout is normal, just check for KeyboardInterrupt
            except socket.error as e:
                if sys.platform == 'win32' and hasattr(e, 'winerror') and e.winerror == 10054:
                    print("Client forcibly closed connection (UDP - can be ignored)")
                    continue
                print(f"Socket error: {e}")
            except Exception as e:
                print(f"Error processing message: {e}")
                
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        # Clean up
        sockfd.close()
        print("Server socket closed.")


if __name__ == "__main__":
    main()