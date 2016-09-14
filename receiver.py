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
seqno_rec = 66400;

# current sender sequence number:
curr_sender_sqn = 0

# header indices constants:
PORT = 0
SEQ_NUM = PORT + PORT_BYTES
ACK_NUM = SEQ_NUM + SEQ_NUM_BYTES
SYN_FLAG = ACK_NUM + ACK_NUM_BYTES
ACK_FLAG = SYN_FLAG + 1
FIN_FLAG = ACK_FLAG + 1
DATA_SIZE = FIN_FLAG + 1
START_DATA = DATA_SIZE + DATA_SIZE_BYTES

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

# create default header with ACK based on current state
def createAckHeader(ack_num, port):
    port = str(port).zfill(PORT_BYTES)
    seq_num = str(seqno_rec).zfill(SEQ_NUM_BYTES)
    ack_num = str(ack_num).zfill(ACK_NUM_BYTES)
    syn_flag = str(0)
    ack_flag = str(1)
    fin_flag = str(0)
    data_size = str(0).zfill(DATA_SIZE_BYTES)

    header = port + seq_num + ack_num + syn_flag + ack_flag + fin_flag + data_size
    return header


# handle receiving SYN
while 1:
    message, fromAddress = receiverSocket.recvfrom(2048)
    fromIP, fromPort = fromAddress
    fromSQN = int(getHeaderElement(message,SEQ_NUM))
    curr_sender_sqn = fromSQN
    if (int(message[SYN_FLAG]) == 1 and int(message[ACK_FLAG]) == 0):
        print "SYN"
        print "with SEQ number: " + getHeaderElement(message, SEQ_NUM)
        modifiedMessage = message
        modifiedMessage = modifyHeader(modifiedMessage, ACK_FLAG, 1)    # set ack flag
        modifiedMessage = modifyHeader(modifiedMessage, SEQ_NUM, seqno_rec)
        modifiedMessage = modifyHeader(modifiedMessage, ACK_NUM, fromSQN+1)
        modifiedMessage = modifyHeader(modifiedMessage, PORT, fromPort) # set new port
        receiverSocket.sendto(modifiedMessage, fromAddress)
        break

# handle ACK:
message, fromAddress = receiverSocket.recvfrom(2048)
curr_sender_sqn = int(getHeaderElement(message,SEQ_NUM)) - 1

# handle receiving segment packets
while 1:
    message, fromAddress = receiverSocket.recvfrom(2048)
    fromIP, fromPort = fromAddress
    sender_seq_num = int(getHeaderElement(message,SEQ_NUM))
    data_size = int(getHeaderElement(message, DATA_SIZE))
    print "SENDER SEQ NUM: " + str(sender_seq_num)
    print "CURR_SENDER_SEQ: " + str(curr_sender_sqn)
    print "DATA SIZE: " + str(data_size)
    # duplicate handling:
    if (sender_seq_num == curr_sender_sqn):
        print "Duplicate detected - seq num: " + str(sender_seq_num)
    else:
        print message[START_DATA:]
        curr_sender_sqn = int(getHeaderElement(message,SEQ_NUM))
        print "CURR_SENDER_SEQ IS NOW: " + str(curr_sender_sqn)
    modifiedMessage = createAckHeader(sender_seq_num+data_size, fromPort)
    print "SENDING ACK NUM: " + str(sender_seq_num+data_size)
    print "SENDING (ACTUAL) ACK NUM: " + getHeaderElement(modifiedMessage,ACK_NUM)
    receiverSocket.sendto(modifiedMessage, fromAddress)
    print '\n'
