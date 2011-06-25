# C++ C-Function Wrapper Generator (CFWG)

##  Purpose

Dependency-injection in C++ is not convenient, especially when you bring "Free" C functions into the mix.  There are several approaches you can use to isolate these functions, but the one I've had the most success with is to create C++ classes whose sole purpose is to wrap calls to C functions.  This approach works quite well, both in minimizing the impact to the production while while also simplifying unit testing, particularly when paired with the [googlemock C++ Mocking framework](http://code.google.com/p/googlemock).

I've been doing this for some time and have started to feel some pain in the maintenance area.  Wrapper functions are starting to be duplicated between wrapper modules, and classes depending on wrappers are importing functions that they'll never call.  But most of all, building out and maintaining these wrapper classes takes time and is extremely tedious.  So being the lazy developer that I am, I wrote CFWG to do the heavy lifting for me.

##  Requirements

CFWG requires Python 3.X (namely the str.format function).

##  Usage

###  Generating the Wrappers

cfunctionwrapper.py Command-line Usage

    cfunctionwrapper.py functionList [-i include_path] [-n] [-b base_namespace] [-m mock_namespace] [-c component_namespace] [-p funcPrefix] [-s component_suffix] [-i base_include] [-t interface_dir] [-o component_dir] [-k mock_dir]

Precondition: The INCLUDE environment variable must be set

    function_file           [Required] Path to a file containing a list of C function names to wrap.  This file contains a
    number of lines in the format: 

    <function> <actual_header> <include_header>

    Function = The function you want to mock
    Actual Header = The header where the function prototype is actually located
    Include Header = The base header that you include to ultimately get at the function (can be the same as Actual Header)

    See the provided cfunctions.txt file for examples.

    include_path            [Default: The INCLUDE environment variable] Directories to search to find all the actual headers
                            if your <function_file>. This should be a list of directories separated by ';' on Windows or ':'
                            on Unix. If this option is not specified, the INCLUDE environment variable is used.

    -n = Disable generateGmock
    generateGmock           [Default: True] Whether or not to generate GMock style mock classes

    base_namespace          [Default: ''] Base class namespace

    mock_namespace          [Default: 'Mock'] Name of mock namespace. Fully qualified namespace will become
                             base_namespace::mock_namespace

    component_namespace     [Default: 'Component'] Name of component namespace. Fully qualified namespace will become
                            base_namespace::component_namespace

    funcPrefix              [Default: 'my'] Prefix to wrapper functions. This is used to prevent colliding with the wrapped
                            C function

    component_suffix        [Default: 'Wrapper'] Suffix that will be appended to class names of generated Component classes
                            as well as the IMasterC<suffix> master interface.

    base_include            [Default: 'src/Base'] Base include directory where generated wrappers will be stored

    interface_dir           [Default: ''] Directory (relative to base_include) where the ICWrappers interface file will be
                            written

    component_dir           [Default: 'Component'] Directory (relative to base_include) where the component CWrappers file
                            should be written

    mock_dir                [Default: 'Mock'] Directory (relative to base_include) where the mock CWrappers file should be
                            written. Must be different than component_dir.

### Using the Wrappers

So you have your C functions tidily wrapped up into a few files, now what?  First, to really make your C++ classes testable with the wrappers, you'll need to update your class' to constructor (or whatever other dependency-injection mechanism you have) to take in references to the interface(s) containing C functions you care about.  For example, in the provided test example the class depends on three C functions: CreateFileA, WriteFile, and CloseHandle.  By providing these to CFWG three interfaces are created, ICreateFileA, IWriteFile, and ICloseHandle.  There is also an IMasterCWrapper interface and corresponding MasterCWrapper component generated, but they are more for convenience during unit testing and I wouldn't recommend having your classes depend on IMasterCWrapper, particlarly for shared libraries where not all linkage may be necessary for all users.

So how does this look?

_Unit/Foo.h_

    #include <ICWrappers.h>
    
    /* Unit class (has dependencies) */
    class Unit::Foo
    {
    public:
        Foo(ICreateFileA &createFileA, IWriteFile &writeFile, ICloseHandle &closeHandle)
            : m_createFileA(createFileA), m_writeFile(writeFile), m_closeHandle(closeHandle)
        {}
        
        void bar();
        
    private:
        ICreateFileA &m_createFileA;
        IWriteFile &m_writeFile;
        ICloseHandle &m_closeHandle;
    };

_Component/FooIndividual.h_

    #include <Component/CWrappers.h>
    
    /* Component class (provides dependencies through individual linkage) */
    class Component::FooIndividual
    {
    public:
        Foo() : m_unit(m_createFileA, m_writeFile, m_closeHandle)
        
    private:
        CreateFileAWrapper m_createFileA;
        WriteFileWrapper m_writeFile;
        CloseHandleWrapper m_closeHandle;
        
        Unit::Foo m_unit;
    };

_Component/FooMaster.h_

    #include <Component/CWrappers.h>
    
    /* Component class (provides dependencies through master wrapper) */
    class Component::FooMaster
    {
    public:
        Foo() : m_unit(m_master, m_master, m_master)
        
    private:
        MasterCWrapper m_master;
        
        Unit::Foo m_unit;
    };

**Note**: you would typically only use one pattern, either Individual or Master in your injection, not both.

Now, Foo.bar() can just call its C functions through the interfaces

_Unit/Foo.cpp_

    #include <Unit/Foo.h>
    
    void
    Unit::Foo::Bar()
    {
        HANDLE handle = m_createFileA.myCreateFileA(
            "testFile.txt",
            GENERIC_WRITE,
            0,
            0,
            CREATE_NEW,
            FILE_ATTRIBUTE_NORMAL,
            0);
        if (INVALID_HANDLE_VALUE == handle)
        {
            throw std::exception("CreateFileA failed!");
        }
        
        const char *toWrite = "yay!!";
        DWORD numBytesWritten = 0;
        if (!m_writeFile.myWriteFile(
            handle,
            toWrite,
            strlen(toWrite),
            &numBytesWritten,
            0) || numBytesWritten != strlen(toWrite))
        {
            m_closeHandle.myCloseHandle(handle);
            throw std::exception("WriteFile failed!");
        }
        
        m_closeHandle.myCloseHandle(handle);
    }

and your unit tests for Unit::Foo can now control interactions between it and the C functions it depends on.

## Limitations

CFWG relies on the cppcheck AST parser to parse the C headers.  It's pretty good, but it's perfect and may choke on some files.  If you see an error like: *'I did my best, but I can go no further. Hopefully the collected functions are sufficient for your needs'* it means that the parser failed on something, but that some symbols were collected.  Hopefully the function prototypes you wished to wrap we successfully collected.  If not, submit a bug report and we'll see what we can do.