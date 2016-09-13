# receiver.py
# COMP3331 2016 S2 Assignment 1
# By Clinton Hadinata, September 2016

# usage:
# python receiver.py 12000 file.txt

import socket
import sys

# constants
PORT_BYTES = 5
SEQ_NUM_BYTES = 5
ACK_NUM_BYTES = 5
DATA_SIZE_BYTES = 4

# arguments
receiver_port = int(sys.argv[1])
filename = sys.argv[2]

# Set up receiver socket
receiverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiverSocket.bind(('', receiver_port))

# current sequence number:
seqno_rec = 0;

# header indices constants:
PORT = 0
SEQ_NUM = PORT + PORT_BYTES
ACK_NUM = SEQ_NUM + SEQ_NUM_BYTES
SYN_FLAG = ACK_NUM + ACK_NUM_BYTES
ACK_FLAG = SYN_FLAG + 1
FIN_FLAG = ACK_FLAG + 1
DATA_FLAG = FIN_FLAG + DATA_SIZE_BYTES

# handle receiving SYN
while 1:
    message, senderAddress = receiverSocket.recvfrom(2048)
    senderIP, senderPort = senderAddress
    if (int(message[SYN_FLAG]) == 1 and int(message[ACK_FLAG]) == 0):
        print "SYN"
        modifiedMessage = message[:ACK_FLAG] + str(1) + message[FIN_FLAG:] # set ACK flag
        receiverSocket.sendto(modifiedMessage, senderAddress)
