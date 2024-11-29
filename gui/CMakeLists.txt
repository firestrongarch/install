cmake_minimum_required(VERSION 3.20)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

project(QtGui)

find_package(Qt6 REQUIRED COMPONENTS Widgets)
find_package(yaml-cpp REQUIRED)
file(GLOB srcs *.cpp)
add_executable(QtGui ${srcs})
target_link_libraries(QtGui PRIVATE Qt6::Widgets yaml-cpp)