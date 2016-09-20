#!/usr/bin/python
#run with: python sender.py 127.0.0.1 2068 test2.txt 800 100 100 0.1 50

import sys
import time
import PLD
import Header
import socket
from socket import AF_INET, SOCK_DGRAM
import threading
import time
import math

receiver_ip = sys.argv[1]
receiver_port = int(sys.argv[2])
text_file = sys.argv[3]
MWS = int(sys.argv[4])
MSS = int(sys.argv[5])
timeout = float(sys.argv[6])/(1000*1.0)
pdrop = float(sys.argv[7])
seed = int(sys.argv[8])


class Sender:

	def __init__(self, index, ip, port):

		self.index = 5
		self.recv_port = port
		self.recv_ip = ip
		self.server_add = (receiver_ip,receiver_port)
		self.sender = PLD.PLD_socket(AF_INET, SOCK_DGRAM, pdrop, seed)

		# flag to indicate if the flowing is recieved
		self.SYNACK = 0
		self.FINACK1 = 0
		self.FIN2 = 0

		self.max_seqSent = 0
		self.curr_seqNum = 0 		# next one to send
		self.sendBase = 0 			# is the last acked_number
		self.count_ack = 0
		self.next_seq = 0
		self.ack_recieved = 0
		self.final_package = 0
		self.timer = threading.Timer(timeout, self.retransmitt, [0])
		self.timer.start()
		self.retransmitting = False #True indicate some packet is retransmitting
									#False then continue sending packets in the

		# summary info
		self.segment_resent = 0
		self.dup_ack = 0


	def abstract_data(self, seq_num):
		if(seq_num + MSS > len(self.content)):
			string_data = self.content[seq_num:]
			self.final_package = 1
			# self.next_seq = len(self.content)
		else:
			string_data = self.content[seq_num:seq_num+MSS]
			self.next_seq = seq_num + MSS
		return string_data


	def data_package(self, string_data):
		header = Header.create_header(self.curr_seqNum,self.sendBase,0,0,0)
		data_sent = header + string_data

		if self.max_seqSent < self.curr_seqNum:
			self.max_seqSent = self.curr_seqNum

		self.sender.PLD_sendto(data_sent, self.server_add)
		self.curr_seqNum = self.next_seq

	def restart_timer(self, check_seq):
		self.timer.cancel()
		self.timer = threading.Timer(timeout, self.retransmitt, [check_seq])
		self.timer.start()


	def retransmitt(self, check_seq):
		self.timer.cancel()

		if check_seq == len(self.content) and self.curr_seqNum == len(self.content):
			return

		if check_seq == self.sendBase:
			self.retransmitting = True
			self.segment_resent +=1
			self.curr_seqNum = self.sendBase
			print "retransmitt:", self.curr_seqNum
			#make data_segment
			string_data = self.abstract_data(self.curr_seqNum)

			self.data_package(string_data)


			self.timer = threading.Timer(timeout, self.retransmitt, [self.sendBase])
			self.timer.start()

			flag = self.recieve_ack_check()

			# if not recieved, retransmitt
			if flag == True :
				self.retransmitting = False
			else:
				self.retransmitt(self.sendBase)




	def recieve_ack_check(self):

		try:
			data, address = self.sender.PLD_recvfrom(2048)
			self.timer.cancel()
			self.ack_recieved = Header.extract_header_ackNum(data)

			#shift window right
			if(self.sendBase < self.ack_recieved):
				self.count_ack = 1
				self.sendBase = self.ack_recieved

				if self.max_seqSent >= self.sendBase:
					return False

			elif self.sendBase == self.ack_recieved:
				# print "self.curr_seqNum", self.curr_seqNum, "self.sendBase ", self.sendBase, "self.ack_recieved", self.ack_recieved
				self.count_ack +=1
				self.dup_ack += 1

			#current can move right, send from sendbase
			if self.curr_seqNum < self.sendBase:
				self.curr_seqNum = self.sendBase


			self.timer = threading.Timer(timeout, self.retransmitt,[self.sendBase])
			self.timer.start()
			return True

		except socket.timeout:
			return False


	def send_data(self):
		#read file
		self.sender.settimeout(0.01)
		file = open(text_file, "r")
		self.content = file.read()
		times = 0

		while self.sendBase < len(self.content):

			# time.sleep(0.01)
			# print "now send: ", self.sendBase

			if self.retransmitting :
				continue

			if self.final_package == 1 and self.sendBase + MSS >= len(self.content):
				continue

			if self.count_ack == 3 :
				self.retransmitt(self.sendBase)

			#continue sending in the window
			elif(self.curr_seqNum < self.sendBase + MWS):
				# print "self.curr_seqNum", self.curr_seqNum, "self.sendBase ", self.sendBase, "self.ack_recieved", self.ack_recieved

				#make data_segment
				string_data = self.abstract_data(self.curr_seqNum)

				#make header and send
				self.data_package(string_data)

				#try recieve ack
				self.recieve_ack_check()

		self.timer.cancel()




	def hand_shake(self):

		#buffer self.content
		file = open(text_file, "r")
		self.content = file.read()

		header = Header.create_header(self.curr_seqNum,self.sendBase, 0,1,0)
		self.sender.PLD_sendto(header, self.server_add)

		flag = True
		while flag :
			data,address = self.sender.PLD_recvfrom(2048)
			flag = False
			header_recieved = Header.extract_header_handshake(data)
			if header_recieved == "SYNACK":
				self.SYNACK =1

				ack_num = Header.extract_header_ackNum(data)

				header = Header.create_header(self.curr_seqNum,self.sendBase,1,0,0) + str(len(self.content))
				self.sender.PLD_sendto(header, self.server_add)
			else:
				flag = True



	def close_connection(self):
		self.timer.cancel()
		time.sleep(0.01)

		#send fin1
		header = Header.create_header(self.curr_seqNum, self.sendBase, 0,0,1)
		self.sender.PLD_sendto(header, self.server_add)
		self.timer.cancel()

		while self.FINACK1 == 0:

			try:
				#recieve finack1
				data,address = self.sender.PLD_recvfrom(2048)
				header_recieved = Header.extract_header_handshake(data)
				self.FINACK1 =1

			except socket.timeout:
				print "FINACK1 not recieved"

		while self.FIN2 == 0:

			try:
				#recieve finack2
				data,address = self.sender.PLD_recvfrom(2048)
				header_recieved = Header.extract_header_handshake(data)
				self.FIN2 =1

			except socket.timeout:
				print "FIN2 not recieved"

		#send finack2
		header = Header.create_header(self.curr_seqNum,self.sendBase, 2, 0 ,2)
		self.sender.PLD_sendto(header, self.server_add)
		self.sender.print_info(len(self.content),math.ceil(len(self.content)/(MSS*1.0)), self.segment_resent, self.dup_ack)
		self.sender.close()



client = Sender(5, receiver_ip, receiver_port)
client.hand_shake()
client.send_data()
client.close_connection()
sys.exit()
