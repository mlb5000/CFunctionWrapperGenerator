import re

class NullDevice():
    def write(self, s):
        pass

class FunctionArgument():

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

class FunctionPrototype():

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