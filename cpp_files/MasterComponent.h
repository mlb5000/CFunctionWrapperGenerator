#pragma once

#ifndef BASE_COMPONENT_MASTEREXAMPLE_H
#define BASE_COMPONENT_MASTEREXAMPLE_H

#include "MasterExample.h"
#include <Base/Sub/Component/Sub2/CWrappers.h>

namespace Base
{
    namespace Component
    {
        class MasterExample;
    }
}

class Base::Component::MasterExample
{
public:
    MasterExample() : m_unit(m_master) {}
    virtual ~MasterExample() {}
    
    void run() const { m_unit.run(); }
    
private:
    Base::Sub::Component::Sub2::MasterCWrapper m_master;
    
    Unit::MasterExample m_unit;
};

#endif