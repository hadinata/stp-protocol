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

# log constants
SEND = 0
RCV = 1
DROP = 2

# input arguments
receiver_host_ip = sys.argv[1]
receiver_port = int(sys.argv[2])
filename = sys.argv[3];
mws = int(sys.argv[4]);
mss = int(sys.argv[5]);
timeout = int(sys.argv[6]);
pdrop = float(sys.argv[7]);
seed = int(sys.argv[8]);

# receiver address:
receiverAddress = (receiver_host_ip, receiver_port)

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

# create empty log file:
f = open("Sender_log.txt", "w")
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
    f = open("Sender_log.txt", "a")
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
createLogEntry(message, SEND)

# SYNACK
# handle receiving SYNACK:
while 1:
    recv_message, fromAddress = senderSocket.recvfrom(2048)
    createLogEntry(recv_message, RCV)
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
        createLogEntry(modifiedMessage, SEND)
        break

# Now ready to send data:

f = open(filename)
filestring = f.read()
segments = [filestring[i:i+mss] for i in range(0, len(filestring), mss)]
f.close()

# PLD:
def generateRandom():
    return random.random()

def sendWithPLD(message):
    rand_value = random.random()
    if (rand_value > pdrop):
        senderSocket.sendto(message, receiverAddress)
        createLogEntry(message, SEND)


# size of window (in terms of the number of segments it can hold)
window_n = mws/mss

# window parameters
start = 0
end = start+window_n

# sent index list
sent = [False] * len(segments)

# segmentIndex
def segIndexToSeqNum(segIndex):
    return isn+1+(segIndex*mss)

# list of segments sent but not yet acked
not_yet_acked = []

not_yet_acked_sqn = []
for i in range (0, len(segments)):
    not_yet_acked_sqn.append(segIndexToSeqNum(i))
print not_yet_acked_sqn

# shift window:
def moveWindowAlong():
    global start
    global end
    shifted_by = 0
    # while (int(getHeaderElement(segments[start],SEQ_NUM)) + int(getHeaderElement(segments[start],DATA_SIZE)) not in not_yet_acked):
    # while (segments[start] and segments[start] not in not_yet_acked):
    # for message in not_yet_acked:
    #print segIndexToSeqNum(start)
    while (len(not_yet_acked_sqn) > 0 and segIndexToSeqNum(start) not in not_yet_acked_sqn):
        #print "windowingg"
        start += 1
        shifted_by += 1
    if (len(not_yet_acked_sqn) <= 0):
        start = len(segments)
    if (end + shifted_by > len(segments)):
        end = len(segments)
    else:
        end += shifted_by



while 1:

    print "START: " + str(start) + "   END: " + str(end)

    if (start >= end):
        break

    # send segments in window
    for i in range (start, end):
        if (sent[i] == False):
            print "Here!"
            header = createCurrentHeader()
            header = modifyHeader(header, DATA_SIZE, len(segments[i]))
            message = header + segments[i]
            print message
            sendWithPLD(message)

            not_yet_acked.append(message)
            not_yet_acked.sort()

            #not_yet_acked_sqn.append(seqno_sender)
            #not_yet_acked_sqn.sort()

            next_seqno = int(getHeaderElement(header,SEQ_NUM)) + int(getHeaderElement(header,DATA_SIZE))
            if (next_seqno > seqno_sender):
                seqno_sender = next_seqno

    try:
        senderSocket.settimeout(timeout/1000)
        while 1:
            # packet_received = senderSocket.recvfrom(2048)
            # if not packet_received:
            #     continue
            returned_message, fromAddress = senderSocket.recvfrom(2048)
            createLogEntry(returned_message, RCV)
            received_ack = int(getHeaderElement(returned_message, ACK_NUM))
            oldest_unacked_sqn = int(getHeaderElement(not_yet_acked[0],SEQ_NUM))
            print "received_ack: " + str(received_ack)
            print "oldest_unacked_sqn: " + str(oldest_unacked_sqn)
            print not_yet_acked_sqn
            if (received_ack > oldest_unacked_sqn):
                print "here!"
                for segment in not_yet_acked:
                    segment_sqn = int(getHeaderElement(segment, SEQ_NUM))
                    if (segment_sqn < received_ack):
                        not_yet_acked_sqn.remove(segment_sqn)
                        not_yet_acked.remove(segment)
                if (len(not_yet_acked) == 0):
                    print "break!"
                    break
            print not_yet_acked_sqn
    except socket.timeout:
        sendWithPLD(not_yet_acked[0])
        senderSocket.sendto(not_yet_acked[0],(receiver_host_ip, receiver_port))

    print "moving window!"
    moveWindowAlong()

    print start
    #print segIndexToSeqNum(start)
