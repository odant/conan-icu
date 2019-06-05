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
    version = "64.2"
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
        "with_unit_tests": [True, False],
        "shared": [True, False]
    }
    default_options = "dll_sign=True", "with_unit_tests=False", "shared=True"
    exports_sources = "src/*", "FindICU.cmake", "msvc_mt.patch"
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
        if get_safe(self.options, "dll_sign"):
            self.build_requires("windows_signtool/[>=1.0]@%s/stable" % self.user)

    def source(self):
        tools.patch(patch_file="msvc_mt.patch")
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
            "--with-library-bits=%s" % {"x86": "32", "x86_64": "64", "mips": "32"}.get(str(self.settings.arch)),
            "--disable-renaming",
            "--disable-samples",
            "--srcdir=%s" % os.path.join(self.build_folder, "src/source")
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
            if self.settings.compiler.runtime == "MT" or self.settings.compiler.runtime == "MTd":
                return "Cygwin/MSVC_MT"
            else:
                return "Cygwin/MSVC"
        elif self.settings.os == "Linux" and self.settings.compiler == "gcc":
            return "Linux/gcc"
        else:
            raise Exception("Unsupported target platform!")

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

