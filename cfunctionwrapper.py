import loadpath
import os
import sys
import texttemplates
import getopt
from cpp import ast
from cfwclasses import *
import yaml

PATH_SEPARATOR = ';' if os.name == 'nt' else ':'

USAGE = 'Usage:\n\n' + __file__ + ''' functionList [-i include_path] [-n] [-b base_namespace]
        [-m mock_namespace] [-c component_namespace] [-p funcPrefix]
        [-s component_suffix] [-i base_include] [-t interface_dir]
        [-o component_dir] [-k mock_dir]'''

DESCRIPTION = '''
Generate C++ C-function wrapper classes

Precondition: The INCLUDE environment variable must be set

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
        
    configuration = yaml.load(open(function_file, 'rt').read())
    print('Parsing files')
    prototypes, found_files = getFunctionASTs(include_path, configuration['Functions'])
    
    interface_classes = ''
    component_classes = ''
    
    print('Generating wrappers')
    wrappers = []
    for prototype in prototypes:
        wrapper = FunctionWrapper(prototype, base_namespace, component_namespace, mock_namespace, funcPrefix, component_suffix)
        wrappers.append(wrapper)
        
        interface_classes += wrapper.interface_class()
        component_classes += wrapper.component_class()
    
    aggregates = []
    for aggregate in configuration['Aggregators']:
        name = aggregate['name']
        functions = aggregate['functions']
        
        ag_wrappers = []
        for wrapper in wrappers:
            if wrapper.prototype.function_name() in functions:
                ag_wrappers.append(wrapper)
        
        aggregator = FunctionAggregate(name, base_namespace, component_suffix, component_namespace, mock_namespace)
        aggregator.wrappers = ag_wrappers
        
        aggregates.append(aggregator)
    
    master = FunctionAggregate('MasterC', base_namespace, component_suffix, component_namespace, mock_namespace)
    master.wrappers = wrappers
    aggregates.append(master)
    
    mock_classes = ''
    
    for aggregate in aggregates:
        print('Generating {0} interface'.format(aggregate.name))
        interface_classes += aggregate.interface_aggregate()
        print('Generating {0} wrapper component'.format(aggregate.name))
        component_classes += aggregate.component_aggregate()
        if generateGmock:
            print('Generating {0} mock wrapper'.format(aggregate.name))
            mock_classes += aggregate.mock_aggregate()
    
    interface_file = os.path.join(full_interface_dir, 'ICWrappers.h')
    print('Generating interface file {0}'.format(interface_file))
    with open(interface_file, 'wt') as file:
        file.write(texttemplates.INTERFACE_FILE_TEMPLATE.format(
            base_namespace,
            interface_classes,
            getInterfaceDefinitions(prototypes, aggregates),
            getIncludes(found_files)))
    
    component_file = os.path.join(full_component_dir, 'CWrappers.h')
    
    print('Generating component file {0}'.format(component_file))
    with open(component_file, 'wt') as file:
        file.write(texttemplates.COMPONENT_FILE_TEMPLATE.format(
            base_namespace,
            getIncludes(found_files),
            component_classes,
            getNamespaceHierarchy(
                getComponentDefinitions(prototypes, aggregates, component_suffix),
                getFullyQualifiedName((base_namespace, component_namespace)))))
    
    if not generateGmock:
        return
    
    mock_file = os.path.join(full_mock_dir, 'CWrappers.h')
    print('Generating mock file {0}'.format(mock_file))
    with open(mock_file, 'wt') as file:
        file.write(texttemplates.GMOCK_FILE_TEMPLATE.format(
            base_namespace,
            mock_classes))
    
    print('Done!')

def getIncludeEnvVar():
    try:
        include_path = os.environ['INCLUDE']
    except KeyError:
        raise Exception("You must either specify include_path or define the INCLUDE environment variable")
    
    return include_path

def mkdirIfNotExist(path):
    if not os.path.exists(path):
        os.makedirs(path)

def getFunctions(function_file):
    with open(function_file, 'rt') as file:
        return list(map(lambda x : x.strip().split(' '), file.readlines()))

def getFunctionASTs(include_path, functionsToWrap):
    filesToFind = []
    funcsToFind = []
    
    for item in functionsToWrap:
        func = item['name']
        real_loc = item['real_header']
        include = item['include_header']
        
        if (real_loc, include) not in filesToFind:
            filesToFind.append((real_loc, include))
        if func not in funcsToFind:
            funcsToFind.append(func)
    
    includeDirs = include_path.split(PATH_SEPARATOR)
    includeDirs.remove(includeDirs[len(includeDirs)-1])
    
    prototypes = []
    foundFiles = []
    for fileName, include in filesToFind:
        for dir in includeDirs:
            filePath = os.path.join(dir, fileName)
            if not os.path.exists(filePath):
                continue
            foundFiles.append(include)
            source = open(filePath, 'rt').read()
            builder = ast.BuilderFromSource(source, filePath)
            entire_ast = filter(None, builder.Generate())
            
            original_stderr = sys.stderr
            sys.stderr = NullDevice()
            for tree in entire_ast:
                try:
                    if type(tree) != ast.Function or tree.name not in funcsToFind:
                        continue
                    
                    prototypes.append(FunctionPrototype(tree))
                except AssertionError:
                    pass
                except:
                    print('I did my best, but I can go no further. Hopefully the collected ASTs are sufficient for your needs')
            sys.stderr = original_stderr
    
    return prototypes, foundFiles

def getFullyQualifiedName(namespaces):
    return '::'.join(namespaces)

def getInterfaceDefinitions(prototypes, aggregators, indent = 4):
    names = []
    for prototype in prototypes:
        names.append('class {0};'.format(INTERFACE_PREFIX + prototype.function_name()))
    
    for aggregate in aggregators:
        names.append('class {0};'.format(aggregate.interface_name()))
    
    base = '\n' + (' ' * indent)
    
    return base.join(names)

def getComponentDefinitions(prototypes, aggregators, component_suffix, indent = 4):
    names = []
    for prototype in prototypes:
        names.append(prototype.function_name() + component_suffix)
    
    for aggregate in aggregators:
        names.append(aggregate.component_name())
    
    return names

def getIncludes(includes):
    return '\n'.join(list(map(lambda x : '#include <{0}>'.format(x), includes)))

def getNamespaceHierarchy(classes, hierarchy):
    namespaces = hierarchy.split('::')
    ns_template = 'namespace {0}\n'
    class_template = 'class {0};'
    hierarchy = ''
    
    ident = 0
    tab = 4
    for namespace in namespaces:
        hierarchy += ' ' * ident + ns_template.format(namespace)
        hierarchy += ' ' * ident + '{\n'
        ident += tab
    
    hierarchy += ' ' * ident
    hierarchy += str('\n' + ' ' * ident).join(list(map(lambda x : class_template.format(x), classes)))
    hierarchy += '\n'
    ident -= tab
    
    for namespace in namespaces:
        hierarchy += ' ' * (ident) + '}\n'
        ident -= tab
    
    return hierarchy

def usage():
    print(USAGE + '\n' + DESCRIPTION)

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
    
    generate(filename, **kwargs)