#!/usr/bin/python

import sys
import time
import PLD
from socket import *
import Header
import random

class PLD_socket(socket):

	def __init__(self, family, type, inputpdrop, inputseed):

		socket.__init__(self, family, type)
		self.log_file = open("Sender_log.txt", 'w')
		self.init_time = time.time()
		self.log_file.truncate()
		self.log_file.write("<snd/rcv/drop>  <time>  <packet_type>  <seq_num>  <num_bytes> <ack_num>\n")
		self.pdrop = inputpdrop
		random.seed(inputseed)
		self.num_drop = 0

	def write_log(self, state,packet,seq_num, length,ack_num):

		string = str(state)+" "
		string +=str(format((time.time() - self.init_time)*1000, '2.2f' )) +" "
		string +=str(packet)+ " "
		string +=str(seq_num)+" "
		string +=str(length)+" "
		string +=str(ack_num)+"\n"
		self.log_file.write(string)

	def PLD_recvfrom(self, size):

		data, address =  self.recvfrom(size)
		ack_num = Header.extract_header_ackNum(data)
		seq_num = Header.extract_header_seqNum(data)
		data_type = Header.extract_packet_type(data)

		if data_type != "":
			if data_type == "D":
				data_type = "A"
			self.write_log("rcv",data_type, seq_num, "0",ack_num)

		return data, address

	def PLD_sendto(self, data, address):

		randNum = random.random()
		header = Header.extract_header_delay(data)
		ack_num = Header.extract_header_ackNum(data)
		seq_num = Header.extract_header_seqNum(data)
		data_segment = Header.extract_data(data)
		data_type = Header.extract_packet_type(data)

		if header == "HANDSHAKE":
			self.sendto(data, address)
			self.write_log("snd",data_type, seq_num,"0" ,ack_num)

		elif randNum > self.pdrop:
			self.sendto(data, address)
			self.write_log("snd",data_type, seq_num,len(data_segment),ack_num)

		else:
			self.num_drop += 1
			self.write_log("drop",data_type, seq_num,len(data_segment),ack_num)
			print "						drop:",  seq_num

	def print_info(self, data_sent,segment_sent, segment_resent, dup_ack ):

		info = "Amount of Data Transferred " + str(data_sent) + "\n"
		info += "Number of Data Segments Sent " + str(int(segment_sent)) + "\n"
		info += "Number of Packets Dropped " + str(self.num_drop)+ "\n"
		info += "Number of Retransmitted Segments " + str(segment_resent)+ "\n"
		info += "Number of Duplicate Acknowledgements received " + str(dup_ack)+ "\n"

		self.log_file.write(info)
		if segment_resent != self.num_drop:
			# print "Packets Dropped", self.num_drop,"Retransmitted",  segment_resent
			print "timeout too fast!"

	def close(self):

		self.log_file.close()
		socket.close(self)
