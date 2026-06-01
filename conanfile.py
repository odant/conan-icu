# ICU Conan package
# Dmitriy Vetutnev, ODANT 2018-2020
# Arkady Yudintsev, ODANT 2021-2025


from conan import ConanFile, tools
import os, glob, shutil, platform


class ICUConan(ConanFile):
    name = "icu"
    version = "78.3+0"
    license = "http://www.unicode.org/copyright.html#License"
    description = "ICU is a mature, widely used set of C/C++ and Java libraries " \
                  "providing Unicode and Globalization support for software applications."
    url = "https://github.com/odant/conan-icu"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "dll_sign": [True, False],
        "with_unit_tests": [True, False],
        "shared": [True, False]
    }
    default_options = {
        "dll_sign": True,
        "with_unit_tests": False,
        "shared": True
    }
    exports_sources = "src/*", "msvc.patch", "data_rc.patch", "icudata-stdlibs.patch"
    no_copy_source = False
    build_policy = "missing"
    package_type = "library"
    python_requires = "windows_signtool/[>=1.2]@odant/stable"

    def configure(self):
        # Only C++11
        if self.settings.compiler.get_safe("libcxx") == "libstdc++":
            raise Exception("This package is only compatible with libstdc++11")
        # MT(d) static library
        if self.settings.os == "Windows" and self.settings.compiler == "msvc":
            if self.settings.compiler.runtime == "static":
                self.options.shared = False
        # DLL sign, only Windows and shared
        if self.settings.os != "Windows" or self.options.shared == False:
            self.options.rm_safe("dll_sign")

    def build_requirements(self):
        if self.settings.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")

    def source(self):
        tools.files.patch(self, patch_file="msvc.patch")
        tools.files.patch(self, patch_file="data_rc.patch")
        tools.files.patch(self, patch_file="icudata-stdlibs.patch")
        if platform.system() != "Windows":
            self.run("chmod a+x %s" % os.path.join(self.source_folder, "src", "source", "configure"))
    
    def generate(self):
        env = tools.env.VirtualBuildEnv(self)
        env.generate()
        if tools.microsoft.is_msvc(self):
            vc = tools.microsoft.VCVars(self)
            vc.generate()

    def build(self):
        flags = self.get_build_flags()
        install_folder = os.path.join(self.build_folder, "icu_install").replace("\\", "/")
        flags.append("--prefix=%s" % tools.microsoft.subsystems.unix_path(self, install_folder))
        with tools.files.chdir(self, os.path.join(self.source_folder, "src", "source")):
            self.run("bash -C runConfigureICU %s" % " ".join(flags))
            debug_arg = "VERBOSE=1" if self.settings.build_type == "Debug" else ""
            self.run("make %s -j %s" % (debug_arg, tools.build.build_jobs(self)))
            self.run("make install")
            if self.options.with_unit_tests:
                self.run("make check")

    def get_build_flags(self):
        flags = []
        if self.settings.build_type == "Debug":
            flags.extend([
                "--enable-debug",
                "--disable-release"
            ])
        flags.append(self.get_target_platform())
        if self.options.shared:
            flags.extend([
                "--enable-shared",
                "--disable-static",
                "--with-data-packaging=library"
            ])
        else:
            flags.extend([
                "--disable-shared",
                "--enable-static",
                "--with-data-packaging=static",
                "--disable-dyload"
            ])
        flags.extend([
            "--with-library-bits=%s" % {"x86": "32", "x86_64": "64", "mips": "32", "armv7": "32"}.get(str(self.settings.arch)),
            "--disable-renaming",
            "--disable-extras"
        ])
        if self.options.with_unit_tests:
            flags.extend([
                "--enable-tests",
                "--enable-samples"
            ])
        else:
            flags.extend([
                "--disable-tests",
                "--disable-samples"
            ])
        return flags

    def get_target_platform(self):
        if self.settings.os == "Windows":
            if self.settings.compiler == "msvc":
                platform = "Cygwin/MSVC"
            elif self.settings.compiler == "clang" and self.settings.compiler.runtime_version:
                platform = "Cygwin/ClangCL"
            else:
               raise Exception("Unsupported compiler on Windows!")
            if self.settings.compiler.runtime == "static":
                platform += "_MT"
            self.output.info("Using '%s' target platform" % platform)
            return platform
        elif self.settings.os == "Linux":
            if self.settings.compiler == "gcc":
                return "Linux/gcc"
            else:
                return "Linux" # Use the clang/clang++ or GNU gcc/g++ compilers on Linux
        else:
            raise Exception("Unsupported target platform!")

    def package(self):
        # Headers
        tools.files.copy(self, "*", dst=os.path.join(self.package_folder, "include"), src=os.path.join(self.build_folder, "icu_install", "include"), keep_path=True)
        if self.settings.os == "Windows":        
            tools.files.copy(self, "*.dll", dst=os.path.join(self.package_folder, "bin"), src=os.path.join(self.source_folder, "src", "source", "lib"), keep_path=False, excludes=["icutu*", "sicutu*", "icutest*", "sicutest*"])
            tools.files.copy(self, "*.pdb", dst=os.path.join(self.package_folder, "bin"), src=os.path.join(self.source_folder, "src", "source", "lib"), keep_path=False, excludes=["icutu*", "sicutu*", "icutest*", "sicutest*"])
            tools.files.copy(self, "*.lib", dst=os.path.join(self.package_folder, "lib"), src=os.path.join(self.source_folder, "src", "source", "lib"), keep_path=False, excludes=["icutu*", "sicutu*", "icutest*", "sicutest*"])
        else:        
            # Linux libraries
            tools.files.copy(self, "libicudata.so*", dst=os.path.join(self.package_folder, "lib"), src=os.path.join(self.build_folder, "icu_install", "lib"), keep_path=False)
            tools.files.copy(self, "libicuuc.so*", dst=os.path.join(self.package_folder, "lib"), src=os.path.join(self.build_folder, "icu_install", "lib"), keep_path=False)
            tools.files.copy(self, "libicui18n.so*", dst=os.path.join(self.package_folder, "lib"), src=os.path.join(self.build_folder, "icu_install", "lib"), keep_path=False)
            tools.files.copy(self, "libicuio.so*", dst=os.path.join(self.package_folder, "lib"), src=os.path.join(self.build_folder, "icu_install", "lib"), keep_path=False)
            tools.files.copy(self, "libicudata.a", dst=os.path.join(self.package_folder, "lib"), src=os.path.join(self.build_folder, "icu_install", "lib"), keep_path=False)
            tools.files.copy(self, "libicuuc.a", dst=os.path.join(self.package_folder, "lib"), src=os.path.join(self.build_folder, "icu_install", "lib"), keep_path=False)
            tools.files.copy(self, "libicui18n.a", dst=os.path.join(self.package_folder, "lib"), src=os.path.join(self.build_folder, "icu_install", "lib"), keep_path=False)
            tools.files.copy(self, "libicuio.a", dst=os.path.join(self.package_folder, "lib"), src=os.path.join(self.build_folder, "icu_install", "lib"), keep_path=False)
        # Sign DLL
        if self.options.get_safe("dll_sign"):
            self.win_bash = False
            self.python_requires["windows_signtool"].module.sign(self, [os.path.join(self.package_folder, "bin", "*.dll")])

    def package_id(self):
        # ICU unit testing shouldn't affect the package's ID
        self.info.options.with_unit_tests = "any"

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "ICU")

        prefix = "s" if self.settings.os == "Windows" and not self.options.shared else ""
        suffix = "d" if self.settings.os == "Windows" and self.settings.build_type == "Debug" else ""

        # icudata
        self.cpp_info.components["icu-data"].set_property("cmake_target_name", "ICU::data")
        icudata_libname = "icudt" if self.settings.os == "Windows" else "icudata"
        self.cpp_info.components["icu-data"].libs = [f"{prefix}{icudata_libname}{suffix}"]
        self.cpp_info.components["icu-data"].defines.append("U_DISABLE_RENAMING=1")
        if not self.options.shared:
            self.cpp_info.components["icu-data"].defines.append("U_STATIC_IMPLEMENTATION")
            # icu uses c++, so add the c++ runtime
            libcxx = stdcpp_library(self)
            if libcxx:
                self.cpp_info.components["icu-data"].system_libs.append(libcxx)

        # Alias of data CMake component
        self.cpp_info.components["icu-data-alias"].set_property("cmake_target_name", "ICU::dt")
        self.cpp_info.components["icu-data-alias"].requires = ["icu-data"]

        # icuuc
        self.cpp_info.components["icu-uc"].set_property("cmake_target_name", "ICU::uc")
        self.cpp_info.components["icu-uc"].set_property("pkg_config_name", "icu-uc")
        self.cpp_info.components["icu-uc"].libs = [f"{prefix}icuuc{suffix}"]
        self.cpp_info.components["icu-uc"].requires = ["icu-data"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["icu-uc"].system_libs = ["m", "pthread"]
        elif self.settings.os == "Windows":
            self.cpp_info.components["icu-uc"].system_libs = ["advapi32"]

        # icui18n
        self.cpp_info.components["icu-i18n"].set_property("cmake_target_name", "ICU::i18n")
        self.cpp_info.components["icu-i18n"].set_property("pkg_config_name", "icu-i18n")
        icui18n_libname = "icuin" if self.settings.os == "Windows" else "icui18n"
        self.cpp_info.components["icu-i18n"].libs = [f"{prefix}{icui18n_libname}{suffix}"]
        self.cpp_info.components["icu-i18n"].requires = ["icu-uc"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["icu-i18n"].system_libs = ["m"]

        # Alias of i18n CMake component
        self.cpp_info.components["icu-i18n-alias"].set_property("cmake_target_name", "ICU::in")
        self.cpp_info.components["icu-i18n-alias"].requires = ["icu-i18n"]

        # icuio
        self.cpp_info.components["icu-io"].set_property("cmake_target_name", "ICU::io")
        self.cpp_info.components["icu-io"].set_property("pkg_config_name", "icu-io")
        self.cpp_info.components["icu-io"].libs = [f"{prefix}icuio{suffix}"]
        self.cpp_info.components["icu-io"].requires = ["icu-i18n", "icu-uc"]

