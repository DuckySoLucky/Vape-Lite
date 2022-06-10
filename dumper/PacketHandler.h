#pragma once
#include <iostream>
#include <vector>
#include <deque>
#include <string>
#include <sstream>
#include <fstream>
#include <mutex>

#include "base64.h"

constexpr auto LOG_FILENAME = "vapev4.log";

enum class ExpectedReply {
    OK,
    MAGIC,
    ZERO,
    FILE,
    ASSETS,
    MAPPING,
    UNK1,
    STRINGS,
};

class PacketHandler {
public:
    PacketHandler() {
        m_logFile = std::make_unique<std::ofstream>(LOG_FILENAME, std::ios::app | std::ios::binary);
        if (!m_logFile->is_open())
            throw std::runtime_error("Failed to open log file.");//TODO No exception?
    }

    void handleRecv(std::string message) {
        const std::lock_guard<std::mutex> lock(m_recvMutex);

        /*if (message.length() == 7 && (stoul(message) == 1036896 || stoul(message) == 3297695) &&
            (m_expectedReplies.empty() || m_expectedReplies[0] != ExpectedReply::FILE)) {
            m_expectedReplies.push_front(ExpectedReply::FILE);
        }*/

        if (m_currentStringCount > 0) {//The server is sending strings!
            /*std::ofstream string_dump_file("strings.txt", std::ios::app | std::ios::binary);
            if (string_dump_file.is_open()) {
                string_dump_file << base64_decode(xorString(message)) << '\000';
                string_dump_file.close();
            }*/
            *m_logFile << "[RECV] STRING : " << base64_decode(xorString(message)) << std::endl;
            m_currentStringCount--;
        }
        else if (m_currentAssetCount > 0) {//The server is sending assets!
            if (m_currentAssetName.empty()) {
                m_currentAssetName = xorString(message);
            }
            else {
                m_currentFile = xorString(message);
                //dumpCurrentFile(m_currentAssetName + ".png");
                *m_logFile << "[RECV] ASSET : " << m_currentAssetName << std::endl;
                m_currentAssetName.clear();
                m_currentAssetCount--;
            }
        }
        else if (m_currentFileSize != -1) {//The server is sending a file!
            if (m_currentFile.size() < m_currentFileSize) {
                m_currentFile += xorString(message);
                //*m_logFile << m_currentFile.size() << "/" << m_currentFileSize << std::endl;

                if (m_currentFile.size() >= m_currentFileSize) {//Finished
                    //dumpCurrentFile();
                    m_currentFile.clear();
                    m_currentFileSize = -1;
                }
            }
            else {
                *m_logFile << "[RECV] Error 1" << std::endl;
                m_currentFileSize = -1;//Safety
            }
        }
        else {
            //Heuristic
            if (message == "ok") {
                *m_logFile << "[RECV] OK" << std::endl;
            }
            else if (message == "0") {
                *m_logFile << "[RECV] ZERO" << std::endl;
            }
            else if (message == "e30=") {
                *m_logFile << "[RECV] {}" << std::endl;
            }
            else if (message.length() == 32 && xorString(message) == "ab33cdea3e72c957eb44677e44b98909") {
                *m_logFile << "[RECV] MAGIC" << std::endl;
            }
            else if (message.length() == 7 && is_number(message) && (stoul(message) == 1036896 || stoul(message) == 3297695)) {
                m_currentFileSize = stoul(message);
                m_currentFile.clear();
            }
            else if (message.length() == 2 && is_number(message) && stoul(message) == 49) {
                m_currentAssetCount = stoul(message);
                m_currentFile.clear();
                m_currentAssetName.clear();
            }
            else if (message.length() == 4 && is_number(message) && stoul(message) == 3402) {
                m_currentStringCount = stoul(message);
            }
            else if (message.length() < 230) {//Most likely a mapping
                /*&& (message._Starts_with("func_") || message._Starts_with("field_")*/
                *m_logFile << "[RECV] MAPPING : " << xorString(message) << std::endl;
            }
            else {
                *m_logFile << "[RECV] Unknown message :" << std::endl << message << std::endl << xorString(message) << std::endl;
            }
            //
        }
#ifdef AAAA
        else {
            //int timeout = 10;
            //while (m_expectedReplies.empty() && timeout > 0) {
            //    Sleep(500);
            //    timeout--;
            //}
            if (m_expectedReplies.empty()) {
                *m_logFile << "[RECV] Unexpected message :" << std::endl << message << std::endl;
                return;
            }

            if (m_expectedReplies[0] == ExpectedReply::OK) {
                if (message == "ok")
                    *m_logFile << "[RECV] OK" << std::endl;
                else
                    *m_logFile << "[RECV] Expected OK, got : " << message << std::endl;
            }
            else if (m_expectedReplies[0] == ExpectedReply::MAGIC) {
                if (xorString(message) == "ab33cdea3e72c957eb44677e44b98909")
                    *m_logFile << "[RECV] MAGIC" << std::endl;
                else
                    *m_logFile << "[RECV] Expected MAGIC, got : " << xorString(message) << std::endl;
            }
            else if (m_expectedReplies[0] == ExpectedReply::ZERO) {
                if (message == "0")
                    *m_logFile << "[RECV] ZERO" << std::endl;
                else
                    *m_logFile << "[RECV] Expected ZERO, got : " << message << std::endl;
            }
            else if (m_expectedReplies[0] == ExpectedReply::FILE) {
                m_currentFileSize = stoul(message);
                *m_logFile << "[RECV] Set next file size to : " << message << std::endl;

                m_currentFile.clear();
            }
            else if (m_expectedReplies[0] == ExpectedReply::MAPPING) {
                *m_logFile << "[RECV] MAPPING : " << xorString(message) << std::endl;
            }
            else if (m_expectedReplies[0] == ExpectedReply::UNK1) {
                *m_logFile << "[RECV] UNK1 : " << message << std::endl;
            }
            else if (m_expectedReplies[0] == ExpectedReply::ASSETS) {
                m_currentAssetCount = stoul(message);
                *m_logFile << "[RECV] The server will send " << message << " assets!" << std::endl;

                m_currentFile.clear();
                m_currentAssetName.clear();
            }
            else if (m_expectedReplies[0] == ExpectedReply::STRINGS) {
                m_currentStringCount = stoul(message);
                *m_logFile << "[RECV] The server will send " << message << " strings!" << std::endl;
            }

            m_expectedReplies.pop_front();
        }
#endif
    }

	void handleSend(std::string payload) {
        const std::lock_guard<std::mutex> lock(m_sendMutex);

        auto splited_payload = split(payload, '\n');
        if (splited_payload.size() == 1) return;

        uint32_t packetID = stoul(splited_payload[0]);
        //Dump order
        if (packetID == 3 && splited_payload.size() >= 3) {//Some sort of hello
            *m_logFile << "[SEND] 03: [Hello] Version : " << splited_payload[2] << std::endl;
            m_expectedReplies.push_back(ExpectedReply::OK);
        }
        else if (packetID == 12 && splited_payload.size() >= 2) {//Sets the xor encryption "key"
            m_xorKey = static_cast<uint8_t>(stoul(splited_payload[1]));
            *m_logFile << "[SEND] 12: [XorKey] Key : " << splited_payload[1] << std::endl;
        }
        else if (packetID == 2) {//Requests some sort of hash. Magic? (ab33cdea3e72c957eb44677e44b98909)
            *m_logFile << "[SEND] 02: [MagicReq]" << std::endl;
            m_expectedReplies.push_back(ExpectedReply::MAGIC);
        }
        else if (packetID == 27 && splited_payload.size() >= 4) {//??? 101
            *m_logFile << "[SEND] 27: [???] " << splited_payload[1] << splited_payload[2] << splited_payload[3] << std::endl;
            m_expectedReplies.push_back(ExpectedReply::ZERO);
        }
        else if (packetID == 47 && splited_payload.size() >= 2) {//File request (jar)
            *m_logFile << "[SEND] 47: [FileReq] File number : " << splited_payload[1] << std::endl;
            m_expectedReplies.push_back(ExpectedReply::FILE);
        }
        else if (packetID == 10 && splited_payload.size() >= 2) {//Minecraft version
            *m_logFile << "[SEND] 10: [MCVersion] Version : " << splited_payload[1] << std::endl;
            m_expectedReplies.push_back(ExpectedReply::ZERO);
        }
        else if (packetID == 53) {//File request 2? (jar)
            *m_logFile << "[SEND] 53: [FileReq2]" << std::endl;
            m_expectedReplies.push_back(ExpectedReply::FILE);
        }
        else if (packetID == 9 && splited_payload.size() >= 3) {//Minecraft Class & Method (Expects mapping from the server)
            *m_logFile << "[SEND] 9: [MC Class & Method] Class : " << xorString(splited_payload[1])
                                                    << " Method : " << xorString(splited_payload[2]) << std::endl;
            m_expectedReplies.push_back(ExpectedReply::MAPPING);
        }
        else if (packetID == 51) {//??? 55 
            *m_logFile << "[SEND] 51: [???]" << std::endl;
            m_expectedReplies.push_back(ExpectedReply::UNK1);
        }
        else if (packetID == 55) {//Request Assets
            *m_logFile << "[SEND] 55: [AssetReq]" << std::endl;
            m_expectedReplies.push_back(ExpectedReply::ASSETS);
        }
        else if (packetID == 54) {//Request Strings
            *m_logFile << "[SEND] 54: [StringReq]" << std::endl;
            m_expectedReplies.push_back(ExpectedReply::STRINGS);
        }
        else if (packetID == 8 && splited_payload.size() >= 3) {//Minecraft Class & Field (Expects mapping from the server)
            *m_logFile << "[SEND] 8: [MC Class & Field] Class : " << xorString(splited_payload[1])
                                                    << " Field : " << xorString(splited_payload[2]) << std::endl;
            m_expectedReplies.push_back(ExpectedReply::MAPPING);
        }
        else if (packetID == 56 && splited_payload.size() >= 6) {//Client Info (IGN, PC Username, Mac Address, ?, ?) (Called on unload) ummmm
            *m_logFile << "[SEND] 56: [ClientInfo] IGN : " << xorString(splited_payload[1])
                                                << " PC Username : " << xorString(splited_payload[2])
                                                << " MAC Address : " << xorString(splited_payload[3])
                                                << " UNK1 : " << xorString(splited_payload[4]) << " UNK2 : " << xorString(splited_payload[5]) <<std::endl;
        }
        else {
            *m_logFile << "[SEND] Unknown packet :" << std::endl << payload << std::endl;
        }
	}

    std::string xorString(const std::string& in) {
        std::string out;
        for (size_t i = 0; i < in.length(); i++) out.push_back(in[i] ^ m_xorKey);
        /*for (const char& c : in) { out.push_back(c ^ m_xorKey); }*/
        return out;
    }

private:
    //https://stackoverflow.com/a/46931770/13544464
    //Lazy to make my own
    std::vector<std::string> split(const std::string& s, char delim) {
        std::vector<std::string> result;
        std::stringstream ss(s);
        std::string item;

        while (getline(ss, item, delim)) {
            result.push_back(item);
        }

        return result;
    }

    bool is_number(const std::string& s) {
        return !s.empty() && std::find_if(s.begin(),
            s.end(), [](unsigned char c) { return !std::isdigit(c); }) == s.end();
    }

    void dumpCurrentFile(std::string name = "") {
        if (m_currentFile.empty()) return;
        if (name.empty()) name = "VapeDump" + std::to_string(m_dumpedFileCounter);
        std::ofstream dump(name, std::ios::binary);
        if (dump.is_open()) {
            dump.write(&m_currentFile[0], m_currentFile.size());
            dump.close();
        }
        m_dumpedFileCounter++;
        m_currentFile.clear();
    }

    std::deque<ExpectedReply> m_expectedReplies;
    std::unique_ptr<std::ofstream> m_logFile;
    uint8_t m_xorKey;

    int32_t m_currentFileSize = -1;
    int32_t m_currentAssetCount = -1;
    int32_t m_currentStringCount = -1;

    std::string m_currentFile;
    std::string m_currentAssetName;

    size_t m_dumpedFileCounter = 0;

    std::mutex m_sendMutex;
    std::mutex m_recvMutex;
};