# C++ C-Function Wrapper Generator (CFWG)

##  Purpose

Dependency-injection in C++ is not convenient, especially when you bring "Free" C functions into the mix.  There are several approaches you can use to isolate these functions, but the one I've had the most success with is to create C++ classes whose sole purpose is to wrap calls to C functions.  This approach works quite well, particularly when paired with the "googlemock":http://code.google.com/p/googlemock/ C++ Mocking framework.

I've been doing this for some time and have started to feel some pain in the maintenance area.  Wrapper functions are starting to be duplicated between wrapper modules, and classes depending on wrappers are importing functions that they'll never call.  But most of all, building out and maintaining these wrapper classes takes time and is extremely tedious.  So being the lazy developer that I am, I wrote CFWG to do the heavy lifting for me.

##  Requirements

CFWG requires Python 3.X (namely the str.format function).

##  Usage

###  Generating the Wrappers

cfunctionwrapper.py Command-line Usage

cfunctionwrapper.py functionList [-i include_path] [-n] [-b base_namespace] [-m mock_namespace] [-c component_namespace] [-p funcPrefix] [-s component_suffix] [-i base_include] [-t interface_dir] [-o component_dir] [-k mock_dir]

Precondition: The INCLUDE environment variable must be set

    -n = Disable generateGmock

    function_file           [Required] Path to a file containing a list of C function names to wrap.  This file contains a
    number of lines in the format: 

    <function> <actual_header> <include_header>

    Function = The function you want to mock
    Actual Header = The header where the function prototype is actually located
    Include Header = The base header that you include to ultimately get at the function (can be the same as Actual Header)

    See the provided cfunctions.txt file for examples.

    include_path            [Default: The INCLUDE environment variable] C compiler include path.  This should be a list of
                            directories separated by ';' on Windows and ':' on Unix

    generateGmock           [Default: True] Whether or not to generate GMock style mock classes

    base_namespace          [Default: ''] Base class namespace

    mock_namespace          [Default: 'Mock'] Name of mock namespace. Fully qualified namespace will become
                             base_namespace::mock_namespace

    component_namespace     [Default: 'Component'] Name of component namespace. Fully qualified namespace will become
                            base_namespace::component_namespace

    funcPrefix              [Default: 'my'] Prefix to wrapper functions. This is used to prevent colliding with the wrapped
                            C function

    component_suffix        [Default: 'Wrapper'] Suffix that will be appended to class names of generated Component classes

    base_include            [Default: 'src/Base'] Base include directory where generated wrappers will be stored

    interface_dir           [Default: ''] Directory (relative to base_include) where the ICWrappers interface file will be
                            written

    component_dir           [Default: 'Component'] Directory (relative to base_include) where the component CWrappers file
                            should be written

    mock_dir                [Default: 'Mock'] Directory (relative to base_include) where the mock CWrappers file should be
                            written. Must be different than component_dir.

h2.  Limitations

p. The cppcheck Parser is not perfect and may choke on some files.  If you see an error like: _'I did my best, but I can go no further. Hopefully the collected functions are sufficient for your needs'_ it means that the parser failed on something, but that some symbols were collected.  Hopefully the function prototypes you wished to wrap are included.  If not, submit a bug report and we'll see what we can do.