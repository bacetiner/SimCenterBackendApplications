add_subdirectory(data)
simcenter_add_executable(NAME MDOF-LU
                         FILES MDOF-LU.cpp InterstoryParam.cpp HazusSAM_Generator.cpp FloorParam.cpp Building.cpp whereami.c
                         DEPENDS CONAN_PKG::jansson common)
