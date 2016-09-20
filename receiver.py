#!/usr/bin/python
#run with: python receiver.py 2068 abc.txt

import sys
from socket import *
import random
import Header
import time

receiver_port = int(sys.argv[1])
output_file =  sys.argv[2]

class Reciever:
	def __init__(self,port):
		self.recv_port = port
		self.reciever = socket(AF_INET, SOCK_DGRAM)
		self.reciever.bind(('', receiver_port))

		# flag to indicate if the flowing is recieved
		self.SYN = 0;
		self.ACK = 0;
		self.FIN1 = 0;
		self.FINACK2 = 0;

		self.expected_seqNum = 0
		self.curr_seqNum_recieved = 0;
		self.file =[]*1

		# write log file
		self.log_file = open("Receiver_log.txt", 'w')
		self.log_file.truncate()
		self.init_time = time.time()
		self.segment_rcv = 0
		self.dup_ack = 0

	def write_file(self):

		recv_file = open(output_file, 'w')
		recv_file.truncate()
		recv_file.write(''.join(self.file))
		recv_file.close()

	def write_log(self, state,packet,seq_num, length,ack_num):

		string = str(state)+" "
		string +=str(format((time.time() - self.init_time)*1000, '2.2f' )) +" "
		string +=str(packet)+ " "
		string +=str(seq_num)+" "
		string +=str(length)+" "
		string +=str(ack_num)+"\n"
		self.log_file.write(string)

	def print_info(self, data_rcv, segment_rcv, dup_ack ):
		info = "Amount of Data Received " + str(data_rcv) + "\n"
		info += "Number of Data Segments Received " + str(segment_rcv) + "\n"
		info += "Number of duplicate segments received " + str(dup_ack)+ "\n"

		self.log_file.write(info)

	def next_ack_to_send(self, index):

		for i in range(index, len(self.file)):
			if self.file[i]=='':
				return i
			if self.file[i] !='' and i == (len(self.file)-1) :
				return len(self.file)
		return index


	def recv_data(self):

		while (self.FINACK2 ==0):
			flag = True

			if(self.SYN == 0):
				while (flag):
					try:
						data, address = self.reciever.recvfrom(2048)
						header_recieved = Header.extract_header_handshake(data)

						if(header_recieved == "SYN"):
							self.SYN = 1;
							seq_num = Header.extract_header_seqNum(data)
							self.write_log("rcv","S", "0", "0","0")

							header = Header.create_header(0,seq_num,1,1,0)
							self.reciever.sendto(header, address)
							self.write_log("snd","SA", "0" ,"0" ,"0")

						elif (header_recieved == "ACK"):
							self.ACK = 1
							self.write_log("rcv","A", "0", "0","0")
							length = Header.extract_file_length(data)
							self.file = ['']*length
							flag = False

					except timeout:
						print "nothing recieved"

			elif(self.ACK == 1):
				while (self.FIN1 == 0 ):

					try:
						data, address = self.reciever.recvfrom(2048)
						header_recieved = Header.extract_header_handshake(data)
						ack_num = Header.extract_header_ackNum(data)
						seq_num = Header.extract_header_seqNum(data)
						data_segment = Header.extract_data(data)

						self.write_log("rcv","D", seq_num, len(data_segment),ack_num)
						print seq_num
						if(header_recieved == "FIN1"):
							self.write_log("rcv","F", seq_num, len(data_segment),ack_num)
							self.FIN1 = 1
							header = Header.create_header(0,self.expected_seqNum, 1, 0,1)
							self.reciever.sendto(header, address)

							header = Header.create_header(0,self.expected_seqNum, 1, 0,2)
							self.reciever.sendto(header, address)
							self.write_log("snd","FA", "0" ,"0" ,self.expected_seqNum)

							while self.FINACK2 == 0 :

								try:
									data, address = self.reciever.recvfrom(2048)
									header_recieved = Header.extract_header_handshake(data)
									self.FINACK2 = 1
									self.write_log("rcv","A", seq_num, len(data_segment),ack_num)
								except timeout:
									print "nothing recieved"

						else:

							seqNum_recieved = Header.extract_header_seqNum(data)
							data_segment = Header.extract_data(data)
							data_length = len(data_segment)

							# write to buffer
							if seqNum_recieved < len(self.file):
								char = seqNum_recieved

								if(self.file[char] == ''):
									self.segment_rcv +=1
									index = 0
									for char in range(seqNum_recieved,data_length+seqNum_recieved):
										self.file[char] = data_segment[index]
										index +=1
								else:
									print self.file[char]
									# print "recieve duplicated packets seq_num = ", seqNum_recieved
									self.dup_ack +=1
									# print self.dup_ack


							self.expected_seqNum = self.next_ack_to_send(self.expected_seqNum)
							header = Header.create_header(0 ,self.expected_seqNum, 0, 0,0)
							self.reciever.sendto(header, address)
							self.write_log("snd","A", "0" ,"0",self.expected_seqNum)

					except timeout:
						print "nothing recieved"

		if(self.FINACK2 == 1):
			self.write_file()
			self.print_info(self.expected_seqNum, self.segment_rcv, self.dup_ack)
			self.reciever.close()



reciever = Reciever(receiver_port)
print "	Init Server done"
reciever.recv_data()
print "	Server close connection"
