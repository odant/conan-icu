# Test for ICU Conan package
# Dmitriy Vetutnev, ODANT, 2018


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

    add_test(
        NAME case_ls
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
        COMMAND ls -l
    )

    message(STATUS "LD_LIBRARY_PATH: $ENV{LD_LIBRARY_PATH}")

    add_test(
        NAME case_ld_debug
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
        COMMAND case_CONAN_PKG
    )
    set_property(TEST case_ld_debug PROPERTY ENVIRONMENT LD_DEBUG=libs)

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
