cmake_minimum_required(VERSION 3.16)
project(comm_pattern_generator)

list(INSERT CMAKE_MODULE_PATH 0 "${CMAKE_SOURCE_DIR}/cmake")

set(CMAKE_CXX_STANDARD 17)

add_executable(comm_pattern_generator)

target_sources(comm_pattern_generator PRIVATE src/driver.cpp src/configuration.cpp src/comm_pattern.cpp src/naive_reduce.cpp src/amg2013.cpp src/unstructured_mesh.cpp)
target_include_directories(comm_pattern_generator PRIVATE include include/comm_pattern_generator include/external)

# Boost
find_package(Boost 1.69.0 REQUIRED mpi serialization)
target_include_directories(comm_pattern_generator PRIVATE ${Boost_INCLUDE_DIR})
target_link_libraries(comm_pattern_generator PRIVATE Boost::mpi)
target_link_libraries(comm_pattern_generator PRIVATE Boost::serialization)
