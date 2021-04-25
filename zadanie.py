#!/usr/bin/env python3
import socket
import os
import sys
import re
import signal
import hashlib

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
s.bind(('',9998))
signal.signal(signal.SIGCHLD,signal.SIG_IGN)
s.listen(5)

while True:
	connected_socket,address=s.accept()
	print(f'spojenie z {address}')
	pid_chld=os.fork()
	if pid_chld==0:
		s.close()
		f=connected_socket.makefile(mode='rw',encoding='utf-8')
		while True:
		
			poziadavka=f.readline()
					# 1) odpoved hlavicky "reply"
					# 2) odpoved obsah "content_reply"
			if "WRITE" == poziadavka:
			
				hlavicka=f.readline()
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
					
				hlavicka=f.readline()
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
					f.write('\n')	#po hlavičke prázdny riadok
					f.flush()
					sprava=f.read(content_length)
					hashS = hashlib.md5(sprava.encode())
					hashS = hashS.hexdigest()
					umiestnenie = os.path.join(mailbox, hashS)
					#os.mkdir(umiestnenie)
					with open (f"{mailbox}/{hashS}.txt","w") as file:
						file.write(f"{sprava}")
					status_num,status_comment=(100,'OK')
					content_reply='\n'
					
				f.write(f'{status_num} {status_comment}\n')
				f.write(content_reply)
				f.flush()
					
			elif "LS" == poziadavka:
			
				hlavicka=f.readline()
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
						f.write("\n") #po hlavičke prázdny riadok
						f.flush()
						
						print(os.listdir(mailbox))
						n = len(os.listdir(mailbox))
						subory=os.listdir(mailbox)
						status_num,status_comment=(100,'OK')
						content_reply=(f"Number-of-messages:{n}\n")
						
						f.write(f'{status_num} {status_comment}\n')
						f.write(f"{content_reply}\n")
						for subor in subory:
							f.write(f"{subor}\n")
						f.flush()
						
			elif "READ" == poziadavka:
				
				hlavicka=f.readline()
				m=re.match("\AMailbox",hlavicka)
				
				if m:
					mailbox = hlavicka
					k=re.split(":",mailbox)
					mailbox = k[1].rstrip()
					if "/" in mailbox:
						status_num,status_comment=(200,'Bad request')
						content_reply=''
					
				hlavicka=f.readline()
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
						with open (f"{mailbox}/{hashS}.txt", "r") as file:
							sprava=file.read()
							
					except ValueError:
						status_num,status_comment=(202,'No Read error')
						content_reply=''
					f.write('\n')	#po hlavičke prázdny riadok
					status_num,status_comment=(100,'OK')
					reply=len(sprava)
					content_reply=sprava
					f.flush()
			
				f.write(f'{status_num} {status_comment}\n')
				f.write(f"Content-length:{reply}\n")
				f.write("\n")
				f.write(f"{content_reply}")
				f.flush()

			elif "READ" or "WRITE" or "LS" != poziadavka:
				status_num,status_comment=(204,'Unknown method')
				content_reply=''
				f.write(f'{status_num} {status_comment}\n')
				f.write(content_reply)
				f.flush()
				sys.exit(0)
				connected_socket.close()
		print(f'{address} uzavrel spojenie')
		sys.exit(0)
	else:
		connected_socket.close()    

