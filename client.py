"""client.py ."""

import socket

import hamming_module as hm

# from time import sleep

UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock.connect(('localhost', UDP_PORT))

while True:
    text = input()
    if text == 'stop':
        sock.send(b'stop')
        break
    else:
        msg = [int(x) for x in text]  # type: ignore

        blocks = []
        for i in range(0, len(msg), 4):
            block = msg[i : i + 4]  # noqa: E203
            encoded_block = hm.encode(block)
            blocks.append(encoded_block)

        interleaved_blocks = [[] for _ in range(7)]

        for block in blocks:
            for i in range(7):
                interleaved_blocks[i].append(block[i])

        for sended in interleaved_blocks:
            data = ''.join(str(elem) for elem in sended)
            sock.sendto(data.encode('utf-8'), ('localhost', UDP_PORT))
