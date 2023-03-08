import socket

from dataclasses import dataclass
from typing import Final


"""
Steps in creating the UDP Echo Server

1. Create a UDP socket.
2. Bind it to an IP address and port.
3. Set up a while loop to:
    - loop until a KeyboardInterrupt happens
    - wait for data to be recieved
    - once it is
        - print out the data
        - echo the data back to the client
"""


@dataclass(frozen=True)
class Address:
    ip_address: str
    port: int


# Constants
MAXIMUM_TRANSMISSIBLE_UNIT: Final[int] = 1500  # MSS + TCP Header size + IP Packet Header size
SERVER_IP_ADDRESS: Final[str] = "127.0.0.1"
SERVER_PORT: Final[int] = 27685
DEFAULT_SERVER_ADDRESS: Final[Address] = Address(
    ip_address=SERVER_IP_ADDRESS,
    port=SERVER_PORT
)


class EchoServer:
    def __init__(
        self, 
        server_address: Address = DEFAULT_SERVER_ADDRESS
    ) -> None:
        self._server_address: Address = server_address
        self._sock: socket.socket = self._create_socket()


    def _create_socket(
        self
    ) -> socket.socket:
        """
        This method creates a UDP socket and is used 
        to assign a socket instance as an EchoServer
        class attribute.

        @return: An instance of socket.socket.
        """
        return socket.socket(
            socket.AF_INET, 
            socket.SOCK_DGRAM
        )

    def _bind_socket(self) -> None:
        """
        This is a convenience method to bind the
        EchoServer class' socket to the assigned
        server ip address and port.

        @return: None
        """
        self._sock.bind((
            self._server_address.ip_address,
            self._server_address.port
        ))

    def _print_data_and_remote_address(
        self,
        data: bytes, 
        remote_address: Address
    ) -> None:
        """
        This is a conveniece method to print out:
            1. The server's IP address and port.
            2. The data sent by the client.
            3. The client's IP address and port.

        @param: data - The bytes sent by the client.
        @param: remote_address - An instance of Address,
        representing an IP address and port.
        @return: None
        """
        print(
            "UDP server accepting datagrams on "
            f"{self._server_address.ip_address}:{self._server_address.port}\n"
        )
        print(f"Client sent: {data}\n")
        print(f"Sending {data} back to {remote_address.ip_address}:{remote_address.port}\n")

    def accept_connections_and_echo_data(self) -> None:
        """
        This method listens for an undetermined amount of time
        and accepts new messages from a client, prints out information
        about the request, and echoes the message back as a response.

        @return: None
        """
        self._bind_socket()

        while True:
            data, remote_address = self._sock.recvfrom(MAXIMUM_TRANSMISSIBLE_UNIT)  # MSS + TCP and IP headers (MTU)
            ip_address, port = remote_address

            self._print_data_and_remote_address(data, Address(ip_address, port))
            self._sock.sendto(data, remote_address)


if __name__ == "__main__":
    echo_server: EchoServer = EchoServer()
    echo_server.accept_connections_and_echo_data()
