# ICU Conan package
# Dmitriy Vetutnev, ODANT 2018


from conans import ConanFile, tools
from conans.errors import ConanException
import os, glob


def get_safe(options, name):
    try:
        return getattr(options, name, None)
    except ConanException:
        return None


class ICUConan(ConanFile):
    name = "icu"
    version = "62.1"
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
    exports_sources = "src/*", "FindICU.cmake"
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
            toolset = str(self.settings.compiler.get_safe("toolset"))
            if toolset.endswith("_xp"):
                self.build_requires("find_sdk_winxp/[>=1.0]@%s/stable" % self.user)
        if get_safe(self.options, "dll_sign"):
            self.build_requires("windows_signtool/[>=1.0]@%s/stable" % self.user)

    def source(self):
        if not tools.os_info.is_windows:
            self.run("chmod a+x %s" % os.path.join(self.source_folder, "src/source/configure"))

    def build(self):
        flags = self.get_build_flags()
        install_folder = os.path.join(self.build_folder, "icu_install").replace("\\", "/")
        flags.append("--prefix=%s" % tools.unix_path(install_folder))
        build_env = self.get_build_environment()
        with tools.chdir("src/source"), tools.environment_append(build_env):
            if self.settings.os == "Windows":
                self.run("echo %PATH%")
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
            "--disable-static",
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
            if tools.get_env("VisualStudioVersion") is not None:
                self.output.warn("vcvars already set, skip")
                #
                self.output.warn("Shift Cygwin path to end")
                path_lst = os.environ["PATH"].split(os.pathsep)
                cygwin_path = self.deps_env_info["cygwin_installer"].path[0]
                path_lst.remove(cygwin_path)
                path_lst.append(cygwin_path)
                os.environ["PATH"] = os.pathsep.join(path_lst)
            else:
                env = tools.vcvars_dict(self.settings, filter_known_paths=False, force=True)
                toolset = str(self.settings.compiler.get_safe("toolset"))
                if toolset.endswith("_xp"):
                    import find_sdk_winxp
                    env = find_sdk_winxp.dict_append(self.settings.arch, env=env)
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
        # Sign DLL
        if get_safe(self.options, "dll_sign"):
            import windows_signtool
            pattern = os.path.join(self.package_folder, "bin", "*.dll")
            for fpath in glob.glob(pattern):
                fpath = fpath.replace("\\", "/")
                for alg in ["sha1", "sha256"]:
                    is_timestamp = True if self.settings.build_type == "Release" else False
                    cmd = windows_signtool.get_sign_command(fpath, digest_algorithm=alg, timestamp=is_timestamp)
                    self.output.info("Sign %s" % fpath)
                    self.run(cmd)

    def package_id(self):
        # ICU unit testing shouldn't affect the package's ID
        self.info.options.with_unit_tests = "any"

    def package_info(self):
        self.cpp_info.defines = ["U_DISABLE_RENAMING=1"]
        if self.settings.os == "Windows":
            self.cpp_info.libs = tools.collect_libs(self)
        else:
            self.cpp_info.libs = ["icuio", "icui18n", "icuuc", "icudata"]

