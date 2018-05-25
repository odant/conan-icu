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
    exports_sources = "src/*"
    no_copy_source = False
    build_policy = "missing"

    def configure(self):
        if self.settings.compiler.get_safe("libcxx") == "libstdc++":
            raise Exception("This package is only compatible with libstdc++11")

    def build_requirements(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.build_requires("cygwin_installer/2.9.0@bincrafters/stable")
            self.build_requires("find_sdk_winxp/[~=1.0]@%s/stable" % self.user)

    def build(self):
        flags = self.get_build_flags()
        build_env = self.get_build_environment()
        with tools.chdir("src/source"), tools.environment_append(build_env):
            self.run("bash -C runConfigureICU %s" % " ".join(flags))
            cpu_count = tools.cpu_count() if self.settings.compiler != "Visual Studio" else "1"
            self.run("make -j %s" % cpu_count)

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
            "--with-data-packaging=library",
            "--disable-samples",
            "--prefix=%s" % self.package_folder
        ])
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
        return
        # CMake scripts
        self.copy("FindGTest.cmake", dst=".", src=".", keep_path=False)
        self.copy("FindGMock.cmake", dst=".", src=".", keep_path=False)
        # Headers
        self.copy("*.h", dst="include", src="src/googletest/include", keep_path=True)
        self.copy("*.h", dst="include", src="src/googlemock/include", keep_path=True)
        # Libraries
        self.copy("*.a", dst="lib", keep_path=False)
        self.copy("*.lib", dst="lib", keep_path=False)
        # PDB
        self.copy("*gtest.pdb", dst="bin", keep_path=False)
        self.copy("*gmock.pdb", dst="bin", keep_path=False)
        self.copy("*gtest_main.pdb", dst="bin", keep_path=False)
        self.copy("*gmock_main.pdb", dst="bin", keep_path=False)
        self.copy("*gtestd.pdb", dst="bin", keep_path=False)
        self.copy("*gmockd.pdb", dst="bin", keep_path=False)
        self.copy("*gtest_maind.pdb", dst="bin", keep_path=False)
        self.copy("*gmock_maind.pdb", dst="bin", keep_path=False)

    def package_info(self):
        pass
