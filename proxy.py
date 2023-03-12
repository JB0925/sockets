import json
import socket

from dataclasses import dataclass
from typing import Dict, Final


"""
Steps in creating the TCP Echo Server

1. Create a TCP socket.
2. Bind it to an IP address and port.
3. Call "listen()".
    - Be sure to bind and listen outside of the while loop.
4. Set up a while loop to:
    - wait for new connections by calling "accept", which returns the remote socket and the client address.
    - call "recv" on the remote socket to get the data
    - send data back on the remote socket
    - close the remote connection
"""


@dataclass(frozen=True)
class Address:
    ip_address: str
    port: int


# Constants
MAXIMUM_TRANSMISSIBLE_UNIT: Final[int] = 1500  # MSS + TCP Header size + IP packet header size
SERVER_IP_ADDRESS: Final[str] = "127.0.0.1"
SERVER_PORT: Final[int] = 27685
DEFAULT_SERVER_ADDRESS: Final[Address] = Address(
    ip_address=SERVER_IP_ADDRESS,
    port=SERVER_PORT
)


class TCPServer:
    def __init__(self, server_address: Address = DEFAULT_SERVER_ADDRESS) -> None:
        self._server_address: Address = server_address
        self._sock: socket.socket = self._create_socket()
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def _create_socket(self) -> socket.socket:
        return socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

    def _bind_and_listen(self) -> None:
        self._sock.bind((self._server_address.ip_address, self._server_address.port))
        self._sock.listen(20)

    def _get_headers(self, data: bytes) -> bytes:
        raw_headers, _ = data.split(b"\r\n\r\n")
        parsed_headers: Dict[str, str] = {}

        for header in raw_headers.split(b"\r\n")[1:]:
            key, value = header.decode("ascii").split(": ")
            parsed_headers[key] = value

        return json.dumps(parsed_headers).encode("utf-8")

    def _print_data_and_remote_address(
        self,
        parsed_request_headers: bytes, 
        remote_address: Address
    ) -> None:
        """
        This is a conveniece method to print out:
            1. The server's IP address and port.
            2. The parsed_request_headers sent by the client.
            3. The client's IP address and port.

        @param: parsed_request_headers - The bytes sent by the client.
        @param: remote_address - An instance of Address,
        representing an IP address and port.
        @return: None
        """
        print(f"Client sent: {parsed_request_headers}\n")
        print(f"Sending {parsed_request_headers} back to {remote_address.ip_address}:{remote_address.port}\n")

    def _parse_true_destination_and_get_data(self, parsed_request_headers: bytes) -> bytes:
        true_destination = json.loads(parsed_request_headers.decode("ascii"))["X-Forwarded-For"]
        proxy_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dest_host, dest_port = true_destination.split(":")
        proxy_socket.connect((dest_host, int(dest_port)))

        """
        NOTE: The format of the "sendall" call directly below. This is because,
        if it is sent in a different way, it will be interpreted as HTTP/0.9,
        which is not allowed by curl.
        """
        proxy_socket.sendall(b"GET / HTTP/1.1\r\nHost: 127.0.0.1:8000\r\n\r\n")
        return_data: bytes = proxy_socket.recv(1500)
        proxy_socket.close()
        return return_data

    def accept_connections_and_return_data(self) -> None:
        self._bind_and_listen()

        print(
            "TCP server accepting connections on "
            f"{self._server_address.ip_address}:{self._server_address.port}\n"
        )

        while True:
            remote_connection, remote_address = self._sock.accept()
            request_data: bytes = remote_connection.recv(MAXIMUM_TRANSMISSIBLE_UNIT)
            parsed_request_headers: bytes = self._get_headers(request_data)
            return_data: bytes = self._parse_true_destination_and_get_data(parsed_request_headers)

            self._print_data_and_remote_address(
                parsed_request_headers,
                Address(remote_address[0], remote_address[1])
            )

            remote_connection.send(b"HTTP/1.1 200 OK\r\n\r\n")
            remote_connection.send(parsed_request_headers)
            remote_connection.send(return_data)
            remote_connection.close()


if __name__ == "__main__":
    tcp_server: TCPServer = TCPServer()
    tcp_server.accept_connections_and_return_data()
