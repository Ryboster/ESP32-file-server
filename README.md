# ESP32-file-server
A simple local file server built on ESP32. 

The ESP32 should have an SD card reader plugged in due to storage limitations on the board. You should wire the card reader the following way:
MISO > Pin 13
MOSI > Pin 12
SCK > Pin 14
CS > Pin 27

To upload files to the server you need to send it a properly formatted HTML header. You can see what it looks like in the client-side script.

Order of operations:
1. The ESP32 establishes a wifi connection.
2. The SD card reader is mounted at the /dev/ directory
3. ESP32 sets up 2 sockets; One for receiving files, and one for serving them. Receiving end is at port 1030, serving end at 8050. Serving end sends a HTML page back to the client, so you would ideally connect to it via a browser.
4. ESP32 checks readability of both sockets and once either of them can be read, it accepts the connection request.
5. ESP32 processes the request. If you're sending a file to it, it receives it at and saves it at the location specified in the header in chunks of 15kb. If you're accessing the receiving end, it looks for all the previously uploaded files and sets up a HTML page with the name and location of each file as well as the links to download them.
6. Once the request is processed, the connection is closed.
