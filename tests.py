import os, shutil, subprocess, cfunctionwrapper, unittest

'''This test suite assumes Visual Studio for now'''
CPP_COMPILER = 'cl.exe /nologo'
CPP_LINKER = 'link.exe /nologo'
FILE_DIR = os.path.dirname(os.path.abspath(__file__))
CPP_FILE_FOLDER = os.path.join(FILE_DIR, 'cpp_files')
CPP_BUILD_FOLDER = os.path.join(FILE_DIR, 'build')
PATH_SEPARATOR = ';' if os.name == 'nt' else ':'

CPP_FILES = (
    os.path.join(CPP_FILE_FOLDER, 'main.cpp'),
    os.path.join(CPP_FILE_FOLDER, 'Example.cpp'),
    )#os.path.join(CPP_FILE_FOLDER, 'ExampleUnitTests.cpp'))
    
OBJ_FILES = (
    os.path.join(CPP_BUILD_FOLDER, 'main.obj'),
    os.path.join(CPP_BUILD_FOLDER, 'Example.obj'),
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
        
        cfunctionwrapper.generate(
            'cfunctions.txt',
            include_path=os.environ['INCLUDE'],
            base_namespace='Base')
        
        os.environ['INCLUDE'] = os.environ['INCLUDE'] + PATH_SEPARATOR + os.path.join(FILE_DIR, 'src')
        
        os.chdir('build')
        subprocess.check_call(CPP_COMPILER + ' ' + ' '.join(CPP_FILES))
        subprocess.check_call(CPP_LINKER + ' ' + ' '.join(OBJ_FILES))
        
        subprocess.check_call(TEST_EXE)
        
        self.assertTrue(os.path.exists('testFile.txt'))

if __name__ == '__main__':
    unittest.main()