### Instruction Manual and Protocol Explaination ###
1. Upon recieving a login message, send in two separate lines:
    - User: <your username>
    - Password: <your password>
failure to write it properly will result in a failure message and being logged off. Incorrect pass or user in the correct format will promt additional chances to attempt sending a correct pass and user

2. Once you successfully logged in, you may use the following commands:
    - calculate: X Y Z
    - is_palindrome: X
    - is_primary: X
failure to write it properly will result in a failure message and being logged off

2.5 If at any point an error takes place
	- there will be a header in the format: "Error: <err message here>" 
	- the client will identify this header and will know that means the server has shut it out, and will close the connection on its end

3. Protocol breakdown:
    All messages are initially encoded using utf-8, and then are packed with a 4 byte header that represents
    the amount of bytes in the message (NOT the packet as a whole. So, if the message is 6 bytes long, the 
    header will read 6, while the packet itself is 10 bytes). 

    In order to do this, first use .encode('utf-8) on your message, then use the struct library's pack function
    on the length of the encoded message. IMPORTANT: use BIG endian! ex: struct.pack('!I', len(encoded_message))

    The reverse must be done to read the packets. You may use the first 4 bytes to know how many bytes to expect 
    (minus the header). Use unpack on the first four bytes, then decode the rest of the recieved message.

    User may ONLY use english letters and characters (1 byte characters in utf-8).

    Additionally, due to the header size being 4 bytes, user may only use 2^32-1 characters in any given message.