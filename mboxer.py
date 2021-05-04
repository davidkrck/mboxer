#!/usr/bin/env python3
import socket
import os
import sys
import re
import signal
import hashlib

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
s.bind(('',9999))
signal.signal(signal.SIGCHLD,signal.SIG_IGN)
s.listen(5)


while True:
	connected_socket,address=s.accept()
	print(f'spojenie z {address}')
	pid_chld=os.fork()
	
	if pid_chld==0:
		s.close()
		f=connected_socket.makefile('rwb')
		
		while True:
		
			poziadavka=f.readline().decode("utf-8").strip()
			
			if not poziadavka:
				break
			
#WRITE
			if re.match("^WRITE$",poziadavka):
			
				hlavicka=f.readline().decode("utf-8")
				m=re.match("\AMailbox",hlavicka)
				
				if m:
				
					mailbox = hlavicka
					k=re.split(":",mailbox)
					mailbox = k[1].rstrip()
					
					if "/" in mailbox or not (all(ord(char) < 128 for char in mailbox[0])):
						status_num,status_comment=(200,'Bad request')
						header_reply=''
						content_reply=''
						
					if not os.path.exists(mailbox):
						os.mkdir(mailbox)
					
				hlavicka=f.readline().decode("utf-8")
				c=re.match("\AContent-length",hlavicka)
				
				if c:
					content_length = hlavicka
					l=re.split(":",content_length)
					content_length = l[1].rstrip("\n")
					content_length = int(content_length)
					
					if  content_length <= 0:
						status_num,status_comment=(200,'Bad request')
						header_reply=''
						content_reply=''
						
					 
				if m and c:
					sprava = f.read(content_length).decode("utf-8")
					hashS = hashlib.md5(sprava.encode())
					hashS = hashS.hexdigest()
					umiestnenie = os.path.join(mailbox, hashS)
					
					try:
						with open (f"{mailbox}/{hashS}","w") as file:
							file.write(f"{sprava}")
						
						status_num,status_comment=(100,'OK')
						header_reply=''
						content_reply=''
					
					except FileNotFoundError:
						status_num,status_comment=(203,'No such mailbox')

#LS
			elif re.match("^LS$",poziadavka):
			
				hlavicka=f.readline().decode("utf-8")
				m=re.match("\AMailbox",hlavicka)
				
				if m:
					mailbox = hlavicka
					k=re.split(":",mailbox)
					mailbox = k[1].rstrip()
					
					if "/" in mailbox or not (all(ord(char) < 128 for char in mailbox[0])):
						status_num,status_comment=(200,'Bad request')
						header_reply=''
						content_reply=''
						
					if not os.path.isdir(mailbox):
						status_num,status_comment=(203,'No such mailbox')
						header_reply=''
						content_reply=''
						
					else:
						n = len(os.listdir(mailbox))
						subory=os.listdir(mailbox)
						
						status_num,status_comment=(100,'OK')
						header_reply=(f"Number-of-messages:{n}\n")
						for subor in subory:
							content_reply = '\n'.join(subory) + '\n'
							
				hlavicka=f.readline().decode("utf-8")
				
#READ						
			elif re.match("^READ$",poziadavka):
				
				hlavicka=f.readline().decode("utf-8")
				m=re.match("\AMailbox",hlavicka)
				
				if m:
					mailbox = hlavicka
					k=re.split(":",mailbox)
					mailbox = k[1].rstrip()
					if "/" in mailbox or not (all(ord(char) < 128 for char in mailbox[0])):
						status_num,status_comment=(200,'Bad request')
						content_reply=''
						header_reply=''
						
					
				hlavicka=f.readline().decode("utf-8")
				c=re.match("\AMessage",hlavicka)
				
				if c:
					hashS = hlavicka
					l=re.split(":",hashS)
					hashS = l[1].rstrip()
					if "/" in hashS or not (all(ord(char) < 128 for char in hashS[0])):
						status_num,status_comment=(200,'Bad request')
						header_reply=''
						content_reply=''
						
				if m and c:
					try:
						with open (f"{mailbox}/{hashS}", "r") as file:
							status_num,status_comment=(100,'OK')
							content_reply=file.read()
							header_reply = (f'Content-length:{len(content_reply)}\n')
								
					except FileNotFoundError:
						status_num,status_comment=(201,'No such message')
						header_reply=''
						content_reply=''
						
					except OSError:
						status_num,status_comment=(202,'Read error')
						header_reply=''
						content_reply=''
				
				hlavicka=f.readline().decode("utf-8")
						
			else:
				status_num,status_comment=(204,'Unknown method')
				
				f.write(f'{status_num} {status_comment}\n'.encode("utf-8"))
				f.flush()
				
				sys.exit(0)
				connected_socket.close()
				
			f.write(f'{status_num} {status_comment}\n'.encode("utf-8"))
			f.write(f"{header_reply}\n".encode("utf-8"))
			if content_reply != "":
				f.write(f"{content_reply}".encode("utf-8"))

			f.flush()
	
		sys.exit(0)


	else:
		connected_socket.close()    

