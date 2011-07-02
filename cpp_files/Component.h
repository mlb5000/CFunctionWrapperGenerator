#pragma once

#ifndef BASE_COMPONENT_EXAMPLE_H
#define BASE_COMPONENT_EXAMPLE_H

#include "Example.h"
#include <Base/Sub/Component/Sub2/CWrappers.h>

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
    Sub::Component::Sub2::CreateFileAWrapper m_createFileA;
    Sub::Component::Sub2::CloseHandleWrapper m_closeHandle;
    Sub::Component::Sub2::WriteFileWrapper m_writeFile;
    
    Unit::Example m_unit;
};

#endif