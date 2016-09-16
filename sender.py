# sender.py
# COMP3331 2016 S2 Assignment 1
# By Clinton Hadinata, September 2016

# usage:
# python sender.py localhost 12000 file.txt 10 10 100 0.5 17

import datetime
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
timeout = float(sys.argv[6]);
pdrop = float(sys.argv[7]);
seed = int(sys.argv[8]);

# receiver address:
receiverAddress = (receiver_host_ip, receiver_port)

# initialise randomiser with seed
random.seed(seed)

# convert timeout time to seconds
timeout_in_sec = float(timeout)/float(1000)
print "timeout_in_sec = " + str(timeout_in_sec)

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
isn = 03200

# initial sequence and ack numbers:
seqno_sender = isn
current_ack = 0

# global variables to keep track of statistics
total_data_sent = 0
num_data_segments = 0
num_packets_dropped = 0
num_retransmitted_segments = 0
num_duplicate_acknowledgements = 0

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
    string = datetime.datetime.now().strftime('%H:%M:%S %f')[:-3]
    string += "."
    string += datetime.datetime.now().strftime('%f')[3:]
    return string
    # return time.asctime(time.localtime(time.time()))

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

# get default timeout value
default_socket_timeout = senderSocket.gettimeout()
print "DEFAULT SOCKET TIMEOUT: " + str(default_socket_timeout)

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
    fromSQN = int(recv_message[SEQ_NUM:ACK_NUM])
    current_ack = fromSQN+1
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

# open file and break it up into segments
f = open(filename)
filestring = f.read()
segments = [filestring[i:i+mss] for i in range(0, len(filestring), mss)]
f.close()

# size of window (in terms of the number of segments it can hold)
window_n = mws/mss

# window parameters
start = 0
end = start+window_n

# hash of whether or not a seq_no has been sent
sent = {}

# segmentIndex
def segIndexToSeqNum(segIndex):
    return isn+1+(segIndex*mss)

# reverse
def seqNumToSegIndex(seqNum):
    return (seqNum-1-isn/mss)

# list of segments sent but not yet acked
not_yet_acked = []

not_yet_acked_sqn = []
for i in range (0, len(segments)):
    not_yet_acked_sqn.append(segIndexToSeqNum(i))
    sent[segIndexToSeqNum(i)] = False
print not_yet_acked_sqn

# the last expected ack number (if the last segment's data size is mss)
last_ack_number = segIndexToSeqNum(len(segments)-1)+mss

# hash of number of times an ack has been received
numTimesReceived = {}

# PLD:
def generateRandom():
    return random.random()

def sendWithPLD(message):
    global num_packets_dropped
    rand_value = random.random()
    print "Random Value: " + str(rand_value)
    if (rand_value > pdrop):
        senderSocket.sendto(message, receiverAddress)
        print "SENDING:"
        print message
        createLogEntry(message, SEND)
    else:
        createLogEntry(message, DROP)
        num_packets_dropped += 1
    sent[int(getHeaderElement(message,SEQ_NUM))] = True


# shift window:
def moveWindowAlong():
    global start
    global end
    shifted_by = 0
    # while (int(getHeaderElement(segments[start],SEQ_NUM)) + int(getHeaderElement(segments[start],DATA_SIZE)) not in not_yet_acked):
    # while (segments[start] and segments[start] not in not_yet_acked):
    # for message in not_yet_acked:
    #print segIndexToSeqNum(start)
    print "start is " + str(start) + " with not_yet_acked_sqn being: "
    print not_yet_acked_sqn
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


# main loop:

while 1:

    print "START: " + str(start) + "   END: " + str(end)

    if (start >= end):
        break

    # start timer just before sending first segment in window
    senderSocket.settimeout(timeout_in_sec)

    # send segments in window
    for i in range (start, end):
        if (sent[segIndexToSeqNum(i)] == False):
            print "Here! At i = " + str(i)
            header = createCurrentHeader()
            header = modifyHeader(header, DATA_SIZE, len(segments[i]))
            message = header + segments[i]
            print message
            sendWithPLD(message)
            total_data_sent += len(segments[i])
            num_data_segments += 1

            not_yet_acked.append(message)
            print "APPENDED with seq number: " + str(getHeaderElement(message,SEQ_NUM))
            print message
            not_yet_acked.sort()

            #not_yet_acked_sqn.append(seqno_sender)
            #not_yet_acked_sqn.sort()

            next_seqno = int(getHeaderElement(header,SEQ_NUM)) + int(getHeaderElement(header,DATA_SIZE))
            if (next_seqno > seqno_sender):
                seqno_sender = next_seqno

    try:
        while 1:
            # packet_received = senderSocket.recvfrom(2048)
            # if not packet_received:
            #     continue
            returned_message, fromAddress = senderSocket.recvfrom(2048)
            createLogEntry(returned_message, RCV)
            if (len(not_yet_acked) > 0):
                senderSocket.settimeout(timeout_in_sec) # restart timer
            received_ack = int(getHeaderElement(returned_message, ACK_NUM))
            if (received_ack not in numTimesReceived or numTimesReceived[received_ack] == 0):
                numTimesReceived[received_ack] = 1
            else:
                if (numTimesReceived[received_ack] == 4):
                    print "Fast retransmit!"
                    sendWithPLD(not_yet_acked[0])
                    num_retransmitted_segments += 1
                numTimesReceived[received_ack] += 1
                num_duplicate_acknowledgements += 1
            oldest_unacked_sqn = int(getHeaderElement(not_yet_acked[0],SEQ_NUM))
            print "received_ack: " + str(received_ack)
            print "oldest_unacked_sqn: " + str(oldest_unacked_sqn)
            print not_yet_acked_sqn
            print len(not_yet_acked)
            if (received_ack > oldest_unacked_sqn):
                print "here!"
                print not_yet_acked
                for segment in not_yet_acked:
                    segment_sqn = int(getHeaderElement(segment, SEQ_NUM))
                    print "at segment: " + str(segment_sqn)
                    print "last_ack_number: " + str(last_ack_number)
                    if (received_ack <= last_ack_number and segment_sqn < received_ack):
                        print "len is: " + str(len(not_yet_acked))
                        print not_yet_acked_sqn
                        print "deleting " + str(segment_sqn)
                        not_yet_acked_sqn.remove(segment_sqn)
                        not_yet_acked.remove(segment)
                        print "now is: " + str(len(not_yet_acked))
                        print not_yet_acked_sqn
                print (len(not_yet_acked))
                if (len(not_yet_acked) == 0):
                    print "break!"
                    break
            print not_yet_acked_sqn
    except socket.timeout:
        print "TIMEOUT! Resending: "
        print not_yet_acked[0]
        sendWithPLD(not_yet_acked[0])
        num_retransmitted_segments += 1

    print "moving window!"
    moveWindowAlong()

    print start
    #print segIndexToSeqNum(start)

    print "\n"


# fin:
fin_packet = createCurrentHeader()
fin_packet = modifyHeader(fin_packet, FIN_FLAG, 1)
senderSocket.sendto(fin_packet, receiverAddress)
createLogEntry(fin_packet, SEND)

# set timeout back to default (none)
senderSocket.settimeout(default_socket_timeout)

# handle receiving finack:
while 1:
    recv_message, fromAddress = senderSocket.recvfrom(2048)
    createLogEntry(recv_message, RCV)
    fromIP, fromPort = fromAddress
    fromACK = int(recv_message[ACK_NUM:SYN_FLAG])
    fromSQN = int(recv_message[SEQ_NUM:ACK_NUM])
    current_ack = fromSQN+1
    print "Received from rec: " + recv_message + " with ack_num: " + str(fromACK)
    if (int(getHeaderElement(recv_message,FIN_FLAG)) == 1 and int(getHeaderElement(recv_message,ACK_FLAG)) == 1):
        print "received FINACK"
        seqno_sender = fromACK
        # send ACK:
        reply = recv_message
        reply = modifyHeader(reply, FIN_FLAG, 0)    # set fin flag to 0
        reply = modifyHeader(reply, SEQ_NUM, seqno_sender)
        reply = modifyHeader(reply, ACK_NUM, fromSQN+1)
        reply = modifyHeader(reply, PORT, fromPort) # set new port
        senderSocket.sendto(reply, fromAddress)
        createLogEntry(reply, SEND)
        print "Final ack sent."
        break

print "\nConnection ended."

print "\n\n"
print "Amount of (original) data sent: " + str(total_data_sent) + " bytes."
print "Number of (original) data segments sent: " + str(num_data_segments)
print "Number of all packets dropped (by PLD): "  + str(num_packets_dropped)
print "Number of retransmitted segments: " + str(num_retransmitted_segments)
print "Number of duplicate acks received: " + str(num_duplicate_acknowledgements)

f = open("Sender_log.txt", "a")
f.write("\n")
f.write("Amount of (original) data sent: " + str(total_data_sent) + " bytes." + "\n")
f.write("Number of (original) data segments sent: " + str(num_data_segments) + "\n")
f.write("Number of all packets dropped (by PLD): "  + str(num_packets_dropped) + "\n")
f.write("Number of retransmitted segments: " + str(num_retransmitted_segments) + "\n")
f.write("Number of duplicate acks received: " + str(num_duplicate_acknowledgements) + "\n")
f.close()
