import selectors
import socket
import types

from typing import Any, Final, List, NamedTuple, Tuple


class Address(NamedTuple):
    ip_address: str
    port: int


# Constants
SERVER_ADDRESS: Final[str] = "127.0.0.1"
SERVER_PORT: Final[int] = 27685
DEFAULT_SERVER_ADDRESS: Address = Address(SERVER_ADDRESS, SERVER_PORT)
MAXIMUM_TRANSMISSIBLE_UNIT: int = 1500
ZERO_CONTENT_LENGTH: Final[int] = 0


class TCPServer:
    def __init__(
            self, 
            server_address: Address = DEFAULT_SERVER_ADDRESS
    ) -> None:
        self._server_address: Address = server_address
        self._sock: socket.socket = self._create_socket()
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._selector: selectors.DefaultSelector = selectors.DefaultSelector()

    def _create_socket(self) -> socket.socket:
        return socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

    def _bind_and_listen(self) -> None:
        self._sock.bind(
            (self._server_address.ip_address,
             self._server_address.port
        ))
        self._sock.listen()
        self._sock.setblocking(0)
        self._selector.register(self._sock, selectors.EVENT_READ, data=None)

    def _get_content_length_from_client(self, recv_data: bytes) -> int:
        cl_header = recv_data.split(b"\r\n")[1:]
        for item in cl_header:
            if b"Content-Length" in item:
                return int(item.split(b": ")[1])

        return ZERO_CONTENT_LENGTH


    def accept_connections_and_echo(self):
        self._bind_and_listen()

        # Event Loop
        while True:
            """
            "events" is a list of tuples.
                - events[0] is a SelectorKey object, which has the following attributes:
                    - key.fileobj - a TCP socket to read from / write to, and close
                    - key.fd - a file descriptor (an integer)
                    - key.data - pretty much anything you want. In this example, it is
                      a SimpleNameSpace containing:
                        - remote address
                        - data (outbound data buffer, inbound data buffer)
                        - a "read_idx", which marks the bytes read so far
                        - an "end_idx", which marks the total amount of bytes, taken
                          from the client's "Content-Length" header
            
            We set "setblocking" to False here, just as we did with the listening socket above.
            """
            events: List[Tuple[Any, Any]]= self._selector.select()
            for key, mask in events:
                if not key.data:
                    remote_sock, remote_address = self._sock.accept()
                    print(f"Accepted connection from {remote_address}")
                    remote_sock.setblocking(0)
                    data: types.SimpleNamespace = types.SimpleNamespace(
                        addr=remote_address,
                        inbound_data = b"",
                        outbound_data = b"",
                        read_idx = 0,
                        end_idx = 0
                    )
                    """
                    By default, a socket registered in "select" has data=None
                    If data is None, we know it is a new connection that is not yet registered
                    We set its data which, for us, is the remote address and two byte buffers
                    for inbound and outbound.
                    Finally, we register it with select.

                    NOTE: register takes a new connection and registers it with select. Its args
                    are:
                        - the actual remote socket
                        - a bitmask to check to see if the socket is waiting to read, write, or both
                        - the new data object, created above
                    """
                    self._selector.register(remote_sock, selectors.EVENT_READ | selectors.EVENT_WRITE, data)
                else:
                    # Get the actual socket and the data from the SelectorKEy object.
                    sock: socket.socket = key.fileobj
                    data: bytes = key.data

                    """
                    If the remote socket is waiting to be read:
                        - call recv on the remote socket to get data from it
                        - check to see if it is not None
                            - if not:
                                - first time through, get the content-length sent by client
                                - add the new data to the data object's outbound_data buffer
                                - increase the read_idx by adding the recv_data size to it
                                - if the "read_idx" is >= the "end_idx" (total amount of content sent by client),
                                  then we know we are finished, and we can add the b"HTTP/1.1 200 OK\r\n\r\n" response.
                        
                        - otherwise, it's already been read and we can close the connection
                    """
                    if mask & selectors.EVENT_READ:
                        recv_data: bytes = remote_sock.recv(MAXIMUM_TRANSMISSIBLE_UNIT)
                        if not data.end_idx:
                            data.end_idx = self._get_content_length_from_client(recv_data)

                        if recv_data:
                            data.outbound_data += recv_data
                            data.read_idx += len(recv_data)
                            if data.read_idx >= data.end_idx:
                                data.outbound_data += b"\r\nHTTP/1.1 200 OK\r\n\r\n"
                            
                        else:
                            print(f"Closing connection to {data.addr}")
                            self._selector.unregister(sock)
                            sock.close()

                    """
                    If the remote socket is waiting to be written to:
                        - check to see if there is outbound data to send
                        - if so, loop over the data and send it back
                        - finally, unregister the socket with the selector and then close the socket
                          once all of the data has been sent.
                    """
                    if mask & selectors.EVENT_WRITE:
                        if data.outbound_data:
                            print(f"Echoing {data.outbound_data} to {data.addr}")
                            sent: int = sock.send(data.outbound_data)
                            data.outbound_data = data.outbound_data[sent:]

                        if data.read_idx >= data.end_idx:
                            self._selector.unregister(sock)
                            sock.close()


if __name__ == "__main__":
    tcp_server: TCPServer = TCPServer()
    tcp_server.accept_connections_and_echo()
