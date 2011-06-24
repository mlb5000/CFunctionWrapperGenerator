import os
import sys
import loadpath
from cpp import ast

PATH_SEPARATOR = ';' if os.name == 'nt' else ':'

class NullDevice():
    def write(self, s):
        pass

def main():
    funcs = getFunctions('cfunctions.txt')
    
    filesToFind = []
    funcsToFind = []
    includeFiles = []
    for func, real_loc, include in funcs:
        if real_loc not in filesToFind:
            filesToFind.append(real_loc)
        if func not in funcsToFind:
            funcsToFind.append(func)
        if include not in includeFiles:
            includeFiles.append(include)
    
    includeDirs = getIncludeEnvVar().split(PATH_SEPARATOR)
    includeDirs.remove(includeDirs[len(includeDirs)-1])
    
    for fileName in filesToFind:
        for dir in includeDirs:
            filePath = os.path.join(dir, fileName)
            if not os.path.exists(filePath):
                continue
            
            source = open(filePath, 'rt').read()
            builder = ast.BuilderFromSource(source, filePath)
            entire_ast = filter(None, builder.Generate())
            
            original_stderr = sys.stderr
            sys.stderr = NullDevice()
            for tree in entire_ast:
                try:
                    if type(tree) != ast.Function or tree.name not in funcsToFind:
                        continue
                    
                    print(str(tree) + '\n\n')
                except AssertionError:
                    pass
                except:
                    print('I did my best, but I can go no further. Hopefully the collected ASTs are sufficient for your needs')
            sys.stderr = original_stderr

def getIncludeEnvVar():
    try:
        include_path = os.environ['INCLUDE']
    except KeyError:
        raise Exception("You must either specify include_path or define the INCLUDE environment variable")
    
    return include_path

def getFunctions(function_file):
    with open(function_file, 'rt') as file:
        return list(map(lambda x : x.strip().split(' '), file.readlines()))

if __name__ == '__main__':
    main()