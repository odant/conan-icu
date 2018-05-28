# ICU Conan package
# Dmitriy Vetutnev, ODANT 2018


from conans import ConanFile, tools
import os


class ICUConan(ConanFile):
    name = "icu"
    version = "61.1"
    license = "http://www.unicode.org/copyright.html#License"
    description = "ICU is a mature, widely used set of C/C++ and Java libraries " \
                  "providing Unicode and Globalization support for software applications."
    url = "https://github.com/odant/conan-icu"
    settings = {
        "os": ["Windows", "Linux"],
        "compiler": ["Visual Studio", "gcc"],
        "build_type": ["Debug", "Release"],
        "arch": ["x86", "x86_64", "mips"]
    }
    options = {
        "dll_sign": [True, False],
        "with_unit_tests": [True, False]
    }
    default_options = "dll_sign=True", "with_unit_tests=False"
    exports_sources = "src/*"
    no_copy_source = False
    build_policy = "missing"

    def configure(self):
        # Only C++11
        if self.settings.compiler.get_safe("libcxx") == "libstdc++":
            raise Exception("This package is only compatible with libstdc++11")
        # DLL sign, only Windows
        if self.settings.os != "Windows":
            del self.options.dll_sign

    def build_requirements(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.build_requires("cygwin_installer/2.9.0@bincrafters/stable")
            self.build_requires("find_sdk_winxp/[~=1.0]@%s/stable" % self.user)

    def build(self):
        flags = self.get_build_flags()
        install_folder = os.path.join(self.build_folder, "icu_install").replace("\\", "/")
        flags.append("--prefix=%s" % tools.unix_path(install_folder))
        build_env = self.get_build_environment()
        with tools.chdir("src/source"), tools.environment_append(build_env):
            self.run("bash -C runConfigureICU %s" % " ".join(flags))
            #self.run("bash -C runConfigureICU Cygwin/MSVC --help=recursive")
            cpu_count = tools.cpu_count() if self.settings.compiler != "Visual Studio" else "1"
            self.run("make -j %s" % cpu_count)
            if self.options.with_unit_tests:
                self.run("make check")
            self.run("make install")

    def get_build_flags(self):
        flags = []
        if self.settings.build_type == "Debug":
            flags.extend([
                "--enable-debug",
                "--disable-release"
            ])
        flags.append(self.get_target_platform())
        flags.extend([
            "--with-library-bits=%s" % {"x86": "32", "x86_64": "64", "mips": "32"}.get(str(self.settings.arch)),
            "--enable-shared",
            "--disable-renaming",
            "--with-data-packaging=library",
            "--disable-samples"
        ])
        if self.settings.os == "Windows" and self.settings.arch == "x86_64":
            flags.append("--with-library-suffix=64")
        if self.options.with_unit_tests:
            flags.append("--enable-tests")
        else:
            flags.append("--disable-tests")
        return flags

    def get_target_platform(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            return "Cygwin/MSVC"
        elif self.settings.os == "Linux" and self.settings.compiler == "gcc":
            return "Linux/gcc"
        else:
            raise Exception("Unsupported target pltform!")
    
    def get_build_environment(self):
        env = {}
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            env = tools.vcvars_dict(self.settings, filter_known_paths=False, force=True)
            toolset = str(self.settings.compiler.get_safe("toolset"))
            if toolset.endswith("_xp"):
                import find_sdk_winxp
                env = find_sdk_winxp.dict_append(self.settings.arch, env=env)
            env["CFLAGS"] = "/FS"
            env["CXXFLAGS"] = "/FS"
        return env

    def package(self):
        # Headers
        self.copy("*", dst="include", src="icu_install/include", keep_path=True)
        # Linux libraries
        self.copy("libicudata.so*", dst="lib", src="icu_install/lib", keep_path=False, symlinks=True)
        self.copy("libicuuc.so*", dst="lib", src="icu_install/lib", keep_path=False, symlinks=True)
        self.copy("libicui18n.so*", dst="lib", src="icu_install/lib", keep_path=False, symlinks=True)
        self.copy("libicuio.so*", dst="lib", src="icu_install/lib", keep_path=False, symlinks=True)
        # Windows libraries
        self.copy("icudt*.dll", dst="bin", src="src/source/lib", keep_path=False)
        self.copy("icudt*.pdb", dst="bin", src="src/source/lib", keep_path=False)
        self.copy("icudt*.lib", dst="lib", src="icu_install/lib", keep_path=False)
        self.copy("icuuc*.dll", dst="bin", src="src/source/lib", keep_path=False)
        self.copy("icuuc*.pdb", dst="bin", src="src/source/lib", keep_path=False)
        self.copy("icuuc*.lib", dst="lib", src="icu_install/lib", keep_path=False)
        self.copy("icuin*.dll", dst="bin", src="src/source/lib", keep_path=False)
        self.copy("icuin*.pdb", dst="bin", src="src/source/lib", keep_path=False)
        self.copy("icuin*.lib", dst="lib", src="icu_install/lib", keep_path=False)
        self.copy("icuio*.dll", dst="bin", src="src/source/lib", keep_path=False)
        self.copy("icuio*.pdb", dst="bin", src="src/source/lib", keep_path=False)
        self.copy("icuio*.lib", dst="lib", src="icu_install/lib", keep_path=False)

    def package_id(self):
        # ICU unit testing shouldn't affect the package's ID
        self.info.options.with_unit_tests = "any"

    def package_info(self):
        self.cpp_info.defines = ["U_DISABLE_RENAMING=1"]
        if self.settings.os == "Windows":
            self.cpp_info.libs = tools.collect_libs(self)
        else:
            self.cpp_info.libs = ["icuio", "icui18n", "icuuc", "icudata"]
