#include "Example.h"
#include <exception>

void
Base::Unit::Example::run() const
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