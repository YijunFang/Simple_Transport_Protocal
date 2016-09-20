#!/usr/bin/python

import sys
import time
from socket import *



def create_header(seq_num, ack_num, ack_flag, syn_flag, fin_flag):
	string = str(seq_num)+" "
	string += str(ack_num)+" "
	string += str(ack_flag)+" "
	string += str(syn_flag)+" "
	string += str(fin_flag)+" "
	return string

def extract_header_handshake(data):
	header_flag = data.split(' ', 5)
	seq_num = header_flag[0]
	ack_num = header_flag[1]
	ack_flag = header_flag[2]
	syn_flag = header_flag[3]
	fin_flag = header_flag[4]

	if(fin_flag == '0'):
		if(syn_flag == '1'): #connection state - syn
			if(ack_flag == '0'): # 1st syn
				return "SYN"
			if(ack_flag == '1'):
				return "SYNACK"
		else:
			if(ack_flag == '1'): # 3rd ack
				return "ACK"
	elif(fin_flag == '1'):
		if(ack_flag == '0'): # 1st fin
			return "FIN1"
		if(ack_flag == '1'):
			return "FINACK1"
	elif(fin_flag == '2'):
		if(ack_flag == '1'): # 1st fin
			return "FIN2"
		if(ack_flag == '2'):
			return "FINACK2"

def extract_data(data):
	#print data
	data_flag = data.split(' ', 5)
	data_segment = data_flag[5]
	return data_segment

def extract_header_seqNum(data):
	header_flag = data.split(' ', 5)
	return int(header_flag[0])

def extract_header_ackNum(data):
	#print data
	header_flag = data.split(' ', 5)
	return int(header_flag[1])

def extract_header_delay(data):
	header_flag = data.split(' ', 5)
	ack_flag = header_flag[2]
	syn_flag = header_flag[3]
	fin_flag = header_flag[4]

	if(ack_flag == syn_flag == fin_flag == '0'):
		return "DATA"
	else:
		return "HANDSHAKE"


def extract_file_length(data):
	header_flag = data.split(' ', 5)
	return int(header_flag[5])

def extract_packet_type(data):
	header_flag = data.split(' ', 5)
	seq_num = header_flag[0]
	ack_num = header_flag[1]
	ack_flag = header_flag[2]
	syn_flag = header_flag[3]
	fin_flag = header_flag[4]

	if(ack_flag == syn_flag == fin_flag == '0'):
		return "D"

	if(fin_flag == '0'):
		if(syn_flag == '1'): #connection state - syn
			if(ack_flag == '0'): # 1st syn
				return "S"
			if(ack_flag == '1'):
				return "SA"
		else:
			if(ack_flag == '1'): # 3rd ack
				return "A"
	elif(fin_flag == '1'):
		if(ack_flag == '0'): # 1st fin
			return "F"
		if(ack_flag == '1'):
			return ""
	elif(fin_flag == '2'):
		if(ack_flag == '1'): # 2st fin
			return "FA"
		if(ack_flag == '2'):
			return "A"
