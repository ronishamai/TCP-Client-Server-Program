#!/usr/bin/python3
from socket import *
import struct
import sys

# The size of the header that contains the length of the message
LEN_HEADER_SIZE = 4

# Input: a string of the message you want to send
# Output: the header that contains the length of the message followed by the message in utf-8 encoding
def insert_length_header(message):
    encoded_message = message.encode('utf-8')
    header = struct.pack('!I', len(encoded_message))
    return  header + encoded_message

# Input: a string of the message we received
# The function: Separated between the length of the message (the header) and the message (and decoded it)
# Output: a tuple containing the dencoded message (utf-8), and the length of the message ()
def extract_length_header(message):
    try:
        len = struct.unpack('!I', message[:LEN_HEADER_SIZE])[0] # updates bytes we wait for
        message = message.decode('utf-8')[LEN_HEADER_SIZE:] # get rid of byte header
        return message, len
    except:
        return message, None

# Implementation for recvall (similar to what we saw in recitation 2 slide 32)
# Input: a socket
# The function: 
#   - each time receives part of the message and concatenate to the entire message
#   - If this is the first time we have started receiving information about this message, the length of the message is extracted. 
#   - Indicator for the end of receiving the message: length of message == length in the header
# Output: the full message (decoded, without the length header)
def recvall(sock):
    extracted = False
    message = b''
    while True:
        message += sock.recv(1024)
        if len(message) >= 4 and not extracted:
            extracted_msg, msg_length = extract_length_header(message)
            extracted = True
            message = extracted_msg
        if len(message) == msg_length:
            break
    return message

def main(hostname='localhost', port=1337):
    try:
        client = socket(AF_INET, SOCK_STREAM) # create an (IPV4, TCP) socket object 
        client.connect((hostname, port)) # connect 
    except Exception as e:
        print('Error: conncection failed')
        return

    try:
        # Recieve a welcome msg from the server
        print(recvall(client)) 

        # Send Username + Password, loop till recieve a msg from the server - Login approval
        while True:
            username = input() 
            client.sendall(insert_length_header(username)) 
            password = input() 
            client.sendall(insert_length_header(password))    
            response = recvall(client)
            print(response)
            if (response == f'Hi {username.split()[1]}, good to see you.'):
                break
            if response.split(' ')[0] == 'Error:':
                break

        # Send commands, loop till recieve an error msg from the server or asking to quit the program
        while True:
            if response.split(' ')[0] == 'Error:':
                break
            command = input() 
            client.sendall(insert_length_header(command))
            if (command == 'quit'):
                break
            response = recvall(client)
            print(response) 

    except Exception as e:
        print(f'Error: {str(e)}')
        client.close()
        return
    
    # close the connection
    client.close()


if __name__ == '__main__':
    # According to the forum of the exercise in the model, it is assumed that there is no need to check the correctness of input, if it is not correct, an error is thrown when trying to initialize the socket and connect
    # Optional arguments are hostname, port (port cannot be given without hostname); their default values are localhost, 1337
    if len(sys.argv) == 3:
        main(sys.argv[1], int(sys.argv[2])) # hostname, port
        
    elif len(sys.argv) == 2:
        main(sys.argv[1]) # hostname
        
    elif len(sys.argv) == 1: 
        main() # all the arguments are optional (except for the program name)
        
    else:
        raise Exception("Error: Too many args!")