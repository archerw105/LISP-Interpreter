"""6.009 Lab 8A: carlae Interpreter"""

import sys


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
            return None
        if v in self.env:
            return self.env[v]
        if self.parent is None:
            return None
        return self.parent.get(v)

    def set(self, symbol, value):
        "Set the value of symbol to value in the current env"
        self.env[symbol] = value

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

carlae_builtins = Environment(init_dict = {
    '+': sum,
    '-': lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
    '*': lambda args: mult_func(*args),
    '/': lambda args: div_func(*args)
})

def result_and_env(tree, cur_env = None):
    """Same as evaluate, but also returns environment"""
    if cur_env is None:
        cur_env = Environment(carlae_builtins)

    if isinstance(tree, list) and len(tree) == 0:
        raise EvaluationError("EvaluationError")

    if isinstance(tree, int) or isinstance(tree, float):
        return tree, cur_env

    if isinstance(tree, str):
        v = cur_env.get(tree)
        if v:
            return v, cur_env
        raise EvaluationError("EvaluationError")

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

    if not isinstance(tree[0], list) and not isinstance(tree[0], str):
        raise EvaluationError("EvaluationError")

    ex = []
    for i in tree[1:]:
        new_env = Environment(cur_env)
        ex.append(result_and_env(i, cur_env)[0])
    new_env = Environment(cur_env)
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

def REPL():
    """
    Do a REPL
    """
    env = Environment(carlae_builtins)
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
