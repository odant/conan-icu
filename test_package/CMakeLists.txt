# Test for Conan package
# Dmitriy Vetutnev, ODANT, 2018


project(PackageTest CXX)
cmake_minimum_required(VERSION 3.0)


include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(TARGETS)


enable_testing()


add_executable(case case.cpp)
target_link_libraries(case CONAN_PKG::icu)
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
