#pragma once

#ifndef BASE_UNIT_EXAMPLE_H
#define BASE_UNIT_EXAMPLE_H

#include <Base/ICWrappers.h>

namespace Base
{
    namespace Unit
    {
        class Example;
    }
}

class Base::Unit::Example
{
public:
    Example(
        ICreateFileA &createFileA,
        ICloseHandle &closeHandle,
        IWriteFile &writeFile) :
            m_createFileA(createFileA),
            m_closeHandle(closeHandle),
            m_writeFile(writeFile)
    {}

    void run() const;

private:
    ICreateFileA &m_createFileA;
    ICloseHandle &m_closeHandle;
    IWriteFile &m_writeFile;
};

#endif