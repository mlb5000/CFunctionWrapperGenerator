import re
import texttemplates

INTERFACE_PREFIX = 'I'

class NullDevice(object):
    def write(self, s):
        pass

class FunctionArgument(object):

    def __init__(self, ast_node):
        self.node = ast_node

    def type(self):
        return self._sanitizeType(self.node.type)
    
    def _sanitizeType(self, typeNode):
        prefix = ''
        if typeNode.modifiers:
            prefix = ' '.join(typeNode.modifiers) + ' '
        name = str(typeNode.name)
        if typeNode.templated_types:
            name += '<%s>' % typeNode.templated_types
        suffix = prefix + name
        if typeNode.reference:
            suffix += '&'
        if typeNode.pointer:
            suffix += '*'
        if typeNode.array:
            suffix += '[]'

        in_re = re.compile('(__(in|out)|(OUT|IN)).*\\s+')
        suffix = in_re.sub('', suffix)
        in_re2 = re.compile('__(in|out).*\(.*\)')
        return in_re2.sub('', suffix)

    def arg_name(self):
        return self.node.name

    def __str__(self):
        return ' '.join((self.type(), self.arg_name())).strip()

class FunctionPrototype(object):

    def __init__(self, ast_node):
        self.node = ast_node

    def return_type(self):
        return self._sanitizeType(self.node.return_type.name)

    def _sanitizeType(self, typeName):
        #return typeName
        unnecessaryKeywords = re.compile('(USERENVAPI|WINBASEAPI|WINAPI|__(in|out))')
        final = ''
        
        for token in unnecessaryKeywords.sub('', typeName).split(' '):
            if len(token.strip()) == 0:
                continue
            final += token.strip()
        
        return final

    def function_name(self):
        return self.node.name

    def args(self):
        args = []
        try:
            for arg in self.node.parameters:
                args.append(FunctionArgument(arg))
        except AttributeError:
            pass
        return args
    
    def qualifier(self):
        return '' #not yet supported

class AstHelper(object):

    def __init__(self):
        pass

    def getFullyQualifiedName(self, namespaces):
        return '::'.join(namespaces)

class FunctionWrapper(object):

    def __init__(self,
                 prototype,
                 base_namespace='',
                 component_namespace='Component',
                 mock_namespace='Mock',
                 funcPrefix='my',
                 component_suffix='Wrapper'):
        self.prototype = prototype
        self.base_namespace = base_namespace
        self.component_namespace = component_namespace
        self.mock_namespace = mock_namespace
        self.funcPrefix = funcPrefix
        self.component_suffix= component_suffix
        self.astHelper = AstHelper()

    def interface_name(self):
        return INTERFACE_PREFIX + self.prototype.function_name()

    def interface_class(self):
        function = texttemplates.INTERFACE_FUNCTION_TEMPLATE.format(
        self.prototype.return_type(),
        self.funcPrefix,
        self.prototype.function_name(),
        self.getArgs(),
        'const')
        
        return texttemplates.INTERFACE_CLASS_TEMPLATE.format(
            self.astHelper.getFullyQualifiedName((self.base_namespace, self.interface_name())),
            function,
            self.interface_name())

    def getArgs(self, indent=8):
        arglist = []
        for arg in self.prototype.args():
            arglist.append(str(arg))
        
        base = ',\n' + (' ' * indent)
        return base.join(arglist)

    def component_name(self):
        return self.prototype.function_name() + self.component_suffix

    def component_class(self):
        function = texttemplates.COMPONENT_FUNCTION_TEMPLATE.format(
            self.prototype.return_type(),
            self.funcPrefix,
            self.prototype.function_name(),
            self.getArgs(),
            'const',
            self.getArgNames())
        
        return texttemplates.INHERITING_CLASS_TEMPLATE.format(
            self.astHelper.getFullyQualifiedName((self.base_namespace, self.component_namespace, self.component_name())),
            self.astHelper.getFullyQualifiedName((self.base_namespace, self.interface_name())),
            function,
            self.component_name())

    def getArgNames(self, ident=12):
        arglist = []
        for arg in self.prototype.args():
            arglist.append(arg.arg_name())
        
        base = ',\n' + ' ' * ident
        return base.join(arglist)

    def mock_function(self):
        numArgs = len(self.prototype.args())
        mockType = 'MOCK_CONST_METHOD{0}'.format(numArgs)
        
        return texttemplates.GMOCK_DECLARATION_TEMPLATE.format(
            mockType,
            self.funcPrefix + self.prototype.function_name(),
            self.prototype.return_type(),
            self.getArgs())

    def real_call(self):
        return texttemplates.COMPONENT_FUNCTION_TEMPLATE.format(
                self.prototype.return_type(),
                self.funcPrefix,
                self.prototype.function_name(),
                self.getArgs(),
                'const',
                self.getArgNames())

class FunctionAggregate(object):

    def __init__(self, name, base_namespace='', component_suffix='Wrapper', component_namespace='Component', mock_namespace='Mock'):
        self.name = name
        self.wrappers = []
        self.base_namespace = base_namespace
        self.component_suffix = component_suffix
        self.component_namespace = component_namespace
        self.mock_namespace = mock_namespace
        self.astHelper = AstHelper()

    def interface_aggregate(self):
        interfaces = []
    
        for wrapper in self.wrappers:
            interfaces.append(wrapper.interface_name())
        
        return texttemplates.INHERITING_CLASS_TEMPLATE.format(
            self.astHelper.getFullyQualifiedName((self.base_namespace, self.interface_name())),
            ',\n    public '.join(interfaces),
            '',
            self.interface_name())

    def interface_name(self):
        return INTERFACE_PREFIX + self.component_name()

    def component_aggregate(self):
        functions = ''
        
        for wrapper in self.wrappers:
            functions += wrapper.real_call() + '    '
        
        return texttemplates.INHERITING_CLASS_TEMPLATE.format(
            self.astHelper.getFullyQualifiedName((self.base_namespace, self.component_namespace, self.component_name())),
            self.astHelper.getFullyQualifiedName((self.base_namespace, self.interface_name())),
            functions,
            self.component_name())

    def component_name(self):
        return self.name + self.component_suffix

    def mock_aggregate(self):
        hierarchy = self.astHelper.getFullyQualifiedName((self.base_namespace, self.mock_namespace))
        
        return self.getNamespaces(hierarchy, (self.component_name(),)) + '\n\n' + \
            texttemplates.INHERITING_CLASS_TEMPLATE.format(
                hierarchy+'::'+self.component_name(),
                self.base_namespace+'::'+self.interface_name(),
                self.mock_functions(),
                self.component_name())

    def mock_functions(self):
        functions = ''

        for wrapper in self.wrappers:
            functions += wrapper.mock_function() + ' ' * 4
        
        return functions

    def getNamespaces(self, full_hierarchy, classes):
        namespaces = full_hierarchy.split('::')
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