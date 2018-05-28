# Test for Conan package
# Dmitriy Vetutnev, ODANT, 2018


project(PackageTest CXX)
cmake_minimum_required(VERSION 3.0)


include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(TARGETS)


set(CMAKE_RUNTIME_OUTPUT_DIRECTORY bin)


enable_testing()


add_executable(case case.cpp)
target_link_libraries(case CONAN_PKG::icu)
set_target_properties(case
    PROPERTIES
    INSTALL_RPATH "$ORIGIN"
    BUILD_WITH_INSTALL_RPATH True
)
add_test(
    NAME case_ldd
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMAND ldd case
)
add_test(
    NAME case_ls
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMAND ls -l
)
add_test(
    NAME case
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMAND case
)
