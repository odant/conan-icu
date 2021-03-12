# Test Conan package
# Dmitriy Vetutnev, Odant 2019 - 2020


from conans import ConanFile, CMake


class PackageTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def isClangClToolset(self):
        return True if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio" and str(self.settings.compiler.toolset).lower() == "clangcl" else False

    def build_requirements(self):
        if not self.isClangClToolset():
            self.build_requires("ninja/[>=1.10.2]")

    def imports(self):
        self.copy("*.pdb", dst="bin", src="bin")
        self.copy("*.dll", dst="bin", src="bin")
        self.copy("*.so*", dst="bin", src="lib")

    def build(self):
        cmakeGenerator = "Ninja" if not self.isClangClToolset() else None
        cmake = CMake(self, generator=cmakeGenerator)
        cmake.verbose = True
        cmake.configure()
        cmake.build()
        self.cmake_is_multi_configuration = cmake.is_multi_configuration

    def test(self):
        if self.cmake_is_multi_configuration:
            self.run("ctest --verbose --build-config %s" % self.settings.build_type)
        else:
            self.run("ctest --verbose")

