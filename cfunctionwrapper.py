import loadpath
import os
import sys
import texttemplates
import glob
import subprocess
import re
import getopt
from pycparser import parse_file
from pycparser import c_parser
from pycparser import c_ast
from pycparser import plyparser

PATH_SEPARATOR = ';' if os.name == 'nt' else ':'

USAGE = 'Usage:\n\n' + __file__ + ''' functionList [-i include_path] [-n] [-b base_namespace]
        [-m mock_namespace] [-c component_namespace] [-p funcPrefix]
        [-s component_suffix] [-i base_include] [-t interface_dir]
        [-o component_dir] [-k mock_dir]'''

DESCRIPTION = '''
Generate C++ C-function wrapper classes

PRE: The INCLUDE environment variable must be set

-n = Disable generateGmock

function_file           [Required] Path to a file containing a list of C function
                        names to wrap
include_path            [Default: The INCLUDE environment variable] C compiler
                        include path.  This should be a list of directories
                        separated by ';' on Windows and ':' on Unix
generateGmock           [Default: True] Whether or not to generate GMock style
                        mock classes
base_namespace          [Default: ''] Base class namespace
mock_namespace          [Default: 'Mock'] Name of mock namespace. Fully qualified
                        namespace will become base_namespace::mock_namespace
component_namespace     [Default: 'Component'] Name of component namespace. Fully
                        qualified namespace will become
                        base_namespace::component_namespace
funcPrefix              [Default: 'my'] Prefix to wrapper functions. This is used
                        to prevent colliding with the wrapped C function
component_suffix        [Default: 'Wrapper'] Suffix that will be appended to class
                        names of generated Component classes
base_include            [Default: 'src/Base'] Base include directory where generated
                        wrappers will be stored
interface_dir           [Default: ''] Directory (relative to base_include) where
                        the ICWrappers interface file will be written
component_dir           [Default: 'Component'] Directory (relative to base_include)
                        where the component CWrappers file should be written to
mock_dir                [Default: 'Mock'] Directory (relative to base_include) where
                        the mock CWrappers file should be written to.  Must be
                        different than component_dir.
'''
def generate(function_file, include_path = '', generateGmock=True, base_namespace = '', mock_namespace = 'Mock', component_namespace = 'Component', funcPrefix='my', component_suffix = 'Wrapper', base_include = 'src/Base', interface_dir='', component_dir='Component', mock_dir='Mock'):
    if include_path == '':
        include_path = getIncludeEnvVar()
    
    full_interface_dir = os.path.normpath(os.path.join(base_include, interface_dir))
    full_component_dir = os.path.normpath(os.path.join(base_include, component_dir))
    full_mock_dir = os.path.normpath(os.path.join(base_include, mock_dir))
    
    mkdirIfNotExist(base_include)
    mkdirIfNotExist(full_interface_dir)
    mkdirIfNotExist(full_component_dir)
    
    if generateGmock:
        mkdirIfNotExist(full_mock_dir)
        
    functionsToWrap = getFunctions(function_file)
    print('Parsing files')
    prototypes, found_files = getFunctionASTs(include_path, functionsToWrap)
    
    interface_classes = ''
    mock_classes = ''
    component_classes = ''
    
    print('Generating wrappers')
    for prototype in prototypes:
        interface_classes += generateInterface(prototype, base_namespace, funcPrefix)
        component_classes += generateComponent(prototype, base_namespace, component_namespace, funcPrefix, component_suffix)
        if generateGmock:
            mock_classes += generateMock(prototype, base_namespace, funcPrefix)
    
    print('Generating master interface')
    interface_classes += generateMasterInterface(prototypes, base_namespace)
    print('Generating master wrapper component')
    component_classes += generateMasterWrapper(prototypes, base_namespace, component_namespace, funcPrefix, component_suffix)
    
    interface_file = os.path.join(full_interface_dir, 'ICWrappers.h')
    print('Generating interface file {0}'.format(interface_file))
    with open(interface_file, 'wt') as file:
        file.write(texttemplates.INTERFACE_FILE_TEMPLATE.format(
            base_namespace,
            interface_classes,
            getClassDefinitions(prototypes),
            getIncludes(found_files)))
    
    component_file = os.path.join(full_component_dir, 'CWrappers.h')
    print('Generating component file {0}'.format(component_file))
    with open(component_file, 'wt') as file:
        file.write(texttemplates.COMPONENT_FILE_TEMPLATE.format(
            base_namespace,
            getIncludes(found_files),
            component_classes,
            getNamespaceHierarchy(
                prototypes,
                getFullyQualifiedName((base_namespace, component_namespace)),
                component_suffix)))
    
    if not generateGmock:
        return
    
    mock_file = os.path.join(full_mock_dir, 'CWrappers.h')
    print('Generating mock file {0}'.format(mock_file))
    with open(mock_file, 'wt') as file:
        file.write(texttemplates.GMOCK_FILE_TEMPLATE.format(
            base_namespace,
            mock_classes))
    
    print('Done!')

def generateMasterWrapper(prototypes, base_namespace, component_namespace, funcPrefix, component_suffix):
    functions = ''
    
    for prototype in prototypes:
        functions += texttemplates.COMPONENT_FUNCTION_TEMPLATE.format(
            prototype.return_type(),
            funcPrefix,
            prototype.function_name(),
            getArgs(prototype),
            'const',
            getArgNames(prototype))
        functions += '    '
    
    className = 'MasterCWrapper'
    
    return texttemplates.INHERITING_CLASS_TEMPLATE.format(
        getFullyQualifiedName((base_namespace, component_namespace, className)),
        getFullyQualifiedName((base_namespace, 'I' + className)),
        functions,
        className)

def generateMasterInterface(prototypes, base_namespace):
    wrappers = []
    
    for p in prototypes:
        wrappers.append('I' + p.function_name())
    
    className = 'IMasterCWrapper'
    
    return texttemplates.INHERITING_CLASS_TEMPLATE.format(
        getFullyQualifiedName((base_namespace, className)),
        ',\n    public '.join(wrappers),
        '',
        className)

def getNamespaceHierarchy(prototypes, hierarchy, component_suffix):
    namespaces = hierarchy.split('::')
    ns_template = 'namespace {0}\n'
    class_template = 'class {0};'.format('{0}' + component_suffix)
    hierarchy = ''
    
    ident = 0
    tab = 4
    for namespace in namespaces:
        hierarchy += ' ' * ident + ns_template.format(namespace)
        hierarchy += ' ' * ident + '{\n'
        ident += tab
    
    hierarchy += ' ' * ident
    hierarchy += str('\n' + ' ' * ident).join(list(map(lambda x : class_template.format(x.function_name()), prototypes)))
    hierarchy += str('\n' + ' ' * ident) + class_template.format('MasterC')
    hierarchy += '\n'
    ident -= tab
    
    for namespace in namespaces:
        hierarchy += ' ' * (ident) + '}\n'
        ident -= tab
    
    return hierarchy

def mkdirIfNotExist(path):
    if not os.path.exists(path):
        os.makedirs(path)

def getIncludeEnvVar():
    try:
        include_path = os.environ['INCLUDE']
    except KeyError:
        raise Exception("You must either specify include_path or define the INCLUDE environment variable")
    
    return include_path

def getClassDefinitions(prototypes, indent = 4):
    names = []
    for prototype in prototypes:
        names.append('class {0};'.format('I' + prototype.function_name()))
    
    names.append('class IMasterCWrapper;')
    
    base = '\n' + (' ' * indent)
    
    return base.join(names)

def getFunctions(function_file):
    with open(function_file, 'rt') as file:
        return list(map(lambda x : x.strip(), file.readlines()))

# A simple visitor for FuncDef nodes that prints the names and 
# locations of function definitions.
#
class FuncDeclVisitor(c_ast.NodeVisitor):

    def __init__(self):
        self.prototypes = {}

    def visit_FuncDecl(self, node):
        proto = FunctionPrototype(node)
        self.prototypes[proto.function_name()] = proto

class FunctionArgument():

    def __init__(self, ast_node):
        self.node = ast_node
        self.ptr = 0

    def _qual(self):
        try:
            if len(self.node.quals) == 0:
                return ''
                
            return self.node.quals[0]
        except AttributeError:
            return ''

    def _get_type_node(self, parent):
        if type(parent) == c_ast.PtrDecl:
            self.ptr += 1
        
        if type(parent) == c_ast.TypeDecl:
            return parent
        
        for child in parent.children():
            return self._get_type_node(child)

    def _type_name(self):
        if type(self.node) is c_ast.EllipsisParam:
            return '...'
        
        self.ptr = 0
        type_node = self._get_type_node(self.node)
        
        if type(type_node.type) == c_ast.Struct:
            return 'struct ' + type_node.type.name + self._get_ptrs()
        
        return ' '.join(reversed(type_node.type.names)) + self._get_ptrs()

    def _get_ptrs(self):
        if self.ptr == 0:
            return ''
            
        return ' ' + '*' * self.ptr

    def arg_name(self):
        if type(self.node) is c_ast.EllipsisParam:
            return ''
            
        self.ptr = 0
        type_node = self._get_type_node(self.node)
        
        if type_node.declname is None:
            return ''
            
        return type_node.declname

    def __str__(self):
        return ' '.join((self._qual(), self._type_name(), self.arg_name())).strip()

class FunctionPrototype():

    def __init__(self, ast_node):
        self.node = ast_node
        self.ptr = 0

    def _get_type_node(self, parent):
        if type(parent) == c_ast.PtrDecl:
            self.ptr += 1
        
        if type(parent) == c_ast.TypeDecl:
            return parent
        
        for child in parent.children():
            return self._get_type_node(child)

    def _get_ptrs(self):
        return '*' * self.ptr

    def return_type(self):
        self.ptr = 0
        type_node = self._get_type_node(self.node.type)
        
        if type(type_node.type) == c_ast.Struct:
            return 'struct ' + type_node.type.name + self._get_ptrs()
            
        return ' '.join(reversed(type_node.type.names))

    def function_name(self):
        self.ptr = 0
        type_node = self._get_type_node(self.node.type)
        
        return type_node.declname

    def args(self):
        args = []
        try:
            for arg in self.node.args.params:
                args.append(FunctionArgument(arg))
        except AttributeError:
            pass
        return args
    
    def qualifier(self):
        try:
            if len(self.node.quals) == 0:
                return ''
            return self.node.quals[0] + ' '
        except AttributeError:
            return ''

    def prototype(self):
        arglist = []
        for arg in self.args():
            arglist.append(str(arg))

        return '''{0}
{1}(
    {2}){3};\n\n'''.format(self.return_type(), self.function_name(), ',\n    '.join(arglist), self.qualifier())

def getFunctionASTs(include_path, functionsToWrap):
    filesToFind = []
    functionsToFind = []
    
    for function in functionsToWrap:
        function, file = function.split(' ')
        if not file in filesToFind:
            filesToFind.append(file)
        if not function in functionsToFind:
            functionsToFind.append(function)
        
    parser = c_parser.CParser()
    ast = parser.parse(open('windows.i', 'rt').read(), 'windows.h.i')
    v = FuncDeclVisitor()
    v.visit(ast)
    
    funcs = []
    
    for function in functionsToFind:
        funcs.append(v.prototypes[function])
        
    return funcs, filesToFind
    
    ###############################
    ## we will be able to call the preprocessor every time once pycparser is a little more resilient
    ###############################
    # includeDirs = include_path.split(PATH_SEPARATOR)
    # includeDirs.remove(includeDirs[len(includeDirs)-1])
    
    # functionASTs = {}
    
    # parser = c_parser.CParser()
    # for fileName in filesToFind:
        # for dir in includeDirs:
            # filePath = os.path.join(dir, fileName)
            # if not os.path.exists(filePath):
                # continue
            # command = 'cl.exe /EP /u /DWIN32 /D_WIN32 /D_M_IX86 /D_X86_ /D__inline= /DMIDL_PASS /U__cplusplus "{0}"'.format(filePath)
            # print(command)
            # preprocessor = subprocess.Popen(
                # command,
                # shell=True,
                # stdout=subprocess.PIPE,
                # stderr=subprocess.PIPE,
                # universal_newlines=True)
            # text = removePragmas(preprocessor.communicate()[0])
            
            # if (preprocessor.returncode != 0):
                # print('Failed to preprocess {0}'.format(filePath))
                # continue
            
            # try:
                # ast = parser.parse(text, filePath)
                # print(ast)
                # break
            # except plyparser.ParseError as e:
                # print(e)
                # open('{0}.i'.format(fileName), 'wt').write(text)
                        
    # if len(functionASTs) != len(functionsToWrap):
        # print('One or more functions could not be found in the include path')
    
    # return None, None

def removePragmas(text):
    cleaned = ''
    regex = re.compile('^\#pragma.*$')
    uow = re.compile('\s*UOW\s*UOW')
    text = text.replace('__declspec(deprecated)', '') \
        .replace('__declspec(dllimport)', '') \
        .replace('__declspec(align(4))', '') \
        .replace('__declspec(noreturn)', '') \
        .replace('[size_is(SubAuthorityCount)]', '') \
        .replace('__stdcall', '') \
        .replace('[range(0,32768)]', '') \
        .replace('GUID  UOW', 'GUID  uOW') \
        .replace('[size_is(cbData)]', '') \
        .replace('[range(0,100)]', '') \
        .replace('[range(0,266240)]', '')
        
    for line in text.splitlines(True):
        if len(line.strip()) == 0 or regex.match(line):
            continue
        line = uow.sub('UOW    uOW', line)
        cleaned += line
    
    return cleaned

def getFullyQualifiedName(namespaces):
    return '::'.join(namespaces)

def getArgs(prototype, indent=8):
    arglist = []
    for arg in prototype.args():
        arglist.append(str(arg))
    
    base = ',\n' + (' ' * indent)
    return base.join(arglist)

def generateInterface(prototype, base_namespace, funcPrefix):
    function = texttemplates.INTERFACE_FUNCTION_TEMPLATE.format(
        prototype.return_type(),
        funcPrefix,
        prototype.function_name(),
        getArgs(prototype),
        'const')
    
    className = 'I' + prototype.function_name()
    
    return texttemplates.INTERFACE_CLASS_TEMPLATE.format(
        getFullyQualifiedName((base_namespace, className)),
        function,
        className)

def getIncludes(includes):
    return '\n'.join(list(map(lambda x : '#include <{0}>'.format(x), includes)))

def generateComponent(prototype, base_namespace, component_namespace, funcPrefix, component_suffix):
    function = texttemplates.COMPONENT_FUNCTION_TEMPLATE.format(
        prototype.return_type(),
        funcPrefix,
        prototype.function_name(),
        getArgs(prototype),
        'const',
        getArgNames(prototype))
    
    className = prototype.function_name() + component_suffix
    
    return texttemplates.INHERITING_CLASS_TEMPLATE.format(
        getFullyQualifiedName((base_namespace, component_namespace, className)),
        getFullyQualifiedName((base_namespace, 'I' + prototype.function_name())),
        function,
        className)

def getArgNames(prototype, ident=12):
    arglist = []
    for arg in prototype.args():
        arglist.append(arg.arg_name())
    
    base = ',\n' + ' ' * ident
    return base.join(arglist)

def generateMock(prototype, base_namespace, funcPrefix):
    return ''

def usage():
    print(USAGE + '\n' + DESCRIPTION)

    ''' functionList [-i include_path] [-n] [-b base_namespace]
        [-m mock_namespace] [-c component_namespace] [-p funcPrefix]
        [-s component_suffix] [-i base_include] [-t interface_dir]
        [-o component_dir] [-k mock_dir]'''
        
if __name__ == '__main__':
    try:
        filename = sys.argv[1]
    except:
        usage()
    
    if (len(sys.argv) > 2):
        try:
            opts, args = getopt.getopt(sys.argv[2:], 'i:nb:m:c:p:s:i:t:o:k:', ['include_path=', 'disableGMock', 'base_namespace=', 'mock_namespace=', 'component_namespace=', 'funcPrefix=', 'component_suffix=', 'base_include=', 'interface_dir=', 'component_dir=', 'mock_dir='])
        except getopt.GetoptError as err:
            print(err)
            usage()
            sys.exit(2)
    
    kwargs = {}
    
    for o, a in opts:
        if o in ('-i', '--include_path'):
            kwargs['include_path'] = a
        elif o in ('-n', '--disableGMock'):
            kwargs['generateGmock'] = False
        elif o in ('-b', '--base_namespace'):
            kwargs['base_namespace'] = a
        elif o in ('-m', '--mock_namespace'):
            kwargs['mock_namespace'] = a
        elif o in ('-c', '--component_namespace'):
            kwargs['component_namespace'] = a
        elif o in ('-p', '--funcPrefix'):
            kwargs['funcPrefix'] = a
        elif o in ('-s', '--component_suffix'):
            kwargs['component_suffix'] = a
        elif o in ('-i', '--base_include'):
            kwargs['base_include'] = a
        elif o in ('-t', '--interface_dir'):
            kwargs['interface_dir'] = a
        elif o in ('-o', '--component_dir'):
            kwargs['component_dir'] = a
        elif o in ('-k', '--mock_dir'):
            kwargs['mock_dir'] = a
    
    generate(filename, *kwargs)