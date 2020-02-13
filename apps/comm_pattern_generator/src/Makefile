CXX=mpicxx
CPPFLAGS=-g
CFLAGS=-std=c++17 -O3
INCLUDES=-I.
LDFLAGS=
LIBS=

SOURCES=main.cpp naive_reduce.cpp
OBJECTS=$(patsubst %.cpp, %.o, $(SOURCES))
TARGET=generator.exe

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CXX) $(LDFLAGS) -o $@ $(OBJECTS) $(LIBS)

%.o: %.cpp
	$(CXX) -c $(CPPFLAGS) -o $@ $< $(CFLAGS)

clean:
	rm -f $(TARGET) $(OBJECTS)
