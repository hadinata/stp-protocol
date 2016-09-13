# sender.py
# COMP3331 2016 S2 Assignment 1
# By Clinton Hadinata, September 2016

# usage:
# python sender.py localhost 12000 file.txt 10 10 100 0.5 17

import sys
import socket
import time

# constants
PORT_BYTES = 5
SEQ_NUM_BYTES = 5
ACK_NUM_BYTES = 5
DATA_SIZE_BYTES = 4

# input arguments
receiver_host_ip = sys.argv[1]
receiver_port = int(sys.argv[2])
filename = sys.argv[3];
mws = int(sys.argv[4]);
mss = int(sys.argv[5]);
timeout = int(sys.argv[6]);
pdrop = float(sys.argv[7]);
seed = int(sys.argv[8]);

# HEADER STRUCTURE:
# 5B - receiver port
# 5B - seq num
# 5B - ack num
# 3B - flags
# 4B - size of data

# header indices constants:
PORT = 0
SEQ_NUM = PORT + PORT_BYTES
ACK_NUM = SEQ_NUM + SEQ_NUM_BYTES
SYN_FLAG = ACK_NUM + ACK_NUM_BYTES
ACK_FLAG = SYN_FLAG + 1
FIN_FLAG = ACK_FLAG + 1
DATA_SIZE = FIN_FLAG + DATA_SIZE_BYTES

def modifyHeader(header, component, value):

    modifiedHeader = header

    if (component == PORT):
        modifiedHeader = str(value).zfill(PORT_BYTES) + header[SEQ_NUM:]
    elif (component == SEQ_NUM):
        modifiedHeader = header[:SEQ_NUM] + str(value).zfill(SEQ_NUM_BYTES) + header[ACK_NUM:]
    elif (component == ACK_NUM):
        modifiedHeader = header[:ACK_NUM] + str(value).zfill(ACK_NUM_BYTES) + header[SYN_FLAG:]
    elif (component == SYN_FLAG):
        modifiedHeader = header[:SYN_FLAG] + str(value).zfill(1) + header[ACK_FLAG:]
    elif (component == ACK_FLAG):
        modifiedHeader = header[:ACK_FLAG] + str(value).zfill(1) + header[FIN_FLAG:]
    elif (component == FIN_FLAG):
        modifiedHeader = header[:FIN_FLAG] + str(value).zfill(1) + header[DATA_SIZE:]
    elif (component == DATA_SIZE):
        modifiedHeader = header[:DATA_SIZE] + str(value).zfill(DATA_SIZE_BYTES)

    return modifiedHeader

# isn
isn = 0;
seqno_sender = isn;

# state constants:


# initialise state:

# Declare client socket
senderSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# intiial header elements:
port = str(receiver_port).zfill(5)
seq_num = str(seqno_sender).zfill(SEQ_NUM_BYTES);
ack_num = str(0).zfill(ACK_NUM_BYTES);
syn_flag = str(0);
ack_flag = str(0);
fin_flag = str(0);
data_size = str(0).zfill(DATA_SIZE_BYTES);

# create header
header = port + seq_num + ack_num + syn_flag + ack_flag + fin_flag + data_size

# Establish connection:

# SYN
# set SYN flag to 1:
message = header[:SYN_FLAG] + str(1) + header[ACK_FLAG:]

# send SYN:
senderSocket.sendto(message,(receiver_host_ip, receiver_port))

# SYNACK
# handle receiving SYNACK:
while 1:
    recv_message, fromAddress = senderSocket.recvfrom(2048)
    fromIP, fromPort = fromAddress
    print "Received from rec: " + recv_message
    if (int(recv_message[SYN_FLAG]) == 1 and int(recv_message[ACK_FLAG]) == 1):
        print "SYNACK"
        modifiedMessage = modifyHeader(recv_message, SYN_FLAG, 0)   # set syn flag to 0
        modifiedMessage = modifyHeader(message, PORT, fromPort)     # set new port
        senderSocket.sendto(modifiedMessage, fromAddress)
        break
