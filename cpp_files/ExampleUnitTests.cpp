#include "ExampleUnitTests.h"

using ::testing::Return;
using ::testing::_;
using ::testing::SetArgPointee;
using ::testing::SaveArg;

using namespace Base::Unit::Test;

const HANDLE FILE_HANDLE = reinterpret_cast<HANDLE>(0x12345);
void
Base::Unit::Test::ExampleUnitTests::SetUp()
{
    ON_CALL(m_masterMock, myCreateFileA(_, _, _, _, _, _, _))
        .WillByDefault(Return(FILE_HANDLE));
    
    DWORD size = 0;
    ON_CALL(m_masterMock, myWriteFile(FILE_HANDLE, _, _, _, _))
        .WillByDefault(
            DoAll(
                SaveArg<2>(&size),
                SetArgPointee<3>(size),
                Return(TRUE)));
        
    ON_CALL(m_masterMock, myCloseHandle(FILE_HANDLE))
        .WillByDefault(Return(TRUE));
}

TEST_F(ExampleUnitTests, ThrowsExceptionWhenCreateFileFails)
{
    EXPECT_CALL(m_masterMock, myCreateFileA(_, _, _, _, _, _, _))
        .WillRepeatedly(Return(INVALID_HANDLE_VALUE));
        
    ASSERT_THROW(m_unit.run(), std::exception);
}

TEST_F(ExampleUnitTests, ThrowsExceptionWhenWriteFileFails)
{
    EXPECT_CALL(m_masterMock, myWriteFile(FILE_HANDLE, _, _, _, _))
        .WillRepeatedly(Return(FALSE));
        
    ASSERT_THROW(m_unit.run(), std::exception);
}

TEST_F(ExampleUnitTests, ThrowsExceptionWhenWriteFileDoesntWriteEnoughBytes)
{
    DWORD size = 0;
    EXPECT_CALL(m_masterMock, myWriteFile(FILE_HANDLE, _, _, _, _))
        .WillRepeatedly(
            DoAll(
                SaveArg<2>(&size),
                SetArgPointee<3>(size-1),
                Return(TRUE)));
        
    ASSERT_THROW(m_unit.run(), std::exception);
}