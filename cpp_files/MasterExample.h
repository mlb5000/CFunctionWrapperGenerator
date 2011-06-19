#pragma once

#ifndef BASE_UNIT_MASTEREXAMPLE_H
#define BASE_UNIT_MASTEREXAMPLE_H

#include <Base/ICWrappers.h>

namespace Base
{
    namespace Unit
    {
        class MasterExample;
    }
}

class Base::Unit::MasterExample
{
public:
    MasterExample(IMasterCWrapper &master) : m_master(master)
    {}

    void run() const;

private:
    IMasterCWrapper &m_master;
};

#endif