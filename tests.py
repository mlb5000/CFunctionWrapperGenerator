import os
import shutil
import subprocess
import unittest

'''This test suite assumes Visual Studio for now'''
CPP_COMPILER = 'cl.exe /nologo /EHsc /c'
CPP_LINKER = 'cl.exe /nologo'
FILE_DIR = os.path.dirname(os.path.abspath(__file__))
CPP_FILE_FOLDER = os.path.join(FILE_DIR, 'cpp_files')
CPP_BUILD_FOLDER = os.path.join(FILE_DIR, 'build')
PATH_SEPARATOR = ';' if os.name == 'nt' else ':'
PYTHON31 = 'python31'

CPP_FILES = (
    os.path.join(CPP_FILE_FOLDER, 'main.cpp'),
    os.path.join(CPP_FILE_FOLDER, 'MasterExample.cpp'),
    os.path.join(CPP_FILE_FOLDER, 'Example.cpp'),
    os.path.join(CPP_FILE_FOLDER, 'ExampleUnitTests.cpp'),
    os.path.join(CPP_FILE_FOLDER, 'TestMain.cpp'),
    
    os.path.join(FILE_DIR, 'gmock-1.6.0/src/gmock-all.cc'),
    
    os.path.join(FILE_DIR, 'gmock-1.6.0/gtest/src/gtest-all.cc'),
    )
    
OBJ_FILES = (
    os.path.join(CPP_BUILD_FOLDER, 'main.obj'),
    os.path.join(CPP_BUILD_FOLDER, 'MasterExample.obj'),
    os.path.join(CPP_BUILD_FOLDER, 'Example.obj'),
    'userenv.lib',
    )

TEST_OBJ_FILES = (
    os.path.join(CPP_BUILD_FOLDER, 'TestMain.obj'),
    os.path.join(CPP_BUILD_FOLDER, 'Example.obj'),
    os.path.join(CPP_BUILD_FOLDER, 'ExampleUnitTests.obj'),
    
    os.path.join(CPP_BUILD_FOLDER, 'gmock-all.obj'),
    os.path.join(CPP_BUILD_FOLDER, 'gtest-all.obj'),
    )

TEST_EXE = os.path.join(CPP_BUILD_FOLDER, 'main.exe')
UNIT_TEST_EXE = os.path.join(CPP_BUILD_FOLDER, 'TestMain.exe')

class TestGenerationCompilation(unittest.TestCase):

    def setUp(self):
        self.origwd = os.getcwd()
        try:
            shutil.rmtree('CWrappers', ignore_errors=True)
        except IOError:
            pass
            
        try:
            shutil.rmtree('build', ignore_errors=True)
        except IOError:
            pass
        os.mkdir('build')

    def tearDown(self):
        os.chdir(self.origwd)

    def test_CompileSingleWrapper(self):
        self.failUnless('INCLUDE' in os.environ, msg='''Please configure your compiler environment
        On Windows this might be something like running vsvars32.bat''')
        
        subprocess.check_call([
            PYTHON31,
            '-O',
            os.path.join(FILE_DIR, 'cfunctionwrapper.py'),
            'cfunctions.txt',
            '--base_namespace=Base::Sub',
            '--mock_namespace=Mock::Sub2',
            '--component_namespace=Component::Sub2'])
        
        os.environ['INCLUDE'] = PATH_SEPARATOR.join((
            os.environ['INCLUDE'],
            os.path.normpath(os.path.join(FILE_DIR, 'CWrappers')),
            os.path.normpath(os.path.join(FILE_DIR, 'gmock-1.6.0/include')),
            os.path.normpath(os.path.join(FILE_DIR, 'gmock-1.6.0')),
            os.path.normpath(os.path.join(FILE_DIR, 'gmock-1.6.0/gtest/include')),
            os.path.normpath(os.path.join(FILE_DIR, 'gmock-1.6.0/gtest')),
            ))
        
        os.chdir('build')
        subprocess.check_call(CPP_COMPILER + ' ' + ' '.join(CPP_FILES))
        subprocess.check_call(CPP_LINKER + ' ' + ' '.join(OBJ_FILES))
        subprocess.check_call(CPP_LINKER + ' ' + ' '.join(TEST_OBJ_FILES))
        
        print('')
        print('Verifying that the wrappers call real functions')
        subprocess.check_call(TEST_EXE)
        self.assertTrue(open('testFile.txt', 'rt').read() == 'yay!!')
        self.assertTrue(open('masterTestFile.txt', 'rt').read() == 'hooray!!')
        print('Done!')
        print('')
        
        print('Verifying unit tests can use mocks')
        subprocess.check_call(UNIT_TEST_EXE)
        print('Done!')

if __name__ == '__main__':
    unittest.main()