#pragma once

#ifndef BASE_UNIT_MASTEREXAMPLE_H
#define BASE_UNIT_MASTEREXAMPLE_H

#include <Base/Sub/ICWrappers.h>

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
    MasterExample(Sub::IMasterCWrapper &master) : m_master(master)
    {}

    void run() const;

private:
    Sub::IMasterCWrapper &m_master;
};

#endif