/* 
 * horus4fsk.cpp - A simple Raspberry Pi transmitter for Horus Binary v2 
 * (C) 2024 Andrew Koenig KE5GDB <ke5gdb@gmail.com>
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <cstring>
#include <errno.h>
#include <stdarg.h>
#include <stdint.h>
#include <time.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <iostream>
#include <fstream>

#include <librpitx/librpitx.h>

#define PREAMBLE 0x1B

ngfmdmasync *mod;
int FifoSize=10000; //10ms
bool running=true;

int tone_spacing = 270;
int baud_rate = 100;

void PlayTone(double Frequency,uint32_t Timing)//Timing in 0.1us
{
    uint32_t SumTiming=0;
    SumTiming+=Timing%100;
    if(SumTiming>=100)
    {
        Timing+=100;
        SumTiming=SumTiming-100;
    }
    int samples=(Timing/100);

    while(samples>0)
    {
        usleep(10);
        int Available=mod->GetBufferAvailable();
        if(Available>FifoSize/2)
        {
            int Index=mod->GetUserMemIndex();
            if(Available>samples) Available=samples;
            for(int j=0;j<Available;j++)
            {
                mod->SetFrequencySample(Index+j,Frequency);
                samples--;
            }
        }
    }
}

void TransmitByte(char byte)
{
    double tone;
    for(int i=0; i<4; i++) {
        tone = ((byte & 0b11000000) >> 6) * tone_spacing - (tone_spacing * 1.5); // there is probably a better way to do this
        PlayTone(tone, (uint32_t)(10000000 / baud_rate));
        byte <<= 2;
    }
}

void TransmitStream(std::string packet)
{
    std::ios_base::sync_with_stdio(false);

    char c;
    int charsRead;
    bool lineRead = false;

	while(running) {
        TransmitByte(PREAMBLE);
        TransmitByte(PREAMBLE);
        TransmitByte(PREAMBLE);
        TransmitByte(PREAMBLE);

        // If packet is provided via function argv this is a one-shot transmission
        if (packet.length() > 0) {
            running = false;
            lineRead = true;
        } else {
            // Grab as many characters as we can from stdin
            do {
                charsRead = std::cin.readsome(&c, 1);
                if(charsRead == 1) {
                    if(c == '\n') {
                        lineRead = true; 
                    } else {
                        packet.append(1, c);
                    }
                }
            } while (charsRead != 0);
        }

        // If complete line, then transmit packet
        if(lineRead) {
            // Check to see if OneBitPerByte input
            const char *cpacket = packet.c_str();
            std::stringstream spacket;
            if(cpacket[0] < 0x02) {
                for(unsigned i=0; i<packet.length(); i++) {
                    c |= (cpacket[i] << (7 - (i % 8)));
                    if((i % 8) == 0 && i > 0) {
                        TransmitByte(c);
                        spacket << std::hex << (int)c;
                        c = 0;
                    }
                }
                std::cout << "Transmitted packet: " << spacket.str() << std::endl;
            } else {
                if((packet.length() % 2) == 0) {
                    for(unsigned i=0; i<packet.length(); i+=2) {
                        c = std::stoi(packet.substr(i, 2), nullptr, 16);
                        TransmitByte(c);
                    }
                } else {
                    fprintf(stderr, "Input packet is missing a nibble!\n");
                }
                std::cout << "Transmitted packet: " << packet << std::endl;
            }
            lineRead = false;
            packet.clear();
        }
	}
}

static void terminate(int num)
{
    running=false;
	fprintf(stderr,"Caught signal - Terminating %x\n",num);
}

int main(int argc, char **argv)
{
	float frequency = 434.5e6;
    std::string packet;

	if (argc > 1) {
		frequency = atof(argv[1]);
        if (argc == 3) {
            packet = argv[2];
        }
    } else {
		printf("usage : horus4fsk frequency(Hz) [packet]\n");
		exit(0);
	}

    std::cout << "argc " << argc << std::endl;
    std::cout << "Starting transmission on " << frequency << std::endl;

	for (int i = 0; i < 64; i++) {
        struct sigaction sa;

        std::memset(&sa, 0, sizeof(sa));
        sa.sa_handler = terminate;
        sigaction(i, &sa, NULL);
    }

	mod=new ngfmdmasync(frequency,100000,14,FifoSize);

    TransmitStream(packet);

    // Allow last symbol to clear FIFO
    usleep((uint32_t)(1000000 / baud_rate));

	delete mod;
	return 0;
}