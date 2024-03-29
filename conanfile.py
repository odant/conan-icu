# ICU Conan package
# Dmitriy Vetutnev, ODANT 2018-2020


from conans import ConanFile, tools
import os, glob


class ICUConan(ConanFile):
    name = "icu"
    version = "74.2+0"
    license = "http://www.unicode.org/copyright.html#License"
    description = "ICU is a mature, widely used set of C/C++ and Java libraries " \
                  "providing Unicode and Globalization support for software applications."
    url = "https://github.com/odant/conan-icu"
    settings = {
        "os": ["Windows", "Linux"],
        "compiler": ["Visual Studio", "gcc", "clang"],
        "build_type": ["Debug", "Release"],
        "arch": ["x86", "x86_64", "mips", "armv7"]
    }
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
    exports_sources = "src/*", "FindICU.cmake", "msvc.patch", "data_rc.patch", "icudata-stdlibs.patch"
    no_copy_source = False
    build_policy = "missing"

    def configure(self):
        # Only C++11
        if self.settings.compiler.get_safe("libcxx") == "libstdc++":
            raise Exception("This package is only compatible with libstdc++11")
        # MT(d) static library
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            if self.settings.compiler.runtime == "MT" or self.settings.compiler.runtime == "MTd":
                self.options.shared=False
        # DLL sign, only Windows and shared
        if self.settings.os != "Windows" or self.options.shared == False:
            del self.options.dll_sign

    def build_requirements(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.build_requires("cygwin_installer/2.9.0@bincrafters/stable")
        if self.options.get_safe("dll_sign"):
            self.build_requires("windows_signtool/[>=1.2]@%s/stable" % self.user)

    def source(self):
        tools.patch(patch_file="msvc.patch")
        tools.patch(patch_file="data_rc.patch")
        tools.patch(patch_file="icudata-stdlibs.patch")
        if not tools.os_info.is_windows:
            self.run("chmod a+x %s" % os.path.join(self.source_folder, "src/source/configure"))

    def build(self):
        flags = self.get_build_flags()
        install_folder = os.path.join(self.build_folder, "icu_install").replace("\\", "/")
        flags.append("--prefix=%s" % tools.unix_path(install_folder))
        build_env = self.get_build_environment()
        with tools.chdir("src/source"), tools.environment_append(build_env):
            self.run("bash -C runConfigureICU %s" % " ".join(flags))
            debug_arg = "VERBOSE=1" if self.settings.build_type == "Debug" else ""
            self.run("make %s -j %s" % (debug_arg, tools.cpu_count()))
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
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            platform = "Cygwin/MSVC"
            vs_toolset = str(self.settings.compiler.toolset).lower()
            if vs_toolset == "clangcl":
                platform += "_ClangCL"
            if self.settings.compiler.runtime == "MT" or self.settings.compiler.runtime == "MTd":
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

    def get_build_environment(self):
        env = {}
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            env = tools.vcvars_dict(self)
        return env

    def package(self):
        # CMake script
        self.copy("FindICU.cmake", dst=".", src=".", keep_path=False)
        # Headers
        self.copy("*", dst="include", src="icu_install/include", keep_path=True)
        # Linux libraries
        self.copy("libicudata.so*", dst="lib", src="icu_install/lib", keep_path=False, symlinks=True)
        self.copy("libicuuc.so*", dst="lib", src="icu_install/lib", keep_path=False, symlinks=True)
        self.copy("libicui18n.so*", dst="lib", src="icu_install/lib", keep_path=False, symlinks=True)
        self.copy("libicuio.so*", dst="lib", src="icu_install/lib", keep_path=False, symlinks=True)
        self.copy("libicudata.a", dst="lib", src="icu_install/lib", keep_path=False)
        self.copy("libicuuc.a", dst="lib", src="icu_install/lib", keep_path=False)
        self.copy("libicui18n.a", dst="lib", src="icu_install/lib", keep_path=False)
        self.copy("libicuio.a", dst="lib", src="icu_install/lib", keep_path=False)
        # Windows libraries
        self.copy("*.dll", dst="bin", src="src/source/lib", keep_path=False, excludes=["icutu*", "sicutu*"])
        self.copy("*.pdb", dst="bin", src="src/source/lib", keep_path=False, excludes=["icutu*", "sicutu*"])
        self.copy("*.lib", dst="lib", src="src/source/lib", keep_path=False, excludes=["icutu*", "sicutu*"])
        # Sign DLL
        if self.options.get_safe("dll_sign"):
            import windows_signtool
            pattern = os.path.join(self.package_folder, "bin", "*.dll")
            for fpath in glob.glob(pattern):
                fpath = fpath.replace("\\", "/")
                for alg in ["sha1", "sha256"]:
                    is_timestamp = True if self.settings.build_type == "Release" else False
                    cmd = windows_signtool.get_sign_command(fpath, digest_algorithm=alg, timestamp=is_timestamp)
                    self.output.info("Sign %s" % fpath)
                    self.run(cmd)

        # Debug build in local folder
        if not self.in_local_cache:
            self.copy("conanfile.py", dst=".", keep_path=False)

    def package_id(self):
        # ICU unit testing shouldn't affect the package's ID
        self.info.options.with_unit_tests = "any"

    def package_info(self):
        self.cpp_info.defines = ["U_DISABLE_RENAMING=1"]
        if not self.options.shared:
            self.cpp_info.defines.append("U_STATIC_IMPLEMENTATION=1")
        if self.settings.os == "Windows":
            self.cpp_info.libs = tools.collect_libs(self)
        else:
            self.cpp_info.libs = ["icuio", "icui18n", "icuuc", "icudata", "pthread"]

