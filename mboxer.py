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
		
			poziadavka=f.readline().decode("ASCII")
			print(poziadavka)
			
					# 1) odpoved hlavicky "reply"
					# 2) odpoved obsah "content_reply"
			if re.match("^WRITE$",poziadavka):
			
				hlavicka=f.readline().decode("ASCII")
				m=re.match("\AMailbox",hlavicka)
				
				if m:
					mailbox = hlavicka
					k=re.split(":",mailbox)
					mailbox = k[1].rstrip()
					if "/" in mailbox:
						status_num,status_comment=(200,'Bad request')
						content_reply=''
					if not os.path.exists(mailbox):
						os.mkdir(mailbox)
					
				hlavicka=f.readline().decode("ASCII")
				c=re.match("\AContent-length",hlavicka)
				
				if c:
					content_length = hlavicka
					l=re.split(":",content_length)
					content_length = l[1].rstrip("\n")
					content_length = int(content_length)
					if  content_length <= 0:
						status_num,status_comment=(200,'Bad request')
						content_reply=''
					elif not mailbox:
						status_num,status_comment=(203,'No such mailbox')
						content_reply=''
					 
				if m and c:
					f.write('\n'.encode("ASCII"))	#po hlavičke prázdny riadok
					f.flush()
					sprava=f.read(content_length).decode("ASCII")
					hashS = hashlib.md5(sprava.encode())
					hashS = hashS.hexdigest()
					umiestnenie = os.path.join(mailbox, hashS)
					with open (f"{mailbox}/{hashS}","w") as file:
						file.write(f"{sprava}")
					status_num,status_comment=(100,'OK')
					content_reply='\n'
					
				f.write(f'{status_num} {status_comment}\n'.encode("ASCII"))
				f.write(content_reply.encode("ASCII"))
				f.flush()
					
			elif re.match("^LS$",poziadavka):
			
				hlavicka=f.readline().decode("ASCII")
				m=re.match("\AMailbox",hlavicka)
				
				if m:
					mailbox = hlavicka
					k=re.split(":",mailbox)
					mailbox = k[1].rstrip()
					if "/" in mailbox:
						status_num,status_comment=(200,'Bad request')
						content_reply=''
					if not os.path.isdir(mailbox):
						status_num,status_comment=(203,'No such mailbox')
						content_reply=''
					else:
						f.write("\n".encode("ASCII")) #po hlavičke prázdny riadok
						f.flush()
						
						print(os.listdir(mailbox))
						n = len(os.listdir(mailbox))
						subory=os.listdir(mailbox)
						status_num,status_comment=(100,'OK')
						content_reply=(f"Number-of-messages:{n}\n")
						
						f.write(f'{status_num} {status_comment}\n'.encode("ASCII"))
						f.write(f"{content_reply}\n".encode("ASCII"))
						for subor in subory:
							f.write(f"{subor}\n".encode("ASCII"))
						f.flush()
						
			elif re.match("^READ$",poziadavka):
				
				hlavicka=f.readline().decode("ASCII")
				m=re.match("\AMailbox",hlavicka)
				
				if m:
					mailbox = hlavicka
					k=re.split(":",mailbox)
					mailbox = k[1].rstrip()
					if "/" in mailbox:
						status_num,status_comment=(200,'Bad request')
						content_reply=''
					
				hlavicka=f.readline().decode("ASCII")
				c=re.match("\AMessage",hlavicka)
				
				if c:
					hashS = hlavicka
					l=re.split(":",hashS)
					hashS = l[1].rstrip()
					if "/" in hashS:
						status_num,status_comment=(200,'Bad request')
						content_reply=''
					elif not mailbox:
						status_num,status_comment=(203,'No such mailbox')
						content_reply=''
						
				if m and c:
					try:
						with open (f"{mailbox}/{hashS}", "r") as file:
							sprava=file.read()
							
					except ValueError:
						status_num,status_comment=(202,'No Read error')
						content_reply=''
					f.write('\n'.encode("ASCII"))	#po hlavičke prázdny riadok
					status_num,status_comment=(100,'OK')
					reply=len(sprava)
					content_reply=sprava
					f.flush()
			
				f.write(f'{status_num} {status_comment}\n'.encode("ASCII"))
				f.write(f"Content-length:{reply}\n".encode("ASCII"))
				f.write("\n".encode("ASCII"))
				f.write(f"{content_reply}".encode("ASCII"))
				f.flush()

			elif re.match("^READ$",poziadavka) or re.match("^LS$",poziadavka) or re.match("^WRITE$",poziadavka) != poziadavka:
				status_num,status_comment=(204,'Unknown method')
				content_reply=''
				f.write(f'{status_num} {status_comment}\n'.encode("ASCII"))
				f.write(content_reply.encode("ASCII"))
				f.flush()
				sys.exit(0)
				connected_socket.close()
		print(f'{address} uzavrel spojenie')
		sys.exit(0)
	else:
		connected_socket.close()    

