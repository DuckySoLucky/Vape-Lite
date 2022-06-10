import asyncio
import pathlib
import ssl
import websockets
import queue

#The code is dirty since I have NO IDEA on how asyncio works on python
#But it somehow works, yay

SERVER_IP = "localhost"
SERVER_PORT = 8765

TARGET = "wss://vape.sexy:8080"

send_q = queue.Queue()
recv_q = queue.Queue()

async def writeLog(data):
    with open("logging.log", "ab") as f:
        f.write(data)

xor_key = 0
async def xor_string(text: bytes) -> bytes:
    global xor_key
    return bytes([b ^ xor_key for b in text])

nextFileSize = -1
currentFileSize = 0

async def server_recv(websocket):
    global send_q, xor_key, nextFileSize, currentFileSize
    recvdata = await websocket.recv()
    if type(recvdata) is str:
        recvdata = recvdata.encode("ascii")
    await writeLog("SEND :\n".encode("ascii") + recvdata)
    
    
    str_recvdata = recvdata.decode("ascii")
    
    # if nextFileSize != -1:#Receiving file
        # with open("Dump5", "ab") as f:
            # f.write(await xor_string(recvdata))
        # currentFileSize += len(recvdata)
        # if currentFileSize >= nextFileSize:
            # nextFileSize = -1
    # else:
    
    str_recvdata = str_recvdata.split("\n")
    if isnumeric(str_recvdata[0]):
        packet_id = int(str_recvdata[0])
    
        if packet_id == 12 and len(str_recvdata) >= 2:#Packet that sets the xor key
            xor_key = int(str_recvdata[1])
            print(f"SET XOR KEY : {xor_key}")
        elif packet_id == 8 and len(str_recvdata) >= 3:
            class_name = (await xor_string(str_recvdata[1].encode("ascii"))).decode("ascii")
            field_name = (await xor_string(str_recvdata[2].encode("ascii"))).decode("ascii")
            
            print(f"[FieldMap] Class : {class_name} Field : {field_name}")
        elif packet_id == 9 and len(str_recvdata) >= 3:
            class_name = (await xor_string(str_recvdata[1].encode("ascii"))).decode("ascii")
            method_name = (await xor_string(str_recvdata[2].encode("ascii"))).decode("ascii")
            
            print(f"[MethodMap] Class : {class_name} Method : {method_name}")

    # if len(str_recvdata) == 7 and isnumeric(str_recvdata) and int(str_recvdata) == 945727:
        # nextFileSize = 945727
    
    send_q.put(recvdata)

async def server(websocket, path):    
    ip = websocket.remote_address[0];
    print(f"New client from {ip} !")
    
    global recv_q
    while True:
        while not recv_q.empty():
            await websocket.send(recv_q.get())
            # print("RECV")
        try:
            await asyncio.wait_for(server_recv(websocket), timeout=1.0)
        except asyncio.TimeoutError:
            pass
            # print('Server timeout!')

    
async def client_recv(websocket):
    global recv_q
    recvdata = await websocket.recv()
    if type(recvdata) is str:
        recvdata = recvdata.encode("ascii")
    await writeLog("RECV :\n".encode("ascii") + recvdata)
    
    if len(recvdata) < 230:
        decoded = (await xor_string(recvdata)).decode("ascii")
        print(f"MAPPING : {decoded}")
    
    recv_q.put(recvdata)

async def client():
    global send_q
    client_ssl_context = ssl.create_default_context()
    client_ssl_context.check_hostname = False
    client_ssl_context.verify_mode = ssl.CERT_NONE
    
    uri = TARGET
    async with websockets.connect(
        uri, ssl=client_ssl_context
    ) as websocket:
        print("Connected to the server!")
        while True:
            while not send_q.empty():
                await websocket.send(send_q.get())
                # print("SEND")
            try:
                await asyncio.wait_for(client_recv(websocket), timeout=1.0)
            except asyncio.TimeoutError:
                pass
                # print('Client timeout!')

def main():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert_file = pathlib.Path(__file__).with_name("cert.pem")
    key_file = pathlib.Path(__file__).with_name("key.pem")
    ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)

    start_server = websockets.serve(
        server, SERVER_IP, SERVER_PORT, ssl=ssl_context
    )
    print(f"Listening on {SERVER_IP}:{SERVER_PORT}")
    
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_until_complete(client())
    
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()