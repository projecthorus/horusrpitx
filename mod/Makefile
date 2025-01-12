CXXFLAGS ?= -std=c++11 -Wall -g -O2 -Wno-unused-variable
LDFLAGS ?= -L/opt/vc/lib
LDFLAGS += -lrpitx
CXX ?= c++

all: horus4fsk

horus4fsk: horus4fsk.cpp
	$(CXX) $(CXXFLAGS) -o horus4fsk horus4fsk.cpp  $(LDFLAGS)
	@echo "Built horus4fsk"

clean:
	rm -f tx_horus *.o
