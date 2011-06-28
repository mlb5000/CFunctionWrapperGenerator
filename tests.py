import os, shutil, subprocess, unittest, time, cfunctionwrapper

'''This test suite assumes Visual Studio for now'''
CPP_COMPILER = 'cl.exe /nologo'
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
    'userenv.lib'
    )#os.path.join(CPP_FILE_FOLDER, 'ExampleUnitTests.cpp'))
    
OBJ_FILES = (
    os.path.join(CPP_BUILD_FOLDER, 'main.obj'),
    os.path.join(CPP_BUILD_FOLDER, 'MasterExample.obj'),
    os.path.join(CPP_BUILD_FOLDER, 'Example.obj'),
    'userenv.lib'
    )#os.path.join(CPP_FILE_FOLDER, 'ExampleUnitTests.obj'))

TEST_EXE = os.path.join(CPP_BUILD_FOLDER, 'main.exe')

class TestGenerationCompilation(unittest.TestCase):

    def setUp(self):
        self.origwd = os.getcwd()
        try:
            shutil.move('src', 'src_old')
            shutil.rmtree('src_old', ignore_errors=True)
        except IOError:
            pass
            
        try:
            shutil.move('build', 'build_old')
            shutil.rmtree('build_old', ignore_errors=True)
        except IOError:
            pass
        os.mkdir('src')
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
            '--base_namespace=Base'])
        
        os.environ['INCLUDE'] = os.environ['INCLUDE'] + PATH_SEPARATOR + os.path.join(FILE_DIR, 'src')
        
        os.chdir('build')
        subprocess.check_call(CPP_COMPILER + ' ' + ' '.join(CPP_FILES))
        subprocess.check_call(CPP_LINKER + ' ' + ' '.join(OBJ_FILES))
        
        subprocess.check_call(TEST_EXE)
        
        self.assertTrue(open('testFile.txt', 'rt').read() == 'yay!!')
        self.assertTrue(open('masterTestFile.txt', 'rt').read() == 'hooray!!')

if __name__ == '__main__':
    unittest.main()