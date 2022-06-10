#define WIN32_LEAN_AND_MEAN
#define _CRT_SECURE_NO_WARNINGS
#include <Windows.h>
#include <winsock2.h>
#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <iomanip>
#include <mutex>
#include "MinHook.h"

#include "PacketHandler.h"

#pragma comment(lib, "Ws2_32.lib")

DWORD64 base_address = 0;

typedef void* (*Connection)(void*, void*, std::string*, void*);
Connection original_connection = NULL;

void* connection_hook(void* arg1, void* arg2, std::string* addr, void* arg4)
{
	//*addr = "ws://vape.sexy:8080";
	*addr = "ws://localhost:8765";
	return original_connection(arg1, arg2, addr, arg4);
}

std::mutex log_mutex;
void Log(std::string str) {
	log_mutex.lock();
	std::ofstream logfile("vapev4.log", std::ios::app | std::ios::binary);
	if (logfile.is_open()) {
		logfile << str << std::endl;
		logfile.close();
	}
	log_mutex.unlock();
}

using send_type = int(WSAAPI*)(SOCKET, const char*, int, int);
using recv_type = int(WSAAPI*)(SOCKET, char*, int, int);

using WSASend_type = int (WSAAPI*)(SOCKET, LPWSABUF, DWORD, LPDWORD, DWORD, LPWSAOVERLAPPED, LPWSAOVERLAPPED_COMPLETION_ROUTINE);
using WSARecv_type = int (WSAAPI*)(SOCKET, LPWSABUF, DWORD, LPDWORD, LPDWORD, LPWSAOVERLAPPED, LPWSAOVERLAPPED_COMPLETION_ROUTINE);

send_type o_send = NULL;
recv_type o_recv = NULL;
WSASend_type o_WSASend = NULL;
WSARecv_type o_WSARecv = NULL;

std::string byteToHex(const char* bytes, size_t len) {
	std::ostringstream out;
	for (size_t i = 0; i < len; i++) {
		out << std::hex << std::setfill('0') << std::setw(2) << (uint32_t)(uint8_t)(bytes[i]);
	}
	return out.str();
}

std::atomic_uint64_t class_counter = 0;
const bool dumpClass = false;

int WSAAPI send_hook(SOCKET s, const char* buf, int len, int flags) {
	std::cout << "[" << s << "] send() len : " << len << std::endl;
	std::string buf_str;
	buf_str.resize(len);
	memcpy_s(&buf_str[0], len, buf, len);
	
	bool isClass = false;
	auto first_nl = buf_str.find_first_of('\n');
	if (first_nl != std::string::npos) {
		size_t buf_size = atoll(buf_str.substr(0, first_nl).c_str());//Get the buffer size in ascii
		buf_str = buf_str.substr(first_nl + 1);//Strip the buffer size & the new line
		if (buf_str.substr(0, 4) == "\xCa\xFE\xBA\xBE") {//Check if it's a class with the magic number
			isClass = true;
			if (dumpClass) {
				std::ofstream class_file("dump" + std::to_string(class_counter) + ".class", std::ios::binary);
				if (class_file.is_open()) {
					class_file.write(&buf_str[0], buf_str.size());//DUMP!
					class_file.close();
					class_counter++;
				}
			}
		}
	}
	if (!isClass)
		Log("send() [" + std::to_string(s) + "] : " + byteToHex(buf, len));
	return o_send(s, buf, len, flags);
}

int WSAAPI recv_hook(SOCKET s, char* buf, int len, int flags) {
	int ret = o_recv(s, buf, len, flags);
	std::cout << "[" << s << "] recv() len : " << len << std::endl;
	Log("recv() [" + std::to_string(s) + "] : " + byteToHex(buf, len));
	return ret;
}

int WSAAPI WSASend_hook(SOCKET s, LPWSABUF lpBuffers, DWORD dwBufferCount, LPDWORD lpNumberOfBytesSent, DWORD dwFlags, LPWSAOVERLAPPED lpOverlapped, LPWSAOVERLAPPED_COMPLETION_ROUTINE lpCompletionRoutine) {
	WSABUF wsabuf = *lpBuffers;
	std::cout << "[" << s << "] WSASend() len : " << wsabuf.len << std::endl;
	Log("WSASend() [" + std::to_string(s) + "] : " + byteToHex(wsabuf.buf, wsabuf.len));
	return o_WSASend(s, lpBuffers, dwBufferCount, lpNumberOfBytesSent, dwFlags, lpOverlapped, lpCompletionRoutine);
}

int WSAAPI WSARecv_hook(SOCKET s, LPWSABUF lpBuffers, DWORD dwBufferCount, LPDWORD lpNumberOfBytesRecvd, LPDWORD lpFlags, LPWSAOVERLAPPED lpOverlapped, LPWSAOVERLAPPED_COMPLETION_ROUTINE lpCompletionRoutine) {
	Log("WSARecv() [" + std::to_string(s) + "] Enter");
	int ret = o_WSARecv(s, lpBuffers, dwBufferCount, lpNumberOfBytesRecvd, lpFlags, lpOverlapped, lpCompletionRoutine);
	WSABUF wsabuf = *lpBuffers;
	Log("WSARecv() [" + std::to_string(s) + "] : " + byteToHex(wsabuf.buf, wsabuf.len));
	return ret;
}

typedef BOOL(*AC)(void);
AC original_allocconsole = NULL;
AC original_freeconsole = NULL;

using write_push_type = __int64(__fastcall*)(__int64, __int64);
write_push_type original_write_push;

using connection_send_type = char* (__fastcall*)(__int64, char*, __int64);
connection_send_type original_connection_send;

using on_message_type = __int64(__fastcall*)(__int64, __int64);
on_message_type original_on_message;

using std_string_c_str_type = __int64(__fastcall*)(__int64);
std_string_c_str_type std_string_c_str;

using std_string_size_type = __int64(__fastcall*)(__int64);
std_string_size_type std_string_size;

using string_crypto_type = __int64(__fastcall*)(__int64, __int64);
string_crypto_type original_string_crypto;

using std_string_alloc = __int64(__fastcall*)(__int64, __int64, unsigned __int64);
std_string_alloc original_std_string_alloc;

uint64_t getStringSize(PVOID str_ptr) {
	return static_cast<uint64_t>(std_string_size(reinterpret_cast<__int64>(str_ptr)));
}

std::string getString(PVOID str_ptr) {
	return std::string(
		reinterpret_cast<const char*>(std_string_c_str(reinterpret_cast<__int64>(str_ptr))),
		getStringSize(str_ptr)//Don't stop at null bytes!
	);
}

std::string getMessagePayload(PVOID* message_ptr) {
	return getString(reinterpret_cast<PVOID>(reinterpret_cast<DWORD64>(*message_ptr) + 0x50));
}

//Kinda useless, gives the encrypted message
//https://github.com/zaphoyd/websocketpp/blob/1b11fd301531e6df35a6107c1e8665b1e77a2d8e/websocketpp/impl/connection_impl.hpp#L2210
__int64 __fastcall write_push_hook(__int64 a1, __int64 msg) {
	Log("write_push_hook");

	return original_write_push(a1, msg);
}

PacketHandler packetHandler;

//https://github.com/zaphoyd/websocketpp/blob/1b11fd301531e6df35a6107c1e8665b1e77a2d8e/websocketpp/impl/connection_impl.hpp#L104
char* __fastcall connection_send_hook(__int64 a1, char* a2, __int64 msg) {
	std::string payload = getMessagePayload(reinterpret_cast<PVOID*>(msg));
	packetHandler.handleSend(payload);
	//Log("SEND:\n" + byteToHex(payload.c_str(), payload.length()));
	return original_connection_send(a1, a2, msg);
}

//https://github.com/zaphoyd/websocketpp/blob/1b11fd301531e6df35a6107c1e8665b1e77a2d8e/websocketpp/endpoint.hpp#L322
//Endpoint message handler
__int64 __fastcall on_message_hook(__int64 connection_hdl, __int64 msg) {
	std::string payload = getMessagePayload(reinterpret_cast<PVOID*>(msg));
	packetHandler.handleRecv(payload);
	//Log("RECV:\n" + byteToHex(payload.c_str(), payload.length()));
	return original_on_message(connection_hdl, msg);
}

__int64 __fastcall string_crypto_hook(__int64 a1, __int64 a2) {
	Log("string_crypto_hook PRE :\n" + getString(reinterpret_cast<PVOID>(a2)));
	__int64 ret = original_string_crypto(a1, a2);
	Log("string_crypto_hook POST :\n" + getString(reinterpret_cast<PVOID>(a2)));
	return ret;
}

__int64 __fastcall std_string_alloc_hook(__int64 a1, __int64 str, unsigned __int64 len) {
	FILE* f = fopen("vapev4.log", "a");//Avoid calling the string constructor (infinite loop)
	if (f != nullptr) {
		fprintf(f, "%s\n", reinterpret_cast<const char*>(str));
		fclose(f);
	}
	return original_std_string_alloc(a1, str, len);
}

std::string ptrToStr(void* ptr) {
	std::ostringstream ss;
	ss << ptr;
	return ss.str();
}

std::streambuf* CinBuffer, * CoutBuffer, * CerrBuffer;
std::fstream ConsoleInput, ConsoleOutput, ConsoleError;

void RedirectIO()
{
	CinBuffer = std::cin.rdbuf();
	CoutBuffer = std::cout.rdbuf();
	CerrBuffer = std::cerr.rdbuf();
	ConsoleInput.open("CONIN$", std::ios::in);
	ConsoleOutput.open("CONOUT$", std::ios::out);
	ConsoleError.open("CONOUT$", std::ios::out);
	std::cin.rdbuf(ConsoleInput.rdbuf());
	std::cout.rdbuf(ConsoleOutput.rdbuf());
	std::cerr.rdbuf(ConsoleError.rdbuf());
}

BOOL allocconsole_hook()
{
	base_address = reinterpret_cast<DWORD64>(GetModuleHandleA("Vape_V4.exe"));

	MH_Initialize();

	std_string_c_str = (std_string_c_str_type)reinterpret_cast<LPVOID>((base_address + 0x17e70ULL));
	std_string_size = (std_string_size_type)reinterpret_cast<LPVOID>((base_address + 0x16780ULL));

	Connection real_connection = (Connection)reinterpret_cast<LPVOID>((base_address + 0x89c80));
	MH_CreateHook(real_connection, &connection_hook, (void**)&original_connection);
	MH_EnableHook(real_connection);

	//LPVOID write_push_addr = (LPVOID)(base_address + 0xf1550ULL);
	//MH_CreateHook(write_push_addr, &write_push_hook, (void**)&original_write_push);
	//MH_EnableHook(write_push_addr);
	//Log("Hooked write_push " + ptrToStr(write_push_addr));

//#define HOOKK
#ifdef HOOKK
	LPVOID connection_send_addr = (LPVOID)(base_address + 0xdc690ULL);
	MH_CreateHook(connection_send_addr, &connection_send_hook, (void**)&original_connection_send);
	MH_EnableHook(connection_send_addr);
	Log("Hooked connection_send " + ptrToStr(connection_send_addr));

	LPVOID on_message_addr = (LPVOID)(base_address + 0x86d20ULL);
	MH_CreateHook(on_message_addr, &on_message_hook, (void**)&original_on_message);
	MH_EnableHook(on_message_addr);
	Log("Hooked on_message " + ptrToStr(on_message_addr));
#endif

	//LPVOID std_string_alloc = (LPVOID)(base_address + 0x178a0ULL);
	//MH_CreateHook(std_string_alloc, &std_string_alloc_hook, (void**)&original_std_string_alloc);
	//MH_EnableHook(std_string_alloc);
	//Log("Hooked std_string_alloc " + ptrToStr(std_string_alloc));

	//Not crypto :/
	//LPVOID string_crypto_addr = (LPVOID)(base_address + 0x89630ULL);
	//MH_CreateHook(string_crypto_addr, &string_crypto_hook, (void**)&original_string_crypto);
	//MH_EnableHook(string_crypto_addr);
	//Log("Hooked string_crypto " + ptrToStr(string_crypto_addr));

	MH_DisableHook(&AllocConsole);

	BOOL ret = original_allocconsole();

	//HMODULE ws2_32 = LoadLibraryA("ws2_32.dll");

	//FARPROC send_addr = GetProcAddress(ws2_32, "send");
	//FARPROC recv_addr = GetProcAddress(ws2_32, "recv");
	//FARPROC WSASend_addr = GetProcAddress(ws2_32, "WSASend");
	//FARPROC WSARecv_addr = GetProcAddress(ws2_32, "WSARecv");

	//MH_CreateHook(send_addr, &send_hook, (void**)&o_send);
	//MH_EnableHook(send_addr);
	//Log("Hooked send() " + ptrToStr(send_addr));
	//MH_CreateHook(recv_addr, &recv_hook, (void**)&o_recv);
	//MH_EnableHook(recv_addr);
	//Log("Hooked recv() " + ptrToStr(recv_addr));
	//MH_CreateHook(WSASend_addr, &WSASend_hook, (void**)&o_WSASend);
	//MH_EnableHook(WSASend_addr);
	//Log("Hooked WSASend() " + ptrToStr(WSASend_addr));
	//MH_CreateHook(WSARecv_addr, &WSARecv_hook, (void**)&o_WSARecv);
	//MH_EnableHook(WSARecv_addr);
	//Log("Hooked WSARecv() " + ptrToStr(WSARecv_addr));

	//RedirectIO();

	return ret;
}

using ShowWindow_Type = BOOL(WINAPI*)(HWND, int);
ShowWindow_Type original_ShowWindow;

//Don't hide the console! (debug)
BOOL ShowWindow_hook(HWND hWnd,int nCmdShow) {
	HWND console = GetConsoleWindow();
	if (hWnd == console)
		return original_ShowWindow(hWnd, SW_SHOW);
	return original_ShowWindow(hWnd, nCmdShow);
}

BOOL freeconsole_hook() {
	//Don't close the console (debug)
	return TRUE;
}

BOOL WINAPI DllMain(HMODULE module, DWORD call_reason, LPVOID reserved) {
	if (call_reason == DLL_PROCESS_ATTACH) {
		if (!GetModuleHandleA("kernel32.dll")) LoadLibraryA("kernel32.dll");

		MH_Initialize();
		MH_CreateHook(&AllocConsole, &allocconsole_hook, (void**)&original_allocconsole);
		MH_EnableHook(&AllocConsole);
		/*MH_CreateHook(&FreeConsole, &freeconsole_hook, (void**)&original_freeconsole);
		MH_EnableHook(&FreeConsole);*/
		//MH_CreateHook(&ShowWindow, &ShowWindow_hook, (void**)&original_ShowWindow);
		//MH_EnableHook(&ShowWindow);
	}
	return TRUE;
}