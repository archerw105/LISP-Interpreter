"""6.009 Lab 8B: carlae Interpreter Part 2"""

import sys

NULL = object()

class EvaluationError(Exception):
    """Exception to be raised if there is an error during evaluation."""
    pass


def next_token(s):
    "Find the next token in the string s"
    ind = 0
    nex = ""
    while ind < len(s):
        if s[ind] == '(' or s[ind] == ')':
            if len(nex) > 0:
                yield nex
                nex = ""
            yield s[ind]
        elif s[ind] == ' ':
            if len(nex) > 0:
                yield nex
                nex = ""
        elif s[ind] == ';':
            if len(nex) > 0:
                yield nex
                nex = ""
            return
        else:
            nex += s[ind]
        ind += 1
    if len(nex) > 0:
        yield nex

def tokenize(source):
    """
    Splits an input string into meaningful tokens (left parens, right parens,
    other whitespace-separated values).  Returns a list of strings.

    Arguments:
        source (str): a string containing the source code of a carlae
                      expression
    """
    lines = source.split('\n')
    ret = []
    for i in lines:
        for j in next_token(i):
            ret.append(j)
    return ret

def parse_helper(tokens, ind):
    """Returns the ast of the tokens, index where it ends at"""
    if ind == len(tokens):
        return None, ind
    if tokens[ind] == '(':
        ret = []
        nex_ind = ind + 1
        while nex_ind < len(tokens) and tokens[nex_ind] != ')':
            lst, nex_ind = parse_helper(tokens, nex_ind)
            ret.append(lst)
        if nex_ind == len(tokens) or tokens[nex_ind] != ')':
            raise SyntaxError("SyntaxError")
        return ret, nex_ind + 1
    if tokens[ind] == ')':
        raise SyntaxError("SyntaxError")
    try:
        a = int(tokens[ind])
        return a, ind + 1
    except:
        pass
    try:
        a = float(tokens[ind])
        return a, ind + 1
    except:
        pass
    return tokens[ind], ind + 1

def parse(tokens):
    """
    Parses a list of tokens, constructing a representation where:
        * symbols are represented as Python strings
        * numbers are represented as Python ints or floats
        * S-expressions are represented as Python lists

    Arguments:
        tokens (list): a list of strings representing tokens
    """
    out, ind = parse_helper(tokens, 0)
    if ind != len(tokens):
        raise SyntaxError("SyntaxError")
    return out

def mult_func(*args):
    if len(args) == 1:
        return args[0]
    return args[0] * mult_func(*args[1:])

def div_func(*args):
    if len(args) == 1:
        return args[0]
    return args[0] / mult_func(*args[1:])

def boolean_func(op):
    "Return a boolean function that does op"
    def ret(*args):
        if len(args) == 1:
            return True
        return op(args[0], args[1]) and ret(*args[1:])
    return ret

class Environment():
    def __init__(self, parent = None, init_dict = {}):
        "Init"
        self.env = {}
        for i in init_dict:
            self.env[i] = init_dict[i]
        self.parent = parent

    def get(self, v):
        "Get the value of v, or None if v doesn't exist"
        if isinstance(v, list):
            return NULL
        if v in self.env:
            return self.env[v]
        if self.parent is None:
            return NULL
        return self.parent.get(v)

    def set(self, symbol, value):
        "Set the value of symbol to value in the current env"
        self.env[symbol] = value

    def set_bang(self, symbol, value):
        "Set the value of symbol to value using set bang rules"
        if symbol in self.env:
            self.env[symbol] = value
            return True
        if self.parent is not None:
            return self.parent.set_bang(symbol, value)
        return False

    def copy(self):
        "Return a deepcopy"
        ret = Environment(self.parent)
        for i in self.env:
            ret.env[i] = self.env[i]
        return ret

    def __repr__(self):
        "Give representation"
        ret = 'Environment(\n'
        for i in self.env:
            ret += str(i) + ' = ' + str(self.env[i]) + '\n'
        ret += '\n)'
        return ret

class Function():
    def __init__(self, param, code, env):
        """Defines a Function
        env is a given environment for this function
        """
        self.param = param
        self.env = env # the environment of this function
        for i in param:
            self.env.set(i, None)
        self.code = code # will be evaluated when needed

    def set_values(self, param_values):
        "Return a copy of this function with the values set"
        if len(param_values) != len(self.param):
            raise EvaluationError("EvaluationError")
        ret = Function(self.param, self.code, self.env.copy())
        for j, i in enumerate(self.param):
            ret.env.set(i, param_values[j])
        return ret

    def __repr__(self):
        return 'function object'

class LinkedList():
    def __init__(self, elt, nex = None):
        self.elt = elt
        self.next = nex

    def set_next(self, nex):
        self.next = nex

    def __repr__(self):
        ret = 'LinkedList('
        a = self
        while a is not None:
            ret += str(a.elt)
            a = a.next
            if a is not None:
                ret += ', '
        return ret + ')'

    def length(self):
        "Return the length of linked list"
        ret = 0
        a = self
        while a is not None:
            ret += 1
            a = a.next
        return ret

    def copy(self):
        "Return a deepcopy of linked list starting here"
        return self.map(lambda x: x)

    def index(self, ind):
        "Return the value ind places down the list"
        a = self
        while ind > 0 and a is not None:
            ind -= 1
            a = a.next
        if a is None:
            raise EvaluationError('EvaluationError')
        return a

    def end(self):
        "Return the end of the list"
        a = self
        while a.next is not None:
            a = a.next
        return a

    def map(self, func):
        "Return the map of the list under func"
        ret = LinkedList(func(self.elt))
        ex = ret
        a = self.next
        while a is not None:
            ex.next = LinkedList(func(a.elt))
            ex = ex.next
            a = a.next
        return ret

    def filter(self, func):
        "Return the filter of the list under func"
        ret = None
        ex = ret
        a = self
        while a is not None:
            if func(a.elt):
                if ret is None:
                    ret = LinkedList(a.elt)
                    ex = ret
                else:
                    ex.next = LinkedList(a.elt)
                    ex = ex.next
            a = a.next
        return ret

    def reduce(self, func, init):
        "Reduce the list"
        ret = init
        a = self
        while a is not None:
            ret = func(ret, a.elt)
            a = a.next
        return ret

def make_linked_list(*args):
    "Make a linked list from a given list"
    if len(args) == 0:
        return None
    a = LinkedList(args[0], make_linked_list(*args[1:]))
    return a

def concat_linked_lists(*args):
    "Concatenate linked lists"
    if len(args) == 0:
        return None
    if args[0] is None:
        return concat_linked_lists(*args[1:])
    ret = args[0].copy()
    ret.end().next = concat_linked_lists(*args[1:])
    return ret

def evaluate_function(func, cur_env):
    """Evaluate the function func
    func is either a python function or a carlae function"""
    def extra(*args):
        if isinstance(func, Function):
            f = func.set_values(args)
            return result_and_env(f.code, f.env)[0]
        return func(args)
    return extra

carlae_builtins = Environment(None, {
    '+': sum,
    '-': lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
    '*': lambda args: mult_func(*args),
    '/': lambda args: div_func(*args),
    '=?': lambda args: boolean_func(lambda x, y: x == y)(*args),
    '>': lambda args: boolean_func(lambda x, y: x > y)(*args),
    '>=': lambda args: boolean_func(lambda x, y: x >= y)(*args),
    '<': lambda args: boolean_func(lambda x, y: x < y)(*args),
    '<=': lambda args: boolean_func(lambda x, y: x <= y)(*args),
    '#t': True,
    '#f': False,
    'not': lambda args: EvaluationError("EvaluationError") if len(args) != 1 else not args[0],
    'list': lambda args: make_linked_list(*args),
    'concat': lambda args: concat_linked_lists(*args)
})

def result_and_env(tree, cur_env = None):
    """Same as evaluate, but also returns environment"""
    if cur_env is None:
        cur_env = Environment(carlae_builtins, {})

    if isinstance(tree, list) and len(tree) == 0:
        raise EvaluationError("EvaluationError")

    if isinstance(tree, int) or isinstance(tree, float):
        return tree, cur_env

    if isinstance(tree, str):
        v = cur_env.get(tree)
        if v is NULL:
            raise EvaluationError("EvaluationError")
        return v, cur_env

    if tree[0] == 'define':
        if (not isinstance(tree[1], str)) and (not isinstance(tree[1], list)):
            raise EvaluationError("EvaluationError")
        name = tree[1]
        val = None
        new_env = Environment(cur_env)
        if isinstance(tree[1], list):
            name = tree[1][0]
            val = Function(tree[1][1:], tree[2], new_env)
        else:
            val = result_and_env(tree[2], cur_env)[0]
        cur_env.set(name, val)
        return cur_env.get(name), cur_env

    if tree[0] == 'lambda':
        if len(tree) != 3:
            raise EvaluationError("EvaluationError")
        new_env = Environment(cur_env)
        func = Function(tree[1], tree[2], new_env)
        return func, cur_env

    if tree[0] == 'if':
        if len(tree) != 4:
            raise EvaluationError("EvaluationError")
        if result_and_env(tree[1], cur_env)[0]:
            return result_and_env(tree[2], cur_env)[0], cur_env
        return result_and_env(tree[3], cur_env)[0], cur_env

    if tree[0] == 'and':
        for i in tree[1:]:
            if not result_and_env(i, cur_env)[0]:
                return False, cur_env
        return True, cur_env

    if tree[0] == 'or':
        for i in tree[1:]:
            if result_and_env(i, cur_env)[0]:
                return True, cur_env
        return False, cur_env

    if tree[0] == 'car':
        if len(tree) != 2:
            raise EvaluationError('EvaluationError')
        ll = result_and_env(tree[1], cur_env)[0]
        if ll is None or not isinstance(ll, LinkedList):
            raise EvaluationError('EvaluationError')
        return ll.elt, cur_env

    if tree[0] == 'cdr':
        if len(tree) != 2:
            raise EvaluationError('EvaluationError')
        ll = result_and_env(tree[1], cur_env)[0]
        if ll is None or not isinstance(ll, LinkedList):
            raise EvaluationError('EvaluationError')
        return ll.next.copy(), cur_env

    if tree[0] == 'length':
        if len(tree) != 2:
            raise EvaluationError('EvaluationError')
        ll = result_and_env(tree[1], cur_env)[0]
        if ll is None:
            return 0, cur_env
        return ll.length(), cur_env

    if tree[0] == 'elt-at-index':
        if len(tree) != 3:
            raise EvaluationError('EvaluationError')
        ll = result_and_env(tree[1], cur_env)[0]
        if ll is None:
            raise EvaluationError('EvaluationError')
        return ll.index(result_and_env(tree[2], cur_env)[0]).elt, cur_env

    if tree[0] == 'map':
        if len(tree) != 3:
            raise EvaluationError('EvaluationError')
        func = result_and_env(tree[1], cur_env)[0]
        lst = result_and_env(tree[2], cur_env)[0]
        return lst.map(evaluate_function(func, cur_env)), cur_env

    if tree[0] == 'filter':
        if len(tree) != 3:
            raise EvaluationError('EvaluationError')
        func = result_and_env(tree[1], cur_env)[0]
        lst = result_and_env(tree[2], cur_env)[0]
        return lst.filter(evaluate_function(func, cur_env)), cur_env

    if tree[0] == 'reduce':
        if len(tree) != 4:
            raise EvaluationError('EvaluationError')
        func = result_and_env(tree[1], cur_env)[0]
        lst = result_and_env(tree[2], cur_env)[0]
        return lst.reduce(evaluate_function(func, cur_env), result_and_env(tree[3], cur_env)[0]), cur_env

    if tree[0] == 'begin':
        if len(tree) < 2:
            raise EvaluationError('EvaluationError')
        ret = None
        for i in tree[1:]:
            ret = result_and_env(i, cur_env)[0]
        return ret, cur_env

    if tree[0] == 'let':
        if len(tree) != 3:
            raise EvaluationError('EvaluationError')
        new_env = Environment(cur_env, {})
        for i in tree[1]:
            val = result_and_env(i[1], cur_env)[0]
            new_env.set(i[0], val)
        return result_and_env(tree[2], new_env)[0], cur_env

    if tree[0] == 'set!':
        if len(tree) != 3:
            raise EvaluationError('EvaluationError')
        val = result_and_env(tree[2], cur_env)[0]
        if not cur_env.set_bang(tree[1], val):
            raise EvaluationError('EvaluationError')
        return val, cur_env

    if not isinstance(tree[0], list) and not isinstance(tree[0], str):
        raise EvaluationError("EvaluationError")

    ex = []
    for i in tree[1:]:
        ex.append(result_and_env(i, cur_env)[0])
    func = result_and_env(tree[0], cur_env)[0]
    if isinstance(func, Function):
        func = func.set_values(ex)
        return result_and_env(func.code, func.env)[0], cur_env
    return func(ex), cur_env

def evaluate(tree, cur_env = None):
    """
    Evaluate the given syntax tree according to the rules of the carlae
    language.

    Arguments:
        tree (type varies): a fully parsed expression, as the output from the
                            parse function
    """
    return result_and_env(tree, cur_env)[0]

def evaluate_file(file_name, cur_env = None):
    "Return the evaluation of string in file"
    f = open(file_name, 'r')
    s = f.read()
    f.close()
    return evaluate(parse(tokenize(s)), cur_env)

def REPL():
    """
    Do a REPL
    """
    env = Environment(carlae_builtins)
    
    for i in sys.argv[1:]:
        evaluate_file(i, env)

    while True:
        source = input("in> ")
        if source == "QUIT":
            return
        try:
            print("  out> ", evaluate(parse(tokenize(source)), env))
        except (SyntaxError, EvaluationError) as e:
            print("  out> ", e)
        except:
            print("  out> Error")
        print()

if __name__ == '__main__':
    # code in this block will only be executed if lab.py is the main file being
    # run (not when this module is imported)
    REPL()
