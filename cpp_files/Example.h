#pragma once

#ifndef BASE_UNIT_EXAMPLE_H
#define BASE_UNIT_EXAMPLE_H

#include <Base/Sub/ICWrappers.h>

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
        Sub::ICreateFileA &createFileA,
        Sub::ICloseHandle &closeHandle,
        Sub::IWriteFile &writeFile) :
            m_createFileA(createFileA),
            m_closeHandle(closeHandle),
            m_writeFile(writeFile)
    {}

    void run() const;

private:
    Sub::ICreateFileA &m_createFileA;
    Sub::ICloseHandle &m_closeHandle;
    Sub::IWriteFile &m_writeFile;
};

#endif