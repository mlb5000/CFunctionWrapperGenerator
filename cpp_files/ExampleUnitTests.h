#pragma once

#ifndef BASE_UNIT_TEST_EXAMPLEUNITTESTS_H
#define BASE_UNIT_TEST_EXAMPLEUNITTESTS_H

#include "Example.h"
#include <Base/Sub/Mock/Sub2/CWrappers.h>
#include <gtest/gtest.h>

namespace Base
{
    namespace Unit
    {
        namespace Test
        {
            class ExampleUnitTests;
        }
    }
}

class Base::Unit::Test::ExampleUnitTests : public ::testing::Test
{
protected:
    ExampleUnitTests() : m_unit(m_masterMock, m_masterMock, m_masterMock) {}
    virtual ~ExampleUnitTests() {}

    virtual void SetUp();
    
    ::testing::NiceMock<Base::Sub::Mock::Sub2::MasterCWrapper> m_masterMock;
    Example m_unit;
};

#endif