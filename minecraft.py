import asyncore, socket, struct

# lengths of various structures...
BYTE=1
SBYTE=1
SHORT=2
STRING=64
BYTEARRAY=1024

# Messages to send. Not all code complies with this.
client_messages = {
	0:  (0,  "Player Ident", "BB64s64sB"),
	5:  (5,  "Set Block", "BhhhBB"),
	8:  (8,  "Pos & Orient", "BBhhhBB"),
	13: (13, "Message", "BB64s")}

# Messages to recv.
server_messages = {
	0:  (0,  'Server Ident', BYTE+BYTE+STRING+STRING+BYTE, "BB64s64sB"),
	1:  (1,  'Ping', BYTE, "B"),
	2:  (2,  'Level Init', BYTE, "B"),
	3:  (3,  "Level Data Chunk", BYTE+SHORT+BYTEARRAY+BYTE, "Bh1023sB"),
	4:  (4,  "Level Finalize", BYTE+SHORT+SHORT+SHORT, "Bhhh"),
	6:  (6,  "Set Block", BYTE+SHORT+SHORT+SHORT+BYTE, "BhhhB"),
	7:  (7,  "Spawn Player", BYTE+BYTE+STRING+SHORT+SHORT+SHORT+BYTE+BYTE, "BB64shhhBB"),
	8:  (8,  "Teleport", BYTE+BYTE+SHORT+SHORT+SHORT+BYTE+BYTE, "BBhhhBB"),
	9:  (9,  "Pos & Orient Update", BYTE+BYTE+SBYTE+SBYTE+SBYTE+BYTE+BYTE, "BBbbbBB"),
	10: (10, "Position Update", BYTE+BYTE+SBYTE+SBYTE+SBYTE, "BBbbb"),
	11: (11, "Orient Update", BYTE+BYTE+BYTE+BYTE, "BBBB"),
	12: (12, "Despawn", BYTE+BYTE, "BB"),
	13: (13, "Message", BYTE+BYTE+STRING, "BB64s"),
	14: (14, "Disconnect", BYTE+STRING, "B64s"),
	15: (15, "User Type", BYTE+BYTE, "BB")}

for id, data in client_messages.items():
	client_messages[data[1]] = (data[0], data[1], data[2])
for id, data in server_messages.items():
	server_messages[data[1]] = (data[0], data[1], data[2])


class MinecraftBot(asyncore.dispatcher):
	def __init__(self, addr):
		asyncore.dispatcher.__init__(self)
		self.x, self.y, self.z = (0,0,0)
		self.level_size=(0,0,0)
		self._data = ""
		self._send = []
		
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.username, self.password, self.sessid = self.login()
		self.connect(addr)
	
	def login(self):
		return 'jcsmeuk', 'faketokenacceptedbymyservermmmpie', 1
	
	def write(self, type, *args):
		self._send.append(struct.pack(client_messages[type][2], *args))
	
	def handle_connect(self):
		print 'Connected.'
		self.write("Player Ident", 0, 7, self.username.ljust(64), self.password.ljust(64), 0)
	
	
	def handle_read(self):
		self._data += self.recv(512)
		if self._data == '':
			self.handle_close()
		id, type, length, format = server_messages[ord(self._data[0])]
		if not (len(self._data)>=length): # You probably won't need this here... I'm using asyncore, which doesn't handle this myself
			print '*** BUFFER UNDERFLOW (big packet being sent?) (Extra data needed to parse: %d)' % (length-len(self._data))
			return
		
		data = self._data[:length]
		self._data = self._data[length:]
		try:
			data = struct.unpack(format, data)
		except: # Obviously something fucked up, and i'm either not getting long enough data, or the wrong struct.
			print '*** ERROR in UNPACKING', type
			print 'Length of data', len(data)
			print 'Struct expects', length
			if len(data)==length:
				print 'Length CORRECT'
			print 'struct', format
			print 'Data dump:', `data`
			raise
		
		if type in ("Level Data Chunk", 'Teleport', 'Set Block'):
			pass # LOL, SPAM.
		else:
			print type+':',`data`
		
		if type == "Level Finalize":
			self.level_size = data[1:]
		if type == 'Message': # != work.
			print 'Level is %s' % `self.level_size`
			if 'LOVE YOU' in data:
				self._send.append(struct.pack("BB64s", 8,255,"jcsmeuk: &f THIS IS A TEST \x03 lol"))
				msg="<3 you jstoker."
		
		if type == 'Level Ident':
			self.x = self.level_size[0]/2
			self.y = self.level_size[1]/2
			self.z = self.level_size[2]/2
			self._send.append(struct.pack("BBhhhBB", 8, 255, self.x,self.y,self.z, 0, 128))
		if type == 'Ping': # != work.
			self.x += 1
			self.y += 1
			self.z = self.level_size[2]/2
			self._send.append(struct.pack("BBhhhBB", 8, 255, self.x,self.y,self.z, 0, 128))
	
	# Again, you probably won't want this.
	def handle_write(self):
		print 'Send: '+`self._send[0]`
		self.send(self._send.pop(0))

	# Or this!
	def writable(self):
		if self._send:
			return True
		return False

if __name__ == '__main__':
	MinecraftBot(('127.0.0.1', 25565))
	asyncore.loop()
