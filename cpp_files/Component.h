#pragma once

#ifndef BASE_COMPONENT_EXAMPLE_H
#define BASE_COMPONENT_EXAMPLE_H

#include "Example.h"
#include <Base/Component/CWrappers.h>

namespace Base
{
    namespace Component
    {
        class Example;
    }
}

class Base::Component::Example
{
public:
    Example() : m_unit(m_createFileA, m_closeHandle, m_writeFile) {}
    virtual ~Example() {}
    
    void run() const { m_unit.run(); }
    
private:
    Base::Component::CreateFileAWrapper m_createFileA;
    Base::Component::CloseHandleWrapper m_closeHandle;
    Base::Component::WriteFileWrapper m_writeFile;
    
    Unit::Example m_unit;
};

#endif