# sender.py
# COMP3331 2016 S2 Assignment 1
# By Clinton Hadinata, September 2016

# usage:
# python sender.py localhost 12000 file.txt 10 10 100 0.5 17

import random
import socket
import sys
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

# initialise randomiser with seed
random.seed(seed)

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
DATA_SIZE = FIN_FLAG + 1
START_DATA = DATA_SIZE + DATA_SIZE_BYTES

# isn:
isn = 33200

# initial sequence and ack numbers:
seqno_sender = isn
current_ack = 0

# state constants:


# initialise state:


# modify component of header by assigning it value
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


# returns header component (as a string)
def getHeaderElement(header, component):
    if (component == PORT):
        value = header[PORT:PORT+PORT_BYTES]
    elif (component == SEQ_NUM):
        value = header[SEQ_NUM:SEQ_NUM+SEQ_NUM_BYTES]
    elif (component == ACK_NUM):
        value = header[ACK_NUM:ACK_NUM+ACK_NUM_BYTES]
    elif (component == SYN_FLAG):
        value = header[SYN_FLAG:SYN_FLAG+1]
    elif (component == ACK_FLAG):
        value = header[ACK_FLAG:ACK_FLAG+1]
    elif (component == FIN_FLAG):
        value = header[FIN_FLAG:FIN_FLAG+1]
    elif (component == DATA_SIZE):
        value = header[DATA_SIZE:DATA_SIZE+DATA_SIZE_BYTES]
    return value

# create default header based on current state
def createCurrentHeader():
    port = str(receiver_port).zfill(PORT_BYTES)
    seq_num = str(seqno_sender).zfill(SEQ_NUM_BYTES)
    ack_num = str(current_ack).zfill(ACK_NUM_BYTES)
    syn_flag = str(0)
    ack_flag = str(0)
    fin_flag = str(0)
    data_size = str(0).zfill(DATA_SIZE_BYTES)

    header = port + seq_num + ack_num + syn_flag + ack_flag + fin_flag + data_size
    return header


# Declare client socket
senderSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# create initial header
header = createCurrentHeader()

# Establish connection:

# SYN
# set SYN flag to 1:
message = header
message = modifyHeader(message, SYN_FLAG, 1)

# send SYN:
senderSocket.sendto(message,(receiver_host_ip, receiver_port))

# SYNACK
# handle receiving SYNACK:
while 1:
    recv_message, fromAddress = senderSocket.recvfrom(2048)
    fromIP, fromPort = fromAddress
    fromACK = int(recv_message[ACK_NUM:SYN_FLAG])
    current_ack = fromACK
    fromSQN = int(message[SEQ_NUM:ACK_NUM])
    print "Received from rec: " + recv_message + " with ack_num: " + str(fromACK)
    if (int(getHeaderElement(recv_message,SYN_FLAG)) == 1 and int(getHeaderElement(recv_message,ACK_FLAG)) == 1):
        print "received SYNACK"
        seqno_sender = fromACK
        # send ACK:
        modifiedMessage = recv_message
        modifiedMessage = modifyHeader(modifiedMessage, SYN_FLAG, 0)    # set syn flag to 0
        modifiedMessage = modifyHeader(modifiedMessage, SEQ_NUM, seqno_sender)
        modifiedMessage = modifyHeader(modifiedMessage, ACK_NUM, fromSQN+1)
        modifiedMessage = modifyHeader(modifiedMessage, PORT, fromPort) # set new port
        senderSocket.sendto(modifiedMessage, fromAddress)
        break

# Now ready to send data:

f = open(filename)
filestring = f.read()
segments = [filestring[i:i+mss] for i in range(0, len(filestring), mss)]

# PLD:
def generateRandom():
    return random.random()

# send data using stop and wait:
for i in range(0, len(segments)):
    print "SENDING Segment " + str(i)
    header = createCurrentHeader()
    header = modifyHeader(header, DATA_SIZE, len(segments[i]))
    message = header + segments[i]
    while 1:
        try:
            rand_value = generateRandom()
            print rand_value
            if (rand_value > pdrop):
                print "got here!"
                senderSocket.sendto(message, fromAddress)
            senderSocket.settimeout(1)
            print "SENT: " + message + " with SEQNO: " + getHeaderElement(message, SEQ_NUM)
            returned_message, fromAddress = senderSocket.recvfrom(2048)
            received_ack = int(getHeaderElement(returned_message, ACK_NUM))
            print "RECEIVED ACK: " + str(received_ack)
            while (received_ack == current_ack):
                returned_message, fromAddress = senderSocket.recvfrom(2048)
                received_ack = int(getHeaderElement(returned_message, ACK_NUM))
                print "RECEIVED ACK: " + str(received_ack)
            current_ack = received_ack
            break
        except socket.timeout:
            print "Timed out. Resending segment.."
    seqno_sender = received_ack
    print "Segment " + str(i) + " acknowledged with ack num: " + str(received_ack)

    print "\n"
