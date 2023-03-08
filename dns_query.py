import socket
import struct

# Create a UDP Socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
hostname = "www.wikipedia.org"

"""
Below is the DNS Header format
	- struct.pack requires a format
		- "!" means network
		- "H" means "short integer"
		-"!HHHHHH" means that there are 6 parts to what we are packing into this struct. This is because there are 6 parts to the DNS header.
			- ID
			- Flags
			- Question Count
			- Answer Count
			- Name Server Resource Records
			- Additional Records
		
		- 42 is our request ID (could be any integer)
		- In the Flags section on page 25 of https://www.ietf.org/rfc/rfc1035.txt (row 2), we only care about the 8th bit in the first byte, making our query recursive
			- this means that, in hex, our flag is 0x0100
		
		- we have 1 question
		- we are sending 0 answers
		- we are sending 0 Name Server Resource Records
		- we are sending 0 Additional Records
		
		- all of this makes: struct.pack("!HHHHHH", 42, 0x0100, 1, 0, 0, 0)
"""
query = struct.pack("!HHHHHH", 42, 0x0100, 1, 0, 0, 0)

"""
Constructing the Question
You cannot just send "www.wikipedia.org". The DNS RFC says:
QNAME           a domain name represented as a sequence of labels, where
				each label consists of a length octet followed by that
				number of octets.  The domain name terminates with the
				zero length octet for the null label of the root.  Note
				that this field may be an odd number of octets; no
			padding is used.

In code, this maps to:
	qname = b"".join(len(p).to_bytes(1, "big") + p.encode("ascii") for p in hostname.split(".")) + b"\x00"
	query += qname
	
	We:
		- split the hostname string at periods
		- get the length of each part in bytes, using big endian encoding
		- add the actual string to it, i.e. "www", "wikipedia", and "org"
		- add a null byte at the end
		- www.wikipedia.org == b'\x03www\twikipedia\x03org\x00'
		
		- finally, add it to the query
"""
qname = b"".join(len(p).to_bytes(1, "big") + p.encode("ascii") for p in hostname.split(".")) + b"\x00"
query += qname

"""
Add the QTYPE and QCLASS to the Headers: - page 27 of https://www.ietf.org/rfc/rfc1035.txt
	- this is a lot like the first struct
		- adding two fields and using the network == "!HH"
		- set the QTYPE and QCLASS bits to 1
		- query += struct.pack("!HH", 1, 1)
"""
query += struct.pack("!HH", 1, 1)

# Send the data over UDP, recieve data from the DNS resolver, and print it
# NOTE: Use Wireshark to view this activity much more easily once the request is sent. The request returns
# as hex data.
sock.sendto(query, ("8.8.8.8", 53))
data, addr = sock.recvfrom(4096)
print(data)
