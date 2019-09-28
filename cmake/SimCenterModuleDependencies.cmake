######################################################################################################################
#   PLEASE NOTE:
#   The functionality below is taken from the CMake configuration in waLBerla (https://www.walberla.net/)
#   and has been modified and simplified to build SimCenter backend applications.
######################################################################################################################

#######################################################################################################################
#
# This file contains functions that are used by SimCenterFunctions.cmake.
# The user typically only needs the functions in SimCenterFunctions.cmake
##
# Here is an explanation of the SimCenter module mechanism:        
#  - One folder with a CMakeLists.txt that is a subfolder of one of the directories listed in the variable
#    SIMCENTER_MODULE_DIRS can be a module
#  - the name of the module is the path relative to a SIMCENTER_MODULE_DIRS entry
#  - SimCenter modules are all placed in the modules subdirectory, so SIMCENTER_MODULE_DIRS
#    contains ${CMAKE_CURRENT_SOURCE_DIR}/modules/
#  - to create a module call simcenter_add_module() inside this folder
#  - this creates a static library that has the same name as the module, but slashes are replaced by minuses.
#    In case the module contains only header files no static lib is generated, only a custom target is added
#    to display the module in Visual Studio.
#  - simcenter_add_module takes a list of dependent modules. A second list of dependencies is generated by parsing
#    all files in the module for corresponding "#include" lines. This mechanism is not a complete preprocessor
#    and therefore has problems with #ifdef's etc
#    If you forgot to specify a dependency that is detected via this mechanism a warning is printed.
#  - The dependency list is used to store a dependency graph via the SIMCENTER_MODULE_DEPENDS_* variables
#    see simcenter_register_dependency and simcenter_resolve_dependencies
#  - To add modules (i.e. module libraries ) to an application use target_link_modules
#    which uses the stored module graph to find all dependent modules
#
# The module dependencies are explicitly tracked, instead of using cmake's 
# native mechanism target_link_libraries because of the following reasons:
#  - All modules can be built in parallel
#  - Handling of header only modules
#  - dependencies of folders that are on the same level in directory hierarchy
#######################################################################################################################

#######################################################################################################################
#
# Determine Module name using the current folder 
# 
# moduleFolder is the current source directory relative to a folder in SIMCENTER_MODULE_DIRS
# If more arguments are given, these are prepended to SIMCENTER_MODULE_DIR
# Example:
#    If CMAKE_CURRENT_SOURCE_DIR is /modules/createEVENT and /modules/ is an element in SIMCENTER_MODULE_DIRS,
#    then module name is "createEVENT"
#
#######################################################################################################################
function(get_current_module_name  moduleNameOut)

    foreach(moduleDir ${ARGN} ${SIMCENTER_MODULE_DIRS})
        get_filename_component(moduleNameShort ${CMAKE_CURRENT_SOURCE_DIR} NAME_WE)
        file(RELATIVE_PATH moduleFolder ${moduleDir} ${CMAKE_CURRENT_SOURCE_DIR})
        if (NOT ${moduleFolder} MATCHES "\\.\\./.*")
           set (${moduleNameOut} ${moduleFolder} PARENT_SCOPE)
           return() 
        endif()
    endforeach()
    
    message (WARNING "Called get_current_module_name, in a directory "
                     "that is not a subdirectory of SIMCENTER_MODULE_DIRS\n"
                     "Module Dirs: ${SIMCENTER_MODULE_DIRS} \n"
                     "Current Dir: ${CMAKE_CURRENT_SOURCE_DIR}")
    

endfunction(get_current_module_name)
#######################################################################################################################

#######################################################################################################################
#
# Determine Module folder using the current folder. moduleFolderOut is the current source directory stripped of
# the path
#
#######################################################################################################################
function(get_current_module_dir moduleFolderOut)
  
  foreach(moduleDir ${ARGN} ${SIMCENTER_MODULE_DIRS})
    get_filename_component(moduleFolderPath ${CMAKE_CURRENT_SOURCE_DIR} DIRECTORY)    
    file(RELATIVE_PATH moduleFolder ${moduleDir} ${CMAKE_CURRENT_SOURCE_DIR})
    if (NOT ${moduleFolder} MATCHES "\\.\\./.*")
      get_filename_component(moduleFolderDir ${moduleFolderPath} NAME_WE)      
      set (${moduleFolderOut} ${moduleFolderDir} PARENT_SCOPE)
      return() 
    endif()
  endforeach()

  message (WARNING "Called get_current_module_name, in a directory "
           "that is not a subdirectory of SIMCENTER_MODULE_DIRS\n"
           "Module Dirs: ${SIMCENTER_MODULE_DIRS} \n"
           "Current Dir: ${CMAKE_CURRENT_SOURCE_DIR}")
      

endfunction(get_current_module_dir)

#######################################################################################################################
#
# Since slashes occur in module names, but slashes are not allowed in library names
# the library name is the module name, where all slashes are replaced by dashes
#
#######################################################################################################################

function(get_module_library_name libraryNameOut moduleName)
    STRING(REPLACE "/" "-" libraryName ${moduleName})
    
    set(${libraryNameOut} ${libraryName} PARENT_SCOPE)
    
endfunction(get_module_library_name) 
#######################################################################################################################

#######################################################################################################################
# 
# Registers a dependency between modules
# 
# Example: simcenter_register_dependency( m1 m2 m3 m4)
#          registers a dependency of m1 to m2, m3 and m4
# 
# See also simcenter_resolve_dependencies()
# 
#######################################################################################################################

function(simcenter_register_dependency moduleName)
    
    get_module_library_name(moduleLibraryName ${moduleName})
    
    # use the library name as part of the variable name
    set(SIMCENTER_MODULE_DEPENDS_${moduleLibraryName} ${ARG_DEPENDS} 
          CACHE INTERNAL "All modules that depend on ${moduleName}" FORCE)

endfunction(simcenter_register_dependency)

#######################################################################################################################

#######################################################################################################################
# 
# Returns a list of all dependencies (transitively) of a given set of modules
#
# Example:
#   simcenter_register_dependency ( A  B  C  )      # A depends on B and C
#   simcenter_register_dependency ( F  D    )      # F depends on D
#   simcenter_register_dependency ( D  A    )      # cyclic dependencies are allowed  
#   simcenter_resolve_dependencies( outlist  A F ) # outlist is now A F B C D 
#
# See also: simcenter_register_dependency
# 
#######################################################################################################################

function(simcenter_resolve_dependencies outputList )
    
    set(dependencyList ${ARGN})
    
    set(newDependencyFound 0)
    
    foreach(module ${dependencyList})
        foreach(depModule ${SIMCENTER_MODULE_DEPENDS_${module}})
            get_module_library_name(depModLibraryName ${depModule})
            list(FIND dependencyList ${depModLibraryName} found)
            if(found LESS 0)
                list( APPEND dependencyList ${depModLibraryName})
                set(newDependencyFound 1)
            endif()      
        endforeach()
    endforeach()

    if(newDependencyFound)
        simcenter_resolve_dependencies(dependencyList ${dependencyList})
    endif()

    set(${outputList} ${dependencyList} PARENT_SCOPE)

endfunction(simcenter_resolve_dependencies)

# Testcase:
# simcenter_register_dependency ( A "B" )
# simcenter_register_dependency ( B "C" "F")
# simcenter_register_dependency ( C "D")
# simcenter_register_dependency ( F "A" )

# simcenter_resolve_dependencies ( out "A" ) 
# message ( STATUS "Resolve Dependencies testcase ${out}" ) # should print A;B;C;F;D

#######################################################################################################################

#######################################################################################################################
#
# Links a list of modules to a given target
#
# - Translates module names to library names
# - links transitively all modules that depend on given modules
# 
#######################################################################################################################

function(target_link_modules target)

    set(libs)
    foreach(module ${ARGN})
       get_module_library_name(libraryName ${module})
       list(APPEND libs ${libraryName})
    endforeach()
        
    simcenter_resolve_dependencies(libs ${libs})
        
    # The linker needs the modules in the correct order depending on their
    # dependencies. We would have to do a topological sorting here, instead
    # we specify all libs twice -> Could be improved -> faster linking times
    set(libs ${libs} ${libs} ${libs})
    
    foreach(libraryName ${libs})
        if( TARGET ${libraryName}) 
     	   get_target_property( target_type ${libraryName} TYPE) 
     	   if( ${target_type} MATCHES LIBRARY) 
     	      target_link_libraries( ${target} ${SIMCENTER_LINK_LIBRARIES_KEYWORD} ${libraryName})
     	   endif()                    
     	endif() 
    endforeach()
        
endfunction(target_link_modules)
#######################################################################################################################

#######################################################################################################################
# If path contains a CMakeLists.txt, path is returned
# otherwise recursivly the parent directories are checked and returned if they contain a CMakeLists.txt
#######################################################################################################################
    
function(get_parent_with_cmakelists result dir)
    set(${result} NOTFOUND PARENT_SCOPE)
    if(EXISTS ${dir})     
        if(EXISTS "${dir}/CMakeLists.txt")
            set(${result} ${dir} PARENT_SCOPE)
        else()
            get_filename_component( dir ${dir} PATH)
            get_parent_with_cmakelists( res ${dir})
            set(${result} ${res} PARENT_SCOPE)    
        endif()
    endif()
endfunction(get_parent_with_cmakelists)
#######################################################################################################################

#######################################################################################################################
#
# Checks the dependencies of the given files 
# 
# Example: get_dependencies(outList "sourceFile1.cpp" "sourceFile2.cpp")
#
# First the files are read and all "#include" lines are inspected. Then it is checked
# if the included file is in ${CMAKE_CURRENT_SOURCE_DIR}/modules
# 
# The module-name is defined as the part of the path that come after "modules/". 
# If a source file has the following line "#include "core/subModuleName/someFile.cpp"
# a dependency to the modules "core/subModuleName" is detected.
#
# Warning: the detection mechanism is not a full preprocessor, therefore it has problems with:
#     #ifdef SOME_VAR
#     #include "core/subModuleName/someFile.cpp"
#     #endif
# Here there would also be detected a module dependency, even if SOME_VAR is not set.
# 
#######################################################################################################################

function(get_dependencies dependentModulesOut)
  foreach(sourceFile ${ARGN})
  
      if(EXISTS ${sourceFile}) # guard for generated headers
          
          file(STRINGS ${sourceFile} includes REGEX "[ ]*#[ ]*include.*")
          foreach(includeLine ${includes})
              # Skip comments
              if(NOT ${includeLine} MATCHES "[ ]*//.*")
                  # Extract the filename from the include ( stripping off "" and <>)
                  string(REGEX REPLACE "[ ]*#[ ]*include[ ][<\"]+(.*)[\">]" "\\1" includedFile "${includeLine}")
                                    
                  # check if included file is from SimCenterBackendApplications/modules directory
                  foreach(modulePath ${SIMCENTER_MODULE_DIRS})
                      if(EXISTS ${modulePath}/${includedFile}  AND NOT IS_DIRECTORY ${modulePath}/${includedFile})
                          get_parent_with_cmakelists( parent "${modulePath}/${includedFile}")
                          file(RELATIVE_PATH dependentModule ${modulePath} ${parent})
                                                    
                          list(APPEND dependentModules ${dependentModule} )
                      endif()  
                  endforeach()  
              endif()                        
          endforeach()
      endif()
  endforeach()
  
  if( dependentModules)
     list(REMOVE_DUPLICATES dependentModules)
  endif()
  
  set(${dependentModulesOut} ${dependentModules} PARENT_SCOPE)
endfunction()
#######################################################################################################################

#######################################################################################################################
#
# Checks that the module has only dependencies to the specified modules
# 
# Examples:
#    check_dependencies( missingDeps additionalDeps FILES field/Communication.h  EXPECTED_DEPS core field) 
#
#######################################################################################################################

function(check_dependencies missingDepsOut additionalDepsOut )
    set(options)
    set(oneValueArgs)
    set(multiValueArgs FILES EXPECTED_DEPS)
    cmake_parse_arguments( ARG "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    get_dependencies(computedDeps ${ARG_FILES})
    set(expectedDeps ${ARG_EXPECTED_DEPS})
        
    # missingDepOut is(computedDeps - expectedDeps)
    set(missingDeps ${computedDeps})
    
    if(missingDeps)
        foreach(element ${expectedDeps})
            list(REMOVE_ITEM missingDeps ${element})
        endforeach()
    endif()
    set(${missingDepsOut} ${missingDeps} PARENT_SCOPE)
    
    # additionalDepOut is (expectedDeps - computedDeps)
    set(additionalDeps ${expectedDeps})   
    if( expectedDeps)
        foreach(element ${computedDeps})
            list(REMOVE_ITEM additionalDeps ${element})
        endforeach()
    endif()
    set(${additionalDepsOut} ${additionalDeps} PARENT_SCOPE)  
    
    
endfunction(check_dependencies)
#######################################################################################################################