# receiver.py
# COMP3331 2016 S2 Assignment 1
# By Clinton Hadinata, September 2016

# usage:
# python receiver.py 12000 file.txt

import socket
import sys
import time

# constants
PORT_BYTES = 5
SEQ_NUM_BYTES = 5
ACK_NUM_BYTES = 5
DATA_SIZE_BYTES = 4

# log constants
SEND = 0
RCV = 1
DROP = 2

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

# create empty log file:
f = open("Receiver_log.txt", "w")
f.write("")
f.close()

# get packet type:
def getPacketType(packet):
    packetType = ""
    if (int(getHeaderElement(packet, DATA_SIZE)) > 0):
        packetType += "D"
    if (int(getHeaderElement(packet, SYN_FLAG)) == 1):
        packetType += "S"
    if (int(getHeaderElement(packet, FIN_FLAG)) == 1):
        packetType += "F"
    if (int(getHeaderElement(packet, ACK_FLAG)) == 1):
        packetType += "A"
    return packetType

# get current time
def getCurrentTime():
    return time.asctime(time.localtime(time.time()))

# create log entry:
def createLogEntry(packet, pkt_type):
    f = open("Receiver_log.txt", "a")
    type_string = ""
    if (pkt_type == SEND):
        type_string = "snd"
    elif (pkt_type == RCV):
        type_string = "rcv"
    elif (pkt_type == DROP):
        type_string = "drop"
    f.write(type_string.ljust(6) + getCurrentTime().ljust(26) + str(getPacketType(packet)).ljust(4)
            + str(getHeaderElement(packet, SEQ_NUM)).ljust(7) + str(getHeaderElement(packet, DATA_SIZE)).ljust(6)
            + str(getHeaderElement(packet, ACK_NUM)).ljust(7) + "\n")
    f.close()

# create empty file where received contents would go:
f = open(filename, "w")
f.write("")
f.close()

# write data to file:
def writeToFile(string):
    f = open(filename, "a")
    f.write(str(string))
    f.close()

# -------------------------------------------------------------- #

# handle receiving SYN
while 1:
    message, fromAddress = receiverSocket.recvfrom(2048)
    createLogEntry(message, RCV)
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
        createLogEntry(modifiedMessage, SEND)
        break

# handle ACK:
message, fromAddress = receiverSocket.recvfrom(2048)
createLogEntry(message, RCV)
curr_sender_sqn = int(getHeaderElement(message,SEQ_NUM)) - 1


# for buffer handling:

# next expected sender sequence number:
# initialised to seqnum of last ACK segment in the connection establishment handshake
nx_ssqn = int(getHeaderElement(message,SEQ_NUM))

# inline_ack is the
inline_ack = nx_ssqn

# buffer list: where non-next segments will be stored
buffer_list = []

# list of sequence numbers which have been received:
received = []


# handle receiving segment packets
while 1:
    message, fromAddress = receiverSocket.recvfrom(2048)
    createLogEntry(message, RCV)
    fromIP, fromPort = fromAddress
    sender_seq_num = int(getHeaderElement(message,SEQ_NUM))
    data_size = int(getHeaderElement(message, DATA_SIZE))

    # duplicate handling:
    if (sender_seq_num in received):

        print "Duplicate detected - seq num: " + str(sender_seq_num)
        reply = createAckHeader(nx_ssqn, fromPort)  # reply with ack = nx_ssqn
        receiverSocket.sendto(reply, fromAddress)

    # if sender_seq_num is the next expected one in order (nx_ssqn)
    elif (sender_seq_num == nx_ssqn):
        print ("TWO!")

        if (inline_ack <= sender_seq_num):              # initial case
            inline_ack = sender_seq_num + data_size

        reply = createAckHeader(inline_ack, fromPort)   # reply with ack = inline_ack
        print "reply: " + reply
        receiverSocket.sendto(reply, fromAddress)       # send reply
        createLogEntry(reply, SEND)
        print "HERE"

        writeToFile(message[START_DATA:])               # write received data to file

        # i = 0                                         # write buffered data to file
        while (len(buffer_list) > 0 and
                int(getHeaderElement(buffer_list[0],SEQ_NUM)) < inline_ack):
            buffer_element = buffer_list[0]
            writeToFile(buffer_element[START_DATA:])
            buffer_list.remove(buffer_element)

        nx_ssqn = inline_ack        # now set nx_ssqn to inline_ack

        if (len(buffer_list) > 0):
            inline_ack = int(getHeaderElement(buffer_list[0],SEQ_NUM)) + int(getHeaderElement(buffer_list[0],DATA_SIZE))
            k = 1
            while (k < len(buffer_list) and
                    int(getHeaderElement(buffer_list[k],SEQ_NUM)) == inline_ack):
                inline_ack = int(getHeaderElement(buffer_list[k],SEQ_NUM)) + int(getHeaderElement(buffer_list[k],DATA_SIZE))
                k = k+1

    # if sender_seq_num is bigger than the next expected one
    elif (sender_seq_num > nx_ssqn):

        print ("THREE!")

        buffer_list.append(message)                 # append message received from sender to the buffer list
        # sort....
        reply = createAckHeader(nx_ssqn, fromPort)  # reply with ack = next expected sqn num
        receiverSocket.sendto(reply, fromAddress)   # send reply
        createLogEntry(reply, SEND)
