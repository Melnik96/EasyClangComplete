from __future__ import print_function
import sys, os

from subprocess import call

from .pycparser import c_parser, c_ast

source_code = ''
source_code_lines = []

structs = {}
nusted_structs = {}
vars = {}

class DeclsVisitor(c_ast.NodeVisitor):
    def visit_Struct(self, node):
        #print('%s at %s fields %s' % (node.name, node.coord, node.decls))
        structs[node.name] = []
        
        if isinstance(node.decls, list):
            nusted_structs[node.name] = {}
            
            for field in node.decls:
                #print(field.type)
                #print('%s 1 %s' % (field.name, isinstance(field.type.type, c_ast.FuncDecl)))
                #print(field.type)
                if isinstance(field.type, c_ast.TypeDecl) and isinstance(field.type.type, c_ast.FuncDecl):
                    structs[node.name].append(field.name)
                    
                if isinstance(field.type, c_ast.PtrDecl) and isinstance(field.type.type, c_ast.TypeDecl) and isinstance(field.type.type.type, c_ast.Struct):
                    #print(node.name, field.name, field.type.type.type.name)
                    
                    nusted_structs[node.name] = {field.name: field.type.type.type.name}
                    #print(nusted_structs)
        
    def visit_TypeDecl(self, node):
        if isinstance(node.type, c_ast.Struct):
            #print(node.declname, node.type.name)
            vars[node.declname] = node.type.name
            
        if isinstance(node.type, c_ast.IdentifierType):
            #print(node.declname, node.type.name)
            vars[node.declname] = node.type.names[0]
        

class FuncDefVisitor(c_ast.NodeVisitor):
    def visit_FuncCall(self, node):
        global source_code
        #print('%s 1 %s 2 %s 3 %s' % (node.coord, node.name.name.name, node.name.type, node.name.field.name))#a esli pointer to function
        
        #print('node.name', node.name)
        #print('node.name.name', node.name.name)
        
        sem_struct_name = ''
        sem_obj_path = ''
        cur_node = node.name
        
        if isinstance(cur_node, c_ast.StructRef):
            print(cur_node)
        else:
            return
        
        while True:
            if isinstance(cur_node.name, c_ast.StructRef):
                sem_obj_path += cur_node.type + cur_node.field.name
                cur_node = cur_node.name
                continue
            if isinstance(cur_node.name, c_ast.ID):
                sem_obj_path = cur_node.name.name + cur_node.type + cur_node.field.name + sem_obj_path
                #sem_struct_name = nusted_structs[vars[cur_node.name.name]]
                #print(sem_struct_name)
                #if cur_node.field.name in sem_struct_name:
                    #print(sem_struct_name[cur_node.field.name])
                break
            else:
                return
        
        #print(sem_obj_path.replace('->', '.').split('.'))
        sem_obj_path_d = sem_obj_path.replace('->', '.').split('.')
        
        f_var = vars[sem_obj_path_d[0]]
        #print('f_var', f_var)
        #print('nusted_structs[f_var]', nusted_structs[f_var])
        del sem_obj_path_d[0]
        
        last_struct = f_var
        for var in sem_obj_path_d:
            if var in nusted_structs[last_struct]:
                #print('vars[var]', nusted_structs[last_struct][var])
                last_struct = nusted_structs[last_struct][var]
            else:
                sem_struct_name = last_struct
                
        
        #print((sem_obj_path.replace(sem_obj_path_d[-1], '')+'-').replace('->-', '').replace('.-', ''))
        
        self_obj = (sem_obj_path.replace(sem_obj_path_d[-1], '')+'-').replace('->-', '').replace('.-', '')
        self_fun_call = sem_obj_path.replace(self_obj, '')
        #print(self_obj)
        #print(last_struct)
        #print(vars)
        
        line_before = source_code_lines[node.coord.line-1]
        line_before_need_comma = ''
        if '()' not in line_before:
            line_before_need_comma = ', '
                    
                
        self_name_exp = self_obj
        if '.' in self_fun_call:
            #print(self_name_exp)
            self_name_exp = '&'+self_name_exp
                
        line_after = source_code_lines[node.coord.line-1].replace(sem_obj_path + '(', sem_struct_name + '_' + self_fun_call.replace('->', '').replace('.', '') + '(' + self_name_exp + line_before_need_comma, 1)
        source_code = source_code.replace(line_before, line_after, 1)
        


def nutty_translate(filename, in_source):
    file = open('/tmp/pncc'+os.path.basename(filename)+'.nuti.i','w')
    file.write(in_source)
    file.close()
    
    e_source = os.popen('gcc -E -I/home/melnik/projects/nutty_lang/pycparser/utils/fake_libc_include/ -I/usr/local/include/ '+'/tmp/pncc'+os.path.basename(filename)+'.nuti.i').read()
        
    for line in source_code.split("\n"):
        source_code_lines.append(line)
    
    ast = c_parser.CParser().parse(e_source, filename='<stdin>')

    v = DeclsVisitor()
    v.visit(ast)
    
    v1 = FuncDefVisitor()
    v1.visit(ast)
    
    return source_code
