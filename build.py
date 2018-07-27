# ICU Conan package
# Dmitriy Vetutnev, ODANT, 2018


import platform, os
from copy import deepcopy
from conan.packager import ConanMultiPackager


# Common settings
username = "odant" if "CONAN_USERNAME" not in os.environ else None
# Windows settings
visual_versions = ["14", "15"] if "CONAN_VISUAL_VERSIONS" not in os.environ else None
visual_runtimes = ["MD", "MDd"] if "CONAN_VISUAL_RUNTIMES" not in os.environ else None
visual_default_toolsets = {
    "14": [None, "v140_xp"],
    "15": [None, "v141_xp"]
}
visual_toolsets = None
if "CONAN_VISUAL_TOOLSETS" in os.environ:
    visual_toolsets = [s.strip() for s in os.environ["CONAN_VISUAL_TOOLSETS"].split(",")]
dll_sign = False if "CONAN_DISABLE_DLL_SIGN" in os.environ else True


def vs_get_toolsets(compiler_version):
    return visual_toolsets if not visual_toolsets is None else visual_default_toolsets.get(compiler_version)


def vs_add_toolset(builds):
    result = []
    for settings, options, env_vars, build_requires, reference in builds:
        toolsets = vs_get_toolsets(settings["compiler.version"])
        if toolsets is None or settings["compiler"] != "Visual Studio":
            result.append([settings, options, env_vars, build_requires, reference])
        else:
            for t in toolsets:
                settings = deepcopy(settings)
                settings["compiler.toolset"] = t
                result.append([settings, options, env_vars, build_requires, reference])
    return result


def add_dll_sign(builds):
    result = []
    for settings, options, env_vars, build_requires, reference in builds:
        options = deepcopy(options)
        options["icu:dll_sign"] = dll_sign
        result.append([settings, options, env_vars, build_requires, reference])
    return result


def filter_libcxx(builds):
    result = []
    for settings, options, env_vars, build_requires, reference in builds:
        if settings["compiler.libcxx"] == "libstdc++11":
            result.append([settings, options, env_vars, build_requires, reference])
    return result


if __name__ == "__main__":
    builder = ConanMultiPackager(
        username=username,
        visual_versions=visual_versions,
        visual_runtimes=visual_runtimes,
        exclude_vcvars_precommand=True
    )
    builder.add_common_builds(pure_c=False)
    # Adjusting build configurations
    builds = builder.items
    if platform.system() == "Windows":
        builds = vs_add_toolset(builds)
        builds = add_dll_sign(builds)
    if platform.system() == "Linux":
        builds = filter_libcxx(builds)
    # Replace build configurations
    builder.items = []
    for settings, options, env_vars, build_requires, _ in builds:
        builder.add(
            settings=settings,
            options=options,
            env_vars=env_vars,
            build_requires=build_requires
        )
    builder.run()
