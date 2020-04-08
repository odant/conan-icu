# FindICU.cmake for ICU Conan package
# Dmitriy Vetutnev, ODANT 2018-2020


# Include path
find_path(ICU_INCLUDE_DIR
    NAMES unicode/uvernum.h
    PATHS ${CONAN_INCLUDE_DIRS_ICU}
    NO_DEFAULT_PATH
)

# Get version
if(ICU_INCLUDE_DIR AND EXISTS ${ICU_INCLUDE_DIR}/unicode/uvernum.h)

    file(STRINGS ${ICU_INCLUDE_DIR}/unicode/uvernum.h icu_header_str
        REGEX "^#define[\t ]+U_ICU_VERSION[\t ]+\".*\".*")

    string(REGEX REPLACE "^#define[\t ]+U_ICU_VERSION[\t ]+\"([^ \\n]*)\".*"
        "\\1" icu_version_string ${icu_header_str})

    set(ICU_VERSION ${icu_version_string})
    unset(icu_header_str)
    unset(icu_version_string)

endif()

# Libaries
find_library(ICU_data_LIBRARY
    NAMES icudata icudt icudtd icudt64 icudt64d sicudt sicudtd sicudt64 sicudt64d
    PATHS ${CONAN_LIB_DIRS_ICU}
    NO_DEFAULT_PATH
)

find_library(ICU_uc_LIBRARY
    NAMES icuuc icuucd icuuc64 icuuc64d sicuuc sicuucd sicuuc64 sicuuc64d
    PATHS ${CONAN_LIB_DIRS_ICU}
    NO_DEFAULT_PATH
)

find_library(ICU_i18n_LIBRARY
    NAMES icui18n icuin icuind icuin64 icuin64d sicuin sicuind sicuin64 sicuin64d
    PATHS ${CONAN_LIB_DIRS_ICU}
    NO_DEFAULT_PATH
)

find_library(ICU_io_LIBRARY
    NAMES icuio icuiod icuio64 icuio64d sicuio sicuiod sicuio64 sicuio64d
    PATHS ${CONAN_LIB_DIRS_ICU}
    NO_DEFAULT_PATH
)


include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(ICU
    REQUIRED_VARS ICU_INCLUDE_DIR ICU_io_LIBRARY ICU_i18n_LIBRARY ICU_uc_LIBRARY ICU_data_LIBRARY
    VERSION_VAR ICU_VERSION
)


if(ICU_FOUND)

    # Set-up variables
    set(ICU_INCLUDE_DIRS ${ICU_INCLUDE_DIR})
    set(ICU_LIBRARIES ${ICU_io_LIBRARY} ${ICU_i18n_LIBRARY} ${ICU_uc_LIBRARY} ${ICU_data_LIBRARY})
    set(ICU_in_LIBRARY ${ICU_i18n_LIBARARY})
    set(ICU_dt_LIBRARY ${ICU_data_LIBARARY})
    mark_as_advanced(ICU_INCLUDE_DIR ICU_io_LIBRARY ICU_i18n_LIBRARY ICU_uc_LIBRARY ICU_data_LIBRARY ICU_in_LIBRARY ICU_dt_LIBRARY)
    set(ICU_DEFINITIONS ${CONAN_COMPILE_DEFINITIONS_ICU}) # Add defines from package_info

    # Imported targets
    if(NOT TARGET ICU::data)

        add_library(ICU::data UNKNOWN IMPORTED)
        set_target_properties(ICU::data PROPERTIES
            INTERFACE_INCLUDE_DIRECTORIES ${ICU_INCLUDE_DIR}
            IMPORTED_LOCATION ${ICU_data_LIBRARY}
        )
        if (ICU_DEFINITIONS)
            set_property(TARGET ICU::data
                APPEND PROPERTY INTERFACE_COMPILE_DEFINITIONS ${ICU_DEFINITIONS}
            )
        endif()

    endif()

    if(NOT TARGET ICU::dt)

        add_library(ICU::dt UNKNOWN IMPORTED)
        set_target_properties(ICU::dt PROPERTIES
            INTERFACE_INCLUDE_DIRECTORIES ${ICU_INCLUDE_DIR}
            IMPORTED_LOCATION ${ICU_data_LIBRARY}
        )
        if (ICU_DEFINITIONS)
            set_property(TARGET ICU::dt
                APPEND PROPERTY INTERFACE_COMPILE_DEFINITIONS ${ICU_DEFINITIONS}
            )
        endif()

    endif()

    if(NOT TARGET ICU::uc)

        add_library(ICU::uc UNKNOWN IMPORTED)
        set_target_properties(ICU::uc PROPERTIES
            IMPORTED_LOCATION ${ICU_uc_LIBRARY}
            INTERFACE_LINK_LIBRARIES ICU::data
        )

    endif()

    if(NOT TARGET ICU::i18n)

        add_library(ICU::i18n UNKNOWN IMPORTED)
        set_target_properties(ICU::i18n PROPERTIES
            IMPORTED_LOCATION ${ICU_i18n_LIBRARY}
            INTERFACE_LINK_LIBRARIES ICU::uc
        )

    endif()

    if(NOT TARGET ICU::in)

        add_library(ICU::in UNKNOWN IMPORTED)
        set_target_properties(ICU::in PROPERTIES
            IMPORTED_LOCATION ${ICU_i18n_LIBRARY}
            INTERFACE_LINK_LIBRARIES ICU::uc
        )

    endif()

    if(NOT TARGET ICU::io)

        add_library(ICU::io UNKNOWN IMPORTED)
        set_target_properties(ICU::io PROPERTIES
            IMPORTED_LOCATION ${ICU_io_LIBRARY}
            INTERFACE_LINK_LIBRARIES ICU::i18n
        )

    endif()

endif()
