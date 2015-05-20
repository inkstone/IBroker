project("Interactive Broker API Python Wrapper")

#prerequests
cmake_minimum_required(VERSION 2.8 FATAL_ERROR)
find_package(PythonLibs REQUIRED)
find_package(PythonInterp REQUIRED)
find_package(Boost COMPONENTS python REQUIRED)  #boost_pythons need to be the same version

#generate source files
execute_process(COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/script/genPythonWrapper.py)

#code settings
include_directories(${Boost_INCLUDE_DIRS} ${PYTHON_INCLUDE_DIRS})
include_directories("${CMAKE_CURRENT_SOURCE_DIR}/include")
file(GLOB OTHER_SRC
  "${CMAKE_CURRENT_SOURCE_DIR}/src/*.c"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp"
  )

#macro
add_definitions( -DIB_USE_STD_STRING -Wno-switch)

#remove prefix of generated library
set(CMAKE_SHARED_LIBRARY_PREFIX "")
#target library
add_library(IBroker SHARED IBroker.cpp ${OTHER_SRC})
#link with boost_python
target_link_libraries(IBroker ${Boost_LIBRARIES} ${PYTHON_LIBRARY})
#enable C++11
target_compile_features(IBroker PUBLIC cxx_range_for)


  
