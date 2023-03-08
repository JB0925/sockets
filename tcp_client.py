import json
import socket


"""
Steps involved in creating a basic TCP client:

1. Connect to the remote server.
2. Send the data via "sock.sendall(data)"
3. Call "recv()" to get data from the remote server.
4. Close the socket.
5. Print the data.
"""

while True:
    sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data: bytes = b"beebo"  # just sending whatever here
    sock.connect(("127.0.0.1", 27685))
    sock.sendall(data)

    data: bytes = sock.recv(1500)
    sock.close()
    print(json.loads(data))
    break
