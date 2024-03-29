# Test for ICU Conan package
# Dmitriy Vetutnev, ODANT, 2018-2020


project(PackageTest CXX)
cmake_minimum_required(VERSION 3.0)


include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(TARGETS)


enable_testing()


# Conan imported targets
add_executable(case_CONAN_PKG case.cpp)
target_link_libraries(case_CONAN_PKG CONAN_PKG::icu)
set_target_properties(case_CONAN_PKG
    PROPERTIES
    INSTALL_RPATH "$ORIGIN"
    BUILD_WITH_INSTALL_RPATH True
)
add_test(
    NAME case_CONAN_PKG
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMAND case_CONAN_PKG
)
if(UNIX)
    set_property(TEST case_CONAN_PKG PROPERTY ENVIRONMENT LD_LIBRARY_PATH=${CMAKE_BINARY_DIR}/bin)
endif()


# ICU imported tragets
find_package(ICU REQUIRED)

add_executable(case case.cpp)
target_link_libraries(case ICU::io)
set_target_properties(case
    PROPERTIES
    INSTALL_RPATH "$ORIGIN"
    BUILD_WITH_INSTALL_RPATH True
)
add_test(
    NAME case
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMAND case
)
if(UNIX)
    set_property(TEST case PROPERTY ENVIRONMENT LD_LIBRARY_PATH=${CMAKE_BINARY_DIR}/bin)
endif()


# Debug static build
find_package(ICU REQUIRED)

add_executable(test_ucnv_open test_ucnv_open.cpp)
target_link_libraries(test_ucnv_open ICU::io)
set_target_properties(test_ucnv_open
    PROPERTIES
    INSTALL_RPATH "$ORIGIN"
    BUILD_WITH_INSTALL_RPATH True
)
add_test(
    NAME test_ucnv_open
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMAND test_ucnv_open
)
if(UNIX)
    set_property(TEST test_ucnv_open PROPERTY ENVIRONMENT LD_LIBRARY_PATH=${CMAKE_BINARY_DIR}/bin)
endif()

