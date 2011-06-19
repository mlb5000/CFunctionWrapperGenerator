#include "MasterExample.h"
#include <exception>

void
Base::Unit::MasterExample::run() const
{
    HANDLE handle = m_master.myCreateFileA(
        "masterTestFile.txt",
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
    
    const char *toWrite = "hooray!!";
    DWORD numBytesWritten = 0;
    if (!m_master.myWriteFile(
        handle,
        toWrite,
        strlen(toWrite),
        &numBytesWritten,
        0) || numBytesWritten != strlen(toWrite))
    {
        m_master.myCloseHandle(handle);
        throw std::exception("WriteFile failed!");
    }
    
    m_master.myCloseHandle(handle);
}