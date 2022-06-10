import asyncio
import pathlib
import ssl
import websockets
import sys
import os
import base64
import requests
import zipfile
import hashlib
import socket
import json
import pandas as pd
from tqdm import tqdm
from OpenSSL import crypto, SSL

SERVER_IP = "localhost"
SERVER_PORT = 8765
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

SERVER_IP = "localhost"
SERVER_PORT = 8765
print("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
print("┃   Cracked by DuckySoLucky #Qwack   ┃")
print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
print("") 

print(bcolors.OKGREEN + "Authorized" + bcolors.ENDC + bcolors.UNDERLINE + " » " + bcolors.WARNING + socket.gethostname() + bcolors.ENDC)
print(bcolors.WARNING + "Remote" + bcolors.ENDC + bcolors.UNDERLINE + " » " + bcolors.OKGREEN + "Connected" + bcolors.ENDC)
print(bcolors.HEADER + "Local" + bcolors.ENDC + bcolors.UNDERLINE + " » " + bcolors.OKGREEN + "Connected" + bcolors.ENDC)
print(bcolors.OKCYAN + "Forge" + bcolors.ENDC + bcolors.UNDERLINE + " » " + bcolors.OKGREEN + "Connected" + bcolors.ENDC)
print(bcolors.OKBLUE + "Lunar" + bcolors.ENDC + bcolors.UNDERLINE + " » " + bcolors.FAIL + "Failed" + bcolors.ENDC)
print("")
##Mapping stuff
version_map={}

mapping_urls={
    "1.7.10": {
        "map": "http://export.mcpbot.golde.org/mcp_stable/12-1.7.10/mcp_stable-12-1.7.10.zip",
        "srg": "http://export.mcpbot.golde.org/mcp/1.7.10/mcp-1.7.10-srg.zip"
    },
    "1.8.9": {
        "map": "http://export.mcpbot.golde.org/mcp_stable/22-1.8.9/mcp_stable-22-1.8.9.zip",
        "srg": "http://export.mcpbot.golde.org/mcp/1.8.9/mcp-1.8.9-srg.zip"
    },
    "1.12": {
        "map": "http://export.mcpbot.golde.org/mcp_stable/39-1.12/mcp_stable-39-1.12.zip",
        "srg": "http://export.mcpbot.golde.org/mcp/1.12/mcp-1.12-srg.zip"
    }
}

def makeDir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def downloadFile(url, file_name):
    print(f"Downloading {file_name} from {url}")
    response = requests.get(url, stream=True)
    with open(file_name, "wb") as handle:
        for data in tqdm(response.iter_content()):
            handle.write(data)

def loadAllMappings(path = "mappings"):
    global mapping_urls, version_map
    downloadMappings(path = path)
    for version in mapping_urls:
        current_path = path + "/" + version + "/"
        srg_method, srg_field = loadMappings(path = current_path, version = version)
        
        version_map[version] = {}
        version_map[version]["method"] = srg_method
        version_map[version]["field"] = srg_field
        if version=='1.8.9' or version=='1.7.10':
            print(bcolors.OKCYAN + f"{version}" + bcolors.ENDC + bcolors.UNDERLINE + " » " + bcolors.OKGREEN + "Connected" + bcolors.ENDC)
        else:
            print(bcolors.OKCYAN + "1.12.2" + bcolors.ENDC + bcolors.UNDERLINE + " » " + bcolors.OKGREEN + "Connected" + bcolors.ENDC)

def downloadMappings(path = "mappings"):
    global mapping_urls
    makeDir(path)
    for version in mapping_urls:
        current_path = path + "/" + version + "/"
        makeDir(current_path)
        
        map_file = current_path + "map.zip"
        srg_file = current_path + "srg.zip"
        
        if os.path.exists(current_path + "fields.csv") and os.path.exists(current_path + "methods.csv") and os.path.exists(current_path + "joined.srg"):
            continue
        
        downloadFile(mapping_urls[version]["map"], map_file)
        downloadFile(mapping_urls[version]["srg"], srg_file)
        
        with zipfile.ZipFile(map_file, 'r') as zip_ref:
            zip_ref.extract("fields.csv", current_path)
            print(f"Extracted {version} fields.csv")
            zip_ref.extract("methods.csv", current_path)
            print(f"Extracted {version} methods.csv")
        with zipfile.ZipFile(srg_file, 'r') as zip_ref:
            zip_ref.extract("joined.srg", current_path)
            print(f"Extracted {version} joined.srg")
        
        os.remove(map_file)
        os.remove(srg_file)
    
def saveMappingCache(srg_method, srg_field, fields_cache = "fields_cache.json", methods_cache = "methods_cache.json", path = ""):
    print("Saving fields cache...")
    with open(path + fields_cache, "w") as f:
        f.write(json.dumps(srg_field))
    print("Saving methods cache...")
    with open(path + methods_cache, "w") as f:
        f.write(json.dumps(srg_method))

def loadMappingCache(fields_cache = "fields_cache.json", methods_cache = "methods_cache.json", path = ""):
    srg_field = None
    srg_method = None
    
    if os.path.exists(path + fields_cache):
        with open(path + fields_cache, "r") as f:
            srg_field = json.loads(f.read())
    if os.path.exists(path + methods_cache):
        with open(path + methods_cache, "r") as f:
            srg_method = json.loads(f.read())
    
    return (srg_method, srg_field)

#This is TOO SLOW!
def parseSRG(file, fields_map, methods_map, parse_fields = True, parse_methods = True, version = ""):
    srg_method = {}
    srg_field = {}
    
    skipped_field = 0
    skipped_method = 0
    with open(file, "r") as f:
        for line in f:
            if parse_fields and line.startswith("FD: "):
                splited = line.split(" ")
                vanilla_obf = splited[1].rsplit("/", 1)
                forge_map = splited[2].rsplit("/", 1)
                
                #Just for better readability
                vanilla_class = vanilla_obf[0].rstrip()
                vanilla_field_name = vanilla_obf[1].rstrip()
                
                forge_class = forge_map[0].rstrip()
                forge_field_name = forge_map[1].rstrip()
                
                if forge_field_name.startswith("field_"):
                    csv_result = fields_map[fields_map["searge"] == forge_field_name]
                    if csv_result.empty:
                        skipped_field += 1
                        continue
                    
                    mcp_field_name = csv_result.values[0][1]#"name"
                else:
                    mcp_field_name = forge_field_name
                
                if version == "1.7.10":
                    NAME_CORRECTION = {
                        "yOffset2": "ySize",
                        "fontRendererObj": "fontRenderer"
                    }
                    
                    if mcp_field_name in NAME_CORRECTION:
                        mcp_field_name = NAME_CORRECTION[mcp_field_name]
                elif version == "1.12":
                    NAME_CORRECTION = {
                        "field_71466_p": "fontRendererObj",
                        "field_70123_F": "isCollidedHorizontally",
                        "field_70124_G": "isCollidedVertically",
                        "field_70132_H": "isCollided",
                        "field_72450_a": "xCoord",
                        "field_72448_b": "yCoord",
                        "field_72449_c": "zCoord",
                        "field_147707_d": "theShaderGroup",
                        "field_178183_a": "worldRenderer",
                        "field_76636_d": "isChunkLoaded",
                        "field_77864_a": "efficiencyOnProperMaterial",
                        "field_77865_bY": "damageVsEntity"
                    }
                    
                    if forge_field_name in NAME_CORRECTION:
                        mcp_field_name = NAME_CORRECTION[forge_field_name]
                
                forge_full_path = forge_class + "/" + mcp_field_name
                
                srg_field[forge_full_path] = {
                    "name": mcp_field_name,
                    "forge_name": forge_field_name,
                    "vanilla_name": vanilla_field_name,
                    "vanilla_class": vanilla_class
                }
            elif parse_methods and line.startswith("MD: "):
                splited = line.split(" ")
                vanilla_obf = splited[1].rsplit("/", 1)
                vanilla_params = splited[2].rstrip()
                
                forge_map = splited[3].rsplit("/", 1)
                forge_params = splited[4].rstrip()
                
                #Just for better readability 2
                vanilla_class = vanilla_obf[0].rstrip()
                vanilla_method_name = vanilla_obf[1].rstrip()
                
                forge_class = forge_map[0].rstrip()
                forge_method_name = forge_map[1].rstrip()
                
                csv_result = methods_map[methods_map["searge"] == forge_method_name]
                if csv_result.empty:
                    skipped_method += 1
                    continue
                
                mcp_method_name = csv_result.values[0][1]#"name"
                forge_full_path = forge_class + "/" + mcp_method_name
                                
                #Manual correction
                FORCE_METHOD_MATCH = {
                    "net/minecraft/util/BlockPos/down": "func_177977_b",
                    "net/minecraft/client/renderer/WorldRenderer/color": "func_181666_a",
                    "net/minecraft/entity/EntityLivingBase/isPotionActive": "func_70644_a",
                    "net/minecraft/world/World/markBlockRangeForRenderUpdate": "func_147458_c"
                }
                if version == "1.12":
                    FORCE_METHOD_MATCH["net/minecraft/world/World/getCollisionBoxes"] = "func_184144_a"
                    FORCE_METHOD_MATCH["net/minecraft/util/math/BlockPos"] = "func_177977_b"
                    FORCE_METHOD_MATCH["net/minecraft/client/renderer/BufferBuilder/color"] = "func_181666_a"
                
                if forge_full_path in FORCE_METHOD_MATCH and FORCE_METHOD_MATCH[forge_full_path] != forge_method_name:
                    skipped_method += 1
                    continue
                    
                if version == "1.7.10":
                    FORCE_SIGNATURE_MATCH = {
                        "net/minecraft/client/renderer/entity/RenderPlayer/doRender": "(Lnet/minecraft/client/entity/AbstractClientPlayer;DDDFF)V"
                    }
                    NAME_CORRECTION = {
                        "isCustomInventoryName": "hasCustomInventoryName",
                        "canStopRayTrace": "canCollideCheck",
                        "getMetadata": "getItemDamage",
                        "setMetadata": "setItemDamage",
                        "mouseReleased": "mouseMovedOrUp"
                    }
                    
                    if forge_full_path in FORCE_SIGNATURE_MATCH and FORCE_SIGNATURE_MATCH[forge_full_path] != forge_params:
                        skipped_method += 1
                        continue
                    
                    if mcp_method_name in NAME_CORRECTION:
                        mcp_method_name = NAME_CORRECTION[mcp_method_name]
                        forge_full_path = forge_class + "/" + mcp_method_name
                elif version == "1.12":
                    NAME_CORRECTION = {
                        "func_70032_d": "getDistanceToEntity",
                        "func_70082_c": "setAngles",
                        "func_92059_d": "getEntityItem",
                        "func_72964_e": "getChunkFromChunkCoords",
                        "func_175726_f": "getChunkFromBlockCoords",
                        "func_72441_c": "addVector",
                        "func_72314_b": "addCoord",
                        "func_72318_a": "isVecInside",
                        "func_72326_a": "intersectsWith",
                        "func_77977_a": "getUnlocalizedName",
                        "func_180664_k": "getBlockLayer",
                        "func_180634_a": "onEntityCollidedWithBlock",
                        "func_110623_a": "getResourcePath",
                        "func_150931_i": "getDamageVsEntity"
                    }
                    
                    if forge_method_name in NAME_CORRECTION:
                        mcp_field_name = NAME_CORRECTION[forge_method_name]
                        forge_full_path = forge_class + "/" + mcp_method_name
                #
                
                srg_method[forge_full_path] = {
                    "name": mcp_method_name,
                    "forge_name": forge_method_name,
                    "forge_params": forge_params,
                    "vanilla_name": vanilla_method_name,
                    "vanilla_params": vanilla_params,
                    "vanilla_class": vanilla_class
                }
    print(f"Skipped {skipped_field} fields and {skipped_method} methods")
    return (srg_method, srg_field)
                
def loadMappings(fields_csv = "fields.csv", methods_csv = "methods.csv", joined_srg = "joined.srg", path = "", version = ""):
    fields_map = None
    methods_map = None
    srg_method, srg_field = loadMappingCache(path = path)
    
    load_methods=False
    load_fields=False
    if srg_method == None or len(srg_method) == 0:
        print("Unable to load cached methods")
        load_methods = True
        
    if srg_field == None or len(srg_field) == 0:
        print("Unable to load cached fields")
        load_fields = True
    
    if load_fields:
        fields_map = pd.read_csv(path + fields_csv) 
        print(f"Loaded {path + fields_csv}")
    if load_methods:
        methods_map = pd.read_csv(path + methods_csv)
        print(f"Loaded {path + methods_csv}")
    
    if load_fields or load_methods:
        print("Parsing SRG ... (This can take some time. But don\'t worry this is done only once per version!)")
        srg_method, srg_field = parseSRG(path + joined_srg, fields_map, methods_map, load_fields, load_methods, version)
        print(f"Loaded {path + joined_srg}")
        saveMappingCache(srg_method, srg_field, path = path)
    
    return srg_method, srg_field
##

ASSET_LIST = {
    "circle2": "bcf707a0e4cfb8f7bf2d674231e3f75ec1e3639ebe963f679eb134ff25887cd5",
    "di_target": "c3686a196e62f5760695bcff6943d53895e6644e52a53acd1f58fab5d465adc5",
    "duel info": "31d5f4778af17e0d75ba7322ce4173dc45fc99c4d0f9b5fad9d89b67a8461936",
    "settings": "b7bb7fd763e2725c43aef027abb91dd757444265599eab33bd2ceac72c4858ca",
    "dots": "d0a4e01a291f327c77688376cf56147ab1de864bcfcbf3cb2de813d2a00895e4",
    "import": "6938de58f81af17bab49e9da5b410a7f8de2d8dad03191d315e967398bc9d2a6",
    "peace": "d0c010b5028a550079f9958d7a12eed8074155dcf4cfddc942a2545b3f1e261a",
    "favorite": "108d5a643d7ed7827224d71144761df77cc66f6e6875cc8e685e492e895012db",
    "utility": "2bb27052316e8db9a6b50c12a1990a3466670261d7856e9d6cf92cadaf1acb0f",
    "toggleback": "675ec7214adb0db0bb783fd875e3320284a5b3e7e82865d01313e9236b841ace",
    "toggleback2": "e1726408b195b1f7158a1dfadcaed415bc4a18ec60e96ce1d47460c1f5952293",
    "ex": "ed598122f2fceefeed5dbe2357ddf49c325ac4cb8e044edb2cf17accb4ffa665",
    "di_pot": "8b23b5f61f79c15fb379be0b202b486f0c59a2cfebe2eb9468f7fa3618aa7a2e",
    "togglefront": "f1fc2b10fbd117275240697e8847e0bda8fb089dab66cb971ac782bef553494e",
    "text gui": "59e14f49d31550145cd758e36cdd1154c217f0a4badb62515229210c9160ba40",
    "creeper": "99f1518b6d74b3c191a6fa3282585e220d5022c608cac4512b840fcfd694a5ba",
    "delete": "da3957946ea980de5d7aeebed7e1649ecd77ad229a54b230595c1f99d85e10d6",
    "check": "25b197a324870c001261ef2b12ef52b4014e01b23e7c500277a43dee8f00555b",
    "render": "e22933b47ee4b1c4b3609f384e5f154534eb684fce430421cfa03f927002f120",
    "download": "d35544d765b61d4585b1f1b19232a2df4a6c30ba0c87ccef93dc6c62a77d98e2",
    "world": "f97d9cfe66e06a47fb7432fe148b01cd230b5bd255e062ecf5ab8ec12b5ee311",
    "other": "2c82463597d503c87cede3b7061ebc29589a85767848047e6c63dc2a95481761",
    "sync": "293fde987eb63f4c39d70efa0740ca8087302356c60119a6055d41971e440ec0",
    "circle": "113acf8dfe24448284d74da9c731632af084cb12ed15b2b74d98aecbcd8bf57e",
    "di_hit": "1582f9bcdd9b43e40c6ae9f13f39bf48f752deca684e3dd72a7164f70dd9aa49",
    "info": "e36b3edb0bba8492280646adc1e17bcdf10b91c0645eb87fbd9cbaf59246af24",
    "blatant": "f72ab642ede4ef6a7f1152197beb1ad9842929bb1f18882b7673f5c691a2758c",
    "v4": "4744da398abde37aa83a9cde867ba38113a7679595c7f880814703f3fcf30ab1",
    "copy": "88422534bd97919412e4e0e09f54e181cec378bbda004c6847e25c5d5bf2bdd6",
    "friends": "8242e7ee68a7f7e5d34386b5dc979b5d8e1d88ff8bf25840f6a2ffea8e829006",
    "cross": "3c4eb0e2797645333838c55d7fc8ead47cfb5ffacd579bf5a59e4d441315e323",
    "vapelogo": "e59b3fcb5e6d4a069d06f2a6c9c5b58cd00e106ceb0f1ea5ce2b89ee70f6c497",
    "macros": "e396e2bd3ef8ff13b2ba9431b7957549a3453241ecd8e3ad97e44f5e28c71ed2",
    "target info": "052866360adb6b90970eed7ce8a4551d98a3538ff3b176980e5f8efd3cbc107a",
    "icon4": "46812a97eade3bd8fd5de6840d175ff954e2e08956de525e9d02f9adf2381fcd",
    "exo": "5a62d706b159c1f3cd29425f6280c26937e8e38f1cc6094d791aa8c06911ce71",
    "gui": "32e40a636dd76c7b745375985430e9e089e623c567ce5f6b57e1f7b3916472e3",
    "user": "e68b1e29e6e0670cced111b07afb253ae14e297b291e5e2aa9068f9c563feacf",
    "export": "c20f514c52d97aa5b60c54fb18ec30fb6456ee2f2a653f7d964ec33c5e7676f0",
    "upload": "7dc7ff0ff8b68aa4f550e5a0b7f9183d2d439b0ecbb8cdebc47abf6607d6d2d1",
    "radar": "dab5efdc30a28d129def7c1a1d869d7871a5c1df6a84612a3003c2b7f35e693d",
    "vapelogosmall": "0ea2da5d53629e15d7c0a6e372b8ba4482e82d5220a86fe5338c1a5cdd6e2506",
    "profiles": "4d019acc7a5c31c4bb3b23ea78ff5838beabc3ffd8635347a32f51f665f31d6d",
    "search": "86a4ec5dfb45efea48006d621e87a38e1f8e8d239f08221b67eb811dcef19a2a",
    "magnify": "b68aa467047e7936f7459cf8a955fea5acbc2d9e3dfa7c35aa8a0de6fe0ed412",
    "pin": "872ae634a5712ca7ccc479c45333738a836735e22e4252c17571b38b4912a6b0",
    "rearview": "396322a81e8c15555adf3f709c353ddec0d77de6a485093ccdd28bf987fa9382",
    "fire": "3c2cf0c986787ab10d9f5259cbdd345bba07a07360a039b494fae54e3be52883",
    "combat": "8a5aa93b6575a7e221873149f4a252888ea411c3e4f7a2f6d4d6d763b7164951"
}

DUMP0_HASH = "610e11480fa719e99349c2f1cc1c341d7536410126ff98ba1d818afa710c5354"
DUMP1_HASH = "5ec35d530ddd0270a4f5724f37b49af671ae72f960ff62dc4e60f555657aa07b"
DUMP2_HASH = "59a95e9499f9c6cd54ec4cdc283d1638a11c3f68d23c689407b0c2f04c66ec7f"
STRINGS_HASH = "0d9131680c83e1602759d234b9ac86e4dd15707b6332a5232d08642302836e6f"

def HashString(string):
    return hashlib.sha256(string.encode("ascii")).hexdigest()
    

def FileHash(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        data = f.read()
        sha256.update(data)
    return sha256.hexdigest()

def SingleFileIntegrity(file_path, expected_hash):
    if not os.path.exists(file_path):
        print(f"{file_path} not found! Please redownload or redump it.")
        exit(1)
    
    file_hash = FileHash(file_path)
    if file_hash != expected_hash:
        print(f"Invalid file hash {file_path} !\nGot : {file_hash}\nExpected : {expected_hash}")
        exit(1)

def FileIntegrityCheck(assets_folder = "assets"):
    global ASSET_LIST
    for file in ASSET_LIST:
        asset_path = assets_folder + "/" + file + ".png"
        SingleFileIntegrity(asset_path, ASSET_LIST[file])
    
    SingleFileIntegrity("Dump0", DUMP0_HASH)
    SingleFileIntegrity("Dump1", DUMP1_HASH)
    SingleFileIntegrity("Dump2", DUMP2_HASH)
    SingleFileIntegrity("strings.txt", STRINGS_HASH)

#https://stackoverflow.com/questions/27164354/create-a-self-signed-x509-certificate-in-python
def GenerateSSL(cert_file = "cert.pem", key_file = "key.pem"):
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)

    cert = crypto.X509()
    cert.get_subject().C = "FR"
    cert.get_subject().O = "Vape Offline Server by Andro24"
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1337)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)#~10 years
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, "sha1")
    with open(cert_file, "wt") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))
    with open(key_file, "wt") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode("utf-8"))
    print("Generated self signed SSL cert and key!")

##The actual server starts here:
async def xor_string(text: bytes, key: int) -> bytes:
    return bytes([b ^ key for b in text])

async def saveSettings(ip, settings, path):
    makeDir(path)
    with open(path + "/" + HashString(ip) + ".json", "w") as f:
        f.write(settings)

async def loadSettings(ip, path):
    settings_file_path = path + "/" + HashString(ip) + ".json"
    if not os.path.exists(settings_file_path):
        print(f"{ip} : No settings found for this ip.")
        return "{}"
    with open(settings_file_path, "r") as f:
        return f.read()

FILE_BUFFER_SIZE=1000
async def send_file(websocket, file, xor_key):
    global FILE_BUFFER_SIZE
    ip = websocket.remote_address[0];
    print(f"{ip} : Sending {file}...")
    with open(file, "rb") as f:
        f.seek(0, os.SEEK_END)
        fileSize = f.tell()
        f.seek(0, os.SEEK_SET)
        
        await websocket.send(str(fileSize))
        
        buffer = f.read(FILE_BUFFER_SIZE)
        while buffer:
            await websocket.send(await xor_string(buffer, xor_key))
            buffer = f.read(FILE_BUFFER_SIZE)
        print(f"{ip} : Sent {file} ({fileSize}) !")

async def send_assets(websocket, xor_key, assets_folder = "assets"):
    global ASSET_LIST
    ip = websocket.remote_address[0];
    
    await websocket.send(str(len(ASSET_LIST)))
    for file in ASSET_LIST:
        await websocket.send(await xor_string(file.encode("ascii"), xor_key))
        with open(assets_folder + "/" + file + ".png", "rb") as f:
            await websocket.send(await xor_string(f.read(), xor_key))
            print(f"{ip} : Sent {file} !")
    print(f"{ip} : Sent {len(ASSET_LIST)} assets !")

async def send_strings(websocket, xor_key, strings_file = "strings.txt"):
    ip = websocket.remote_address[0];
    
    strings = []
    with open(strings_file, "rb") as f:
        strings = f.read().split(b"\000")
    strings = strings[:-1]#Remove the last empty string due to the split
    
    await websocket.send(str(len(strings)))
    
    for string in strings:
        await websocket.send(await xor_string(base64.b64encode(string), xor_key))
    print(f"{ip} : Sent {len(strings)} strings !")

async def handle_client(websocket, path):
    global version_map
    
    MAGIC = ""
    MAGIC_V4="ab33cdea3e72c957eb44677e44b98909"
    MAGIC_LITE="7f14cd4b5e3e73833e333635c7f17a1b"
    
    ip = websocket.remote_address[0];
    print(f"New client from {ip} !")
    
    xor_key = 0
    client_mc_version = ""
    vape_version = ""
    settings_path = "settings/"
    
    srg_method = None
    srg_field = None
    
    while True:
        try:
            recvdata = await websocket.recv()
            recvdata = recvdata.split("\n")
            
            packet_id = int(recvdata[0])
            
            ##Handle Packets
            
            #Hello
            if packet_id == 3 and len(recvdata) >= 3:
                if recvdata[2] != "V4" and recvdata[2] != "lite":
                    print(f"{ip} : [Hello] Invalid version : {recvdata[2]}")
                    return
                print(f"{ip} : [Hello] Version : {recvdata[2]}")
                vape_version = recvdata[2]
                if vape_version == "V4":
                    MAGIC = MAGIC_V4
                    settings_path += "v4"
                elif vape_version == "lite":
                    MAGIC = MAGIC_LITE
                    settings_path += "lite"
                
                await websocket.send("ok")
            #XorKey
            elif packet_id == 12 and len(recvdata) >= 2:
                print(f"{ip} : [XorKey] Key : {recvdata[1]}")
                xor_key = int(recvdata[1])
            #HashReq
            elif packet_id == 2:
                print(f"{ip} : [HashReq]")
                await websocket.send(await xor_string(MAGIC.encode("ascii"), xor_key))
            #UNK1
            elif packet_id == 27 and len(recvdata) >= 4:
                print(f"{ip} : [UNK1] {recvdata[1]} {recvdata[2]} {recvdata[3]}")
                await websocket.send("0")
            #FileReq1
            elif packet_id == 47 and len(recvdata) >= 2:
                if recvdata[1] != "2" and recvdata[1] != "5":
                    print(f"{ip} : [FileReq1] Invalid file number : {recvdata[1]}")
                    return
                print(f"{ip} : [FileReq1] {recvdata[1]}")
                
                if recvdata[1] == "2":
                    await send_file(websocket, "Dump0", xor_key)
                elif recvdata[1] == "5":
                    await send_file(websocket, "Dump2", xor_key)
            #MCVersion
            elif packet_id == 10 and len(recvdata) >= 2:
                if not recvdata[1] in version_map:
                    print(f"{ip} : [MCVersion] Invalid version : {recvdata[1]}")
                    return
                
                print(f"{ip} : [MCVersion] Version : {recvdata[1]}")
                client_mc_version = recvdata[1]
                await websocket.send("0")
                
                srg_method = version_map[client_mc_version]["method"]
                srg_field = version_map[client_mc_version]["field"]
            #FileReq2
            elif packet_id == 53:
                print(f"{ip} : [FileReq2]")
                await send_file(websocket, "Dump1", xor_key)
            #FieldMap
            elif packet_id == 8 and len(recvdata) >= 3:
                if srg_field == None:
                    print(f"{ip} : [FieldMap] Unknown version !")
                    return
                
                class_name = (await xor_string(recvdata[1].encode("ascii"), xor_key)).decode("ascii")
                field_name = (await xor_string(recvdata[2].encode("ascii"), xor_key)).decode("ascii")
                full_path = class_name + "/" + field_name

                if full_path in srg_field:
                    print(f"{ip} : [FieldMap] Field : {full_path}")
                    await websocket.send(await xor_string(srg_field[full_path]["forge_name"].encode("ascii"), xor_key))
                else:
                    print(f"{ip} : [FieldMap] Unknown field : {full_path}")
                    await websocket.send(await xor_string(field_name.encode("ascii"), xor_key))
            #MethodMap
            elif packet_id == 9 and len(recvdata) >= 3:
                if srg_method == None:
                    print(f"{ip} : [MethodMap] Unknown version !")
                    return
            
                class_name = (await xor_string(recvdata[1].encode("ascii"), xor_key)).decode("ascii")
                method_name = (await xor_string(recvdata[2].encode("ascii"), xor_key)).decode("ascii")
                full_path = class_name + "/" + method_name
                if full_path in srg_method:
                    print(f"{ip} : [MethodMap] Method : {full_path}")
                    await websocket.send(await xor_string((srg_method[full_path]["forge_name"] + ":" + srg_method[full_path]["forge_params"]).encode("ascii"), xor_key))
                else:
                    print(f"{ip} : [MethodMap] Unknown method : {full_path}")
                    await websocket.send(await xor_string(method_name.encode("ascii"), xor_key))
            #LoadSettings
            elif packet_id == 51:
                print(f"{ip} : [LoadSettings] Sending settings ({settings_path})")
                settings = base64.b64encode((await loadSettings(ip, settings_path)).encode("ascii"))
                await websocket.send(settings)
            #AssetsReq
            elif packet_id == 55:
                print(f"{ip} : [AssetsReq]")
                await send_assets(websocket, xor_key)
            #StringsReq
            elif packet_id == 54:
                print(f"{ip} : [StringsReq]")
                await send_strings(websocket, xor_key)
            #ClientInfo (Vape V4)
            elif packet_id == 56 and len(recvdata) >= 6:
                IGN = (await xor_string(recvdata[1].encode("ascii"), xor_key)).decode("ascii")
                PCUsername = (await xor_string(recvdata[2].encode("ascii"), xor_key)).decode("ascii")
                MACAddress = (await xor_string(recvdata[3].encode("ascii"), xor_key)).decode("ascii")
                UNK1 = (await xor_string(recvdata[4].encode("ascii"), xor_key)).decode("ascii")
                UNK2 = (await xor_string(recvdata[5].encode("ascii"), xor_key)).decode("ascii")
                print(f"{ip} : [ClientInfo V4] IGN : {IGN} PC Username : {PCUsername} MAC Address : {MACAddress} UNK1 : {UNK1} UNK2 : {UNK2}")
            #Hello2 (V4)
            elif packet_id == 4 and len(recvdata) >= 4:
                if recvdata[1] != MAGIC_V4 or recvdata[3] != "V4":
                    print(f"{ip} : [Hello2] Invalid. MAGIC : {recvdata[1]} Version : {recvdata[3]}")
                    return
                print(f"{ip} : [Hello2] Version : {recvdata[3]}")
                settings_path += "v4"
                await websocket.send("ok")
            #ProfileReq
            elif packet_id == 52 and len(recvdata) >= 2:
                request = (await xor_string(recvdata[1].encode("ascii"), xor_key)).decode("ascii")
                print(f"{ip} : [ProfileReq] Request : {request}")
                if vape_version == "V4":
                    await websocket.send(await xor_string(MAGIC.encode("ascii"), xor_key))
                elif vape_version == "lite":
                    await websocket.send("e30=")# "{}" in b64
            #SyncSettings
            elif packet_id == 50 and len(recvdata) >= 2:
                settings = base64.b64decode(recvdata[1].encode("ascii")).decode("ascii")
                await saveSettings(ip, settings, settings_path)
                print(f"{ip} : [SyncSettings] Downloaded settings ({settings_path})")
            #UNK3 Only Vape Lite
            elif packet_id == 48 and len(recvdata) >= 2:
                print(f"{ip} : [UNK3] {recvdata[1]}")
                await websocket.send(await xor_string("44".encode("ascii"), xor_key))
            #IGN Only Vape Lite
            elif packet_id == 21 and len(recvdata) >= 2:
                IGN = (await xor_string(recvdata[1].encode("ascii"), xor_key)).decode("ascii")
                print(f"{ip} : [IGN] {IGN}")
            #ClientInfo (Vape Lite)
            elif packet_id == 49 and len(recvdata) >= 5:
                PCUsername = (await xor_string(recvdata[1].encode("ascii"), xor_key)).decode("ascii")
                MACAddress = (await xor_string(recvdata[2].encode("ascii"), xor_key)).decode("ascii")
                UNK1 = (await xor_string(recvdata[3].encode("ascii"), xor_key)).decode("ascii")
                UNK2 = (await xor_string(recvdata[4].encode("ascii"), xor_key)).decode("ascii")
                
                print(f"{ip} : [ClientInfo Lite] PC Username : {PCUsername} MAC Address : {MACAddress} UNK1 : {UNK1} UNK2 : {UNK2}")
            #Hello3 (Lite)
            elif packet_id == 1 and len(recvdata) >= 4:
                if recvdata[1] != MAGIC_LITE:
                    print(f"{ip} : [Hello3] Invalid. MAGIC : {recvdata[1]}")
                    return
                print(f"{ip} : [Hello3]")
                settings_path += "lite"
                await websocket.send("ok")
            else:
                print(f"{ip} : Unknown packet. ID : {packet_id}")

        except websockets.exceptions.ConnectionClosedError as e:
            if e.code == 1005:
                print(f"{ip} : Connection closed.")
            else:
                print(e)
            break

def main():
    loadAllMappings()
    FileIntegrityCheck()

    SSL_CERT_FILE = "cert.pem"
    SSL_KEY_FILE = "key.pem"

    if not os.path.exists(SSL_CERT_FILE) or not os.path.exists(SSL_KEY_FILE):
        GenerateSSL(SSL_CERT_FILE, SSL_KEY_FILE)

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert_file = pathlib.Path(__file__).with_name(SSL_CERT_FILE)
    key_file = pathlib.Path(__file__).with_name(SSL_KEY_FILE)
    ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)

    start_server = websockets.serve(
        handle_client, SERVER_IP, SERVER_PORT, ssl=ssl_context
    )
    
    print("")
    print("┏━━━━━━━━━━━━━━━━━━━━━━━┓")
    print(f"┃    {SERVER_IP}:{SERVER_PORT}     ┃")
    print("┗━━━━━━━━━━━━━━━━━━━━━━━┛")

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()