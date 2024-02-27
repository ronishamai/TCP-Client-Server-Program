#!/usr/bin/python3
from socket import *
import sys
import select
import struct

# Programs globals
host = '0.0.0.0' 
LEN_HEADER_SIZE = 4
rlist, wlist, xlist, timeout = [],[],[], 0
sock_to_msg_recv, sock_to_msg_send, sock_to_username, sock_to_password = {}, {}, {}, {}
sock_to_recv_case = {} # 0 - username, 1- password, 3- command
log_off_list = []

# Input: a string of the message you want to send
# Output: the header that contains the length of the message followed by the message in utf-8 encoding
def insert_length_header(message):
    encoded_message = message.encode('utf-8')
    header = struct.pack('!I', len(encoded_message))
    return  header + encoded_message

# Input: a string of the message we received
# The function: Separated between the length of the message (the header) and the message (and decoded it)
# Output: a tuple containing the dencoded message (utf-8), and the length of the message ()
def extract_length_header(msg):
    try:
        len = struct.unpack('!I', msg[:LEN_HEADER_SIZE])[0] ##updates bytes we wait for
        msg = msg.decode('utf-8')[LEN_HEADER_SIZE:] #TODO: need to do decode only once we got full message. get rid of byte header
        return msg, len
    except:
        return msg, None

# Input: a string that represents a calculation request (2 integers & 1 op the 4 basic operators)
# Output: the calculation result if in the correct format, in any case another error
def calculate(X, Y, Z):
    try:
        num1 = int(X)
        op = Y
        num2 = int(Z)
    except:
        raise Exception("Error: Incorrect format, need <int><operator><int>")
    
    # switch cases 
    if op == '+':
        return num1 + num2
    elif op == '-':
        return num1 - num2
    elif op == 'x':
        return num1 * num2
    elif op == '/' :
        if num2 == 0 :
            raise Exception("Error: can't divide by zero")
        return f'{num1 / num2:.2f}'
    else:
        raise Exception("Error: Illegal operator, can only use +, -, /, *")

# Input: a string that represents a number
# Output: YES if it's a palindrome, NO if it's not a palindrome, in any case another error
def is_palindrome(str):
    try:
        float(str)
    except:
        raise Exception("Error: Input must be a legal int or float!")
    return "Yes" if str == str[::-1] else "No"

# Input: a string that represents a number
# Output: YES if it's prime, NO if it's not prime, in any case another error
def is_primary(str):
    try:
        num = int(str)
    except:
        raise Exception("Error: Input must be an integer!")
    
    for i in range(2,int(num**0.5)+1):
        if num % i == 0:
            return "No"
    return "Yes"

# Input: socket to be closed + rlist
# The function: cleans up all the the data structures that are associated with the socket and closes it
def close_sock(sock, rlist):
    try:
        rlist.remove(sock)
    except:
        pass
    try:
        wlist.remove(sock)
    except:
        pass
    try:
        log_off_list.remove(sock)
    except:
        pass
    try:
        sock_to_recv_case.pop(sock)
    except:
        pass
    try:
        sock_to_password.pop(sock)
    except:
        pass
    try:
        sock_to_username.pop(sock)
    except:
        pass
    try:
        sock_to_msg_send.pop(sock)
    except:
        pass
    try:
        sock_to_msg_recv.pop(sock)
    except:
        pass
    sock.close()

# Input: command message
# The function: calls the appropriate calculation function, according to the 4 cases: calculation, is_palindrome, is_prime, quit, or an error in any other case.
# Output: the calculation result (None if the correct command was not called), and a log-off flag (indicates if the client needs to be disconnected)
def response(message):
    log_off = False
    try:
        command = message.split(' ')
        if command[0] == 'calculate:':
            if len(command) != 4:
                raise Exception("Error: Incorrect format")
            try:
                response_msg = f'response: {calculate(command[1], command[2], command[3])}.'
            except Exception as e:
                raise Exception(str(e))
    
        elif command[0] == 'is_palindrome:':
            if len(command) != 2:
                raise Exception("Error: Incorrect format")
            try:
                response_msg = f'response: {is_palindrome(command[1])}.'
            except Exception as e:
                raise Exception(str(e))

        elif command[0] == 'is_primary:':
            if len(command) != 2:
                raise Exception("Error: Incorrect format")
            try:
                response_msg = f'response: {is_primary(command[1])}.'
            except Exception as e:
                raise Exception(str(e))
        
        elif command[0] == 'quit': 
            log_off = True
            response_msg = None

        else:
            log_off = True
            response_msg = "Error: Incorrect command"
        
    except Exception as e:
        return str(e), True
    
    return response_msg, log_off

# Input: username, password, path
# The function: processing the login request, verifying if it was done in the correct format and if so verifying with the user and password file
# Output: username if the username and the password are in the correct format and appears in the file, otherwise None
def login_checker(username, password, path):
    username, password = username.split(': ', 1), password.split(': ', 1)
    if username[0] != "User" or len(username) != 2:
        raise Exception("Error: Send username in correct format")
    elif password[0] != "Password" or len(password) != 2:
        raise Exception("Error: Send password in correct format")
    
    else:
        username, password = username[1], password[1]
        try:
            with open(path, 'r') as pass_file:
                for line in pass_file:
                    info = line.strip().split()
                    if info[0] == username:
                        if info[1] == password: # ignores newline, username and the separating tab
                            return username
        except:
            return None
    return None     

# Input: port
# The function: create an (IPV4, TCP) listening socket object binded to (ip, port)
# Output: the servers socket
def init_server_socket(port):
    server = socket(AF_INET, SOCK_STREAM) # create an (IPV4, TCP) socket object 
    server.bind((host, port)) # bind the socket to (ip, port)
    server.listen() # prepare for unlimited number of clients
    return server

# Input: the servers socket
# The function: Receives the connection to the client, adds it to the list rlist, initializes the data structures and establishes the sending of the welcome message
# Output: The client socket if the connection was successful, otherwise prints an error
def accept_new_connection(server):
    try:
        (client, addr) = server.accept() 
        #rlist.append(client)
        sock_to_msg_send[client] = insert_length_header('Welcome! Please log in.') 
        sock_to_username[client], sock_to_password[client], sock_to_msg_recv[client] \
            = [None,b''], [None,b''], [None,b'']
        return client
    except Exception as e:
        print('Error: conncection failed')
        return

def main(path, port=1337):

    server = init_server_socket(port) # create an (IPV4, TCP) listening socket object binded to (ip, port)
    rlist = [server]
    
    while rlist:
        readable, writeable, _ = select.select(rlist, wlist, xlist, timeout) # multiplexing solution for the blocking problem; returns which of the sockets are read/write/except ready
        
        # SEND CASE (send all implementation)
        for sock in writeable:                           
            
            sent = sock.send(sock_to_msg_send[sock]) # send parts of the msg each time
            if (sent < len(sock_to_msg_send[sock])): # haven't done sending
                sock_to_msg_send[sock] = (sock_to_msg_send[sock])[sent:] # updates from where to send
            else: # done sending
                sock_to_msg_send.pop(sock)
                wlist.remove(sock) 
                rlist.append(sock) # starts receiving
                if not(sock in sock_to_recv_case.keys()): # socket not existing in status list indicates it has recently been opened
                    sock_to_recv_case[sock] = 0 # username status

                if sock in log_off_list: # log-off client
                    close_sock(sock, rlist)

        # RECEIVE CASES 
        for sock in readable:     
            
            # RECEIVE CASE 1: a new client wants to connect the server  
            if sock is server: 
                client = accept_new_connection(sock) # inits a connection with the client
                if client: # connection succided
                    wlist.append(client) # sending 
                else: # connection failed
                    continue   

            # RECEIVE CASE 0: receiving username
            elif sock_to_recv_case[sock] == 0:
                msg = sock.recv(4) # receiving part of the msg
                
                if sock_to_username[sock][0]: # length is already extracted
                    msg = msg.decode('utf-8') 
                    sock_to_username[sock][1] += msg # concatinating to the msg we received so far on this connection
                
                elif len(msg) >= 4 and sock_to_username[sock][0] is None: # got all the message length header and haven't extracted it yet
                    sock_to_username[sock][1], sock_to_username[sock][0] = extract_length_header(msg) 

                if len(sock_to_username[sock][1]) == sock_to_username[sock][0]: # finished receiving the message (msg received length equals to the header content)
                    sock_to_recv_case[sock] = 1 # case receiving password
                    
            
            # RECEIVE CASE 1: receiving password
            elif sock_to_recv_case[sock] == 1:
                msg = sock.recv(4)
                
                if sock_to_password[sock][0]: # length is already extracted
                    msg = msg.decode('utf-8')
                    sock_to_password[sock][1] += msg # concatinating to the msg we received so far on this connection
                
                elif len(msg) >= 4 and sock_to_password[sock][0] is None: # got all the message length header and haven't extracted it yet
                    sock_to_password[sock][1], sock_to_password[sock][0] = extract_length_header(msg)

                if len(sock_to_password[sock][1]) == sock_to_password[sock][0]: # finished receiving the message (msg received length equals to the header content)
                    rlist.remove(sock)   
                    wlist.append(sock) # case sending response - login succeeded/failed

                    try:
                        username = login_checker(sock_to_username[sock][1],sock_to_password[sock][1], path) # check username+password
                    except Exception as e: # login error
                        sock_to_msg_send[sock] = insert_length_header(str(e)) 
                        log_off_list.append(sock)
                        continue
              
                    if username: # login succeeded
                        sock_to_msg_send[sock] = insert_length_header(f'Hi {username}, good to see you.') # sending login confirmation
                        sock_to_recv_case[sock] = 2 # case receiving commands from client
                        sock_to_msg_recv[sock] = [None,b''] # init
                    else: # login failed
                        sock_to_msg_send[sock] = insert_length_header('Failed to login.') # sending the connection failed
                        sock_to_username[sock], sock_to_password[sock] = [None,b''], [None,b''] # init
                        sock_to_recv_case[sock] = 0 # case receiving username again

            # RECEIVE CASE 2: receiving commands
            elif sock_to_recv_case[sock] == 2: 
                msg = sock.recv(4)
                
                if sock_to_msg_recv[sock][0]: # length is already extracted
                    msg = msg.decode('utf-8')
                    sock_to_msg_recv[sock][1] += msg # concatinating to the msg we received so far on this connection
                
                elif len(msg) >= 4 and sock_to_msg_recv[sock][0] is None:  # got all the message length header and haven't extracted it yet
                    sock_to_msg_recv[sock][1], sock_to_msg_recv[sock][0] = extract_length_header(msg)

                if len(sock_to_msg_recv[sock][1]) == sock_to_msg_recv[sock][0]: # finished receiving the message (msg received length equals to the header content)
                    rlist.remove(sock)   
                    wlist.append(sock) # case sending the commands response
                    sock_to_msg_send[sock], log_off = response(sock_to_msg_recv[sock][1])

                    if log_off:
                        if not sock_to_msg_send[sock]: # none msg only if quit was called
                            close_sock(sock, rlist)
                            continue
                        else:
                            log_off_list.append(sock)    

                    sock_to_msg_recv[sock] = [None,b'']
                    sock_to_msg_send[sock] = insert_length_header(sock_to_msg_send[sock])

    server.close()
    
if __name__ == '__main__':
    # According to the forum of the exercise in the model, it is assumed that there is no need to check the correctness of input, if it is not correct, an error is thrown
    # Arguments are path + optional argument is port (default value is 1337)
    
    if len(sys.argv) == 2:
        path = sys.argv[1]
        main(path)
    
    elif len(sys.argv) == 3:
        path = sys.argv[1]
        port = int(sys.argv[2])
        main(path, port)
    
    else:
        raise Exception("Too many args!")
