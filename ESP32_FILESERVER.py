import usocket
import network
import os
import ure
import machine
import uselect
from machine import Pin, SoftSPI #SoftSPI is used to create a virtual SPI
import time
from sdcard import SDCard
import select

###### SET-UP SECTION ######

ssid = 'Your_SSID'
password = 'password'

try:
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(ssid, password)
except:
    print('everything is fine')

while not sta_if.isconnected():
    pass

# Create a virtual SPI object with the appropriate pins
spisd = SoftSPI(-1,
                miso=Pin(13),
                mosi=Pin(12),
                sck=Pin(14))

# Create a SD card object
sd = SDCard(spisd, Pin(27)) # 27 is the Chip Select (CS) pin
vfs=os.VfsFat(sd)
os.mount(vfs, '/dev')
	
###### END OF SET-UP SECTION ######

def flash_led():
    led = Pin(2, Pin.OUT)
    led.value(1)
    time.sleep(0.5)
    led.value(0)
    return

def create_destination_dir(file_path):
    backup_dir = '/dev/BACKUP'
    path_list = file_path.split('/')
    print(path_list)
    path_string = "" + backup_dir
    try:
        os.mkdir(path_string)
    except OSError as e:
        pass
    for folder in path_list:
        if folder == "":
            continue
        else:
            path_string += f"/{folder}"
            try:
                os.mkdir(path_string)
            except OSError as e:
                pass
def save_file(conn):
    led = Pin(2, Pin.OUT)
    led.value(1)
    
    def pass_data(path, filename, buffer):
        create_destination_dir(path)
        with open('/dev/BACKUP/' + path + '/' + filename, 'ab') as dest_file:
            dest_file.write(buffer)        

    buffer = b''  # Initialize buffer
    poller = uselect.poll()
    poller.register(conn, uselect.POLLIN)  # Register the socket for input events
        
    while True:
        events = poller.poll(1000)  # Poll with a timeout of 1 second
        if not events:
            print('timeout reached')
            led.value(0)
            break
        recv_data = conn.recv(15000)
        buffer += recv_data
        print('Buffer size:', len(buffer))
        if not recv_data:
            print('Data stream ended')
            led.value(0)
            f.close()
            break
        if b'\r\n\r\n' in buffer:
            '''If header found in buffer:'''
            header_end = buffer.find(b'\r\n\r\n')
            header = buffer[:header_end].decode('utf-8')
            name_match = ure.search('filename="(.+\..+)";', header)
            path_match = ure.search('path="(.+)"', header)
            filename = name_match.group(1)
            path = path_match.group(1)
            content_start = header_end + 1  # Include the length of \r\n\r\n
            content = buffer[content_start:]  # Get the content part
            print(f'FIRST WRITE: {content}')
            pass_data(path, filename, content)
            remaining_data = buffer[:header_end + 1] #Handle remaining data in the buffer
            print(f"REMAINING DATA: {remaining_data}")
            buffer = b''  # Clear the buffer after processing
            buffer += remaining_data
            print('Bytes written:', len(content))
            continue
                
        if buffer and not buffer.endswith(b'\r\n\r\n'):
            print('x'*20)
            pass_data(path, filename, buffer)
            buffer = b''  # Clear the buffer after processing
            print('Bytes written:', len(buffer))
            continue
            
    print('exited loop') 
    led.value(0)
    return True, path, filename

def get_html_form(file_list):
    
    html_form = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>File Explorer</title>
    </head>
    <body>
        <h1>File Explorer</h1>
        <ul>
    """
    x = 0
    for file_path in file_list:
        path = ''; f = ''
        path_n_file = file_path
        parts = path_n_file.split('/')
        filename = parts[-1]
        parts.pop(-1)
        print('PARTS:',parts, type(parts))
        for part in parts:
            print('PART:',part)
            path += part + '/'
        print('PATH',path)
        if x == 0:
            p = path; x = 1;
            html_form += f"<h4>{p}</h4>"
        if p == path:
            print('p IS path')
            html_form += f'<li><a href="/download/{file_path}">{filename}</a></li>'
        else:
            print('p is NOT path')
            p = path
            for part in parts:
                f += part + '/'
            html_form += f"<h4>{f}</h4>"
        
    html_form += """
        </ul>
    </body>
    </html>
    """
    return html_form

def extract_filename_from_GET(request):
    match = ure.search("GET /download/(.*?) HTTP", request)
    if match:
        requested_file = match.group(1)
        return requested_file
        

def walk(dirname, base_dir='/dev/BACKUP'):
    file_paths = [] 
    
    try:
        for name in os.listdir(dirname):
            path = dirname + '/' + name  
            try:
                if os.listdir(path):  # Check if it's a directory
                    file_paths.extend(walk(path, base_dir)) 
            except OSError:
                file_paths.append(path[len(base_dir) + 1:])  # Append the relative path
                pass 
    except OSError:
        pass  
    
    return file_paths

def main():
    '''Create a socket awaiting POST requests'''
    up_socket = usocket.socket()
    up_socket.bind(('0.0.0.0', 1030))
    up_socket.listen(5)
    
    '''Create a socket awaiting GET requests'''
    down_socket = usocket.socket()
    down_socket.bind(('0.0.0.0', 8050))
    down_socket.listen(5)
    while True:
        read_sockets, _, _ = select.select([up_socket, down_socket], [], [])
        for sock in read_sockets:
            if sock == up_socket:
                conn, addr = up_socket.accept()
        
                if conn:
                    success, path, filename = save_file(conn)
                    if success:
                        flash_led()
                        conn.send('HTTP/1.1 201 Created\r\n\r\nFile uploaded.\n')
                        print('file save successful')
                        print(f'File successfuly saved to /dev/BACKUP/{path}/{filename}')
                        conn.send(f'File successfuly saved to /dev/BACKUP/{path}/{filename}\n')
                    else:
                        conn.send('Failure saving file.\n')
                    conn.close()
            
            elif sock == down_socket:
                conn1, addr1 = down_socket.accept()
                print(conn1)
                print(addr1)
                if conn1:
                    request = conn1.recv(1024).decode()
                    method = request.split(' ')[0]
                    print(f'METHOD: {method}')
                    if method == "GET":
                        start_of_request = request[:14]
                        print(start_of_request)
                        if "GET / HTTP/" in start_of_request:
                            file_paths = walk('/dev/BACKUP')
                            html_form = get_html_form(file_paths)
                            conn1.send('HTTP/1.1 200 OK\r\n')
                            conn1.send(f'Content-Length: {len(html_form)}\r\n')
                            conn1.send('Content-Type: text/html\r\n')
                            conn1.send('\r\n')  # End of headers
                            conn1.send(html_form)
                            print('form sent')
                        elif "GET /download/" in start_of_request:
                            print(request)
                            requested_file = extract_filename_from_GET(request)
                            print(requested_file)
                            print(f'serving /dev/BACKUP/{requested_file}')
                            with open(f'/dev/BACKUP/{requested_file}', 'rb') as f:
                                conn1.send('HTTP/1.1 200 OK\r\n')
                                conn1.send('Content-Type: application/octet-stream\r\n')  # Adjust the content type as needed
                                conn1.send('Content-Disposition: attachment\r\n')  # Suggests download
                                conn1.send('\r\n')  # End of headers
                                while True:
                                    data = f.read(16000)
                                    if not data:
                                        break
                                    conn1.send(data)
                        conn1.close()
                
print('Connection successful')
print("Connected to WiFi")
print("IP address:", sta_if.ifconfig()[0])

main()




