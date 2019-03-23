import sys

class EvaluationError(Exception):
	pass

NULL = object()

def next_token(line):
	tok = ""
	ind = 0
	while ind < len(line):
		if line[ind] == '(' or line[ind] == ')':
			if len(tok) > 0:
				yield tok
				tok =""
			yield line[ind]
		elif line[ind] == ';':
			if len(tok) > 0:
				yield tok
			return
		elif line[ind] == ' ':
			if len(tok) > 0:
				yield tok
				tok = ""
		else:
			tok += line[ind]
		ind+=1
	if len(tok) > 0:
		yield tok

def tokenize(source):
	"""Splits string 'source' into tokens"""
	lines = source.split('\n')
	lex = []
	for i in lines:
		for j in next_token(i):
			lex.append(j)
	return lex

def parse_helper(lex, ind):
	if ind == len(lex):
		raise SyntaxError("SyntaxError")
	if lex[ind] == '(':
		tree = []
		next_ind = ind + 1
		while next_ind < len(lex) and lex[next_ind] != ')':
			subtree, next_ind = parse_helper(lex, next_ind)
			tree.append(subtree)
		if ind == len(lex):
			raise SyntaxError("SyntaxError")
		return tree, next_ind + 1
	if lex[ind] == ')':
		raise SyntaxError("SyntaxError")
	try:
		a = int(lex[ind])
		return a, ind + 1
	except:
		pass
	try:
		a = float(lex[ind])
		return a, ind + 1
	except:
		pass
	return lex[ind], ind + 1

def parse(lex):
	"""Parse list into an abstract syntax tree"""
	syntree, ind = parse_helper(lex, 0)
	if ind != len(lex):
		raise SyntaxError("SyntaxError")
	return syntree

def mult(args):
	if len(args) == 0:
		return 1
	first = args.pop(0)
	return first * mult(args)

def div(args):
	if len(args) == 0:
		return 1
	first = args.pop(0)
	return float(first)/mult(args)

def boolean_func(op):
	def ret(args):
		if len(args) == 1:
			return True
		return op(args[0], args[1]) and ret(args[1:])
	return ret

class Environment():
	def __init__(self, parent = None, init_dict = {}):
		"Initializing environment class"
		self.env = {}
		for i in init_dict:
			self.env[i] = init_dict[i]
		self.parent = parent

	def get(self, v):
		"Get value of v, or None if it doesn't exist"
		if v in self.env:
			return self.env[v]
		if self.parent is None:
			return NULL
		return self.parent.get(v)

	def set(self, name, val):
		self.env[name] = val

	def set_bang(self, name, val):
		if name in self.env:
			self.env[name] = val
			return val
		if self.parent is None:
			return None
		return self.parent.set_bang(name, val)


class LinkedList():
	def __init__(self, val, next_node = None):
		self.elt = val
		self.next = next_node

	def length(self):
		if self.next == None:
			return 1
		return 1 + self.next.length()

	def at_index(self, ind):
		if self.next == None:
			if ind == 0:
				return self.elt
			raise EvaluationError("EvaluationError")
		if ind == 0:
			return self.elt
		return self.next.at_index(ind-1)

	def map(self, func):
		if self.next is None:
			return LinkedList(func([self.elt]), None)
		dupl = LinkedList(func([self.elt]), self.next.map(func))
		return dupl

	def copy(self):
		return self.map(lambda x: x[0])

	def end(self):
		if self.next is None:
			return self
		return self.next.end()

	def filter(self, func):
		if func([self.elt]):
			if self.next is None:
				return LinkedList(self.elt, None)
			return LinkedList(self.elt, self.next.filter(func))
		if self.next is None:
			return None
		return self.next.filter(func)

	def reduce(self, func, val):
		 if self.next is None:
		 	return func([val, self.elt])
		 return self.next.reduce(func, func([val, self.elt]))

def make_list(args):
	if len(args) == 0:
		return None
	a = LinkedList(args[0], make_list(args[1:]))
	return a

def concat_list(args):
	if len(args) == 0:
		return None
	if args[0] == None:
		return concat_list(args[1:])
	dupl = args[0].copy()
	dupl.end().next = concat_list(args[1:])
	return dupl

carlae_builtins = Environment(init_dict = {
    '+': sum,
    '-': lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),   
    '*': mult,
    '/': div,
    '=?': lambda args: boolean_func((lambda x, y: x == y))(args),
    '>': lambda args: boolean_func((lambda x, y: x > y))(args),
    '>=': lambda args: boolean_func((lambda x, y: x >= y))(args),
    '<': lambda args: boolean_func((lambda x, y: x < y))(args),
    '<=': lambda args: boolean_func((lambda x, y: x <= y))(args),
    '#t': True,
    '#f': False,
    'not': lambda args: not args[0],
    'list': lambda args: make_list(args),
    'concat': lambda args: concat_list(args), 
    'begin': lambda args: args[::-1][0],
})

class Function():
	def __init__(self, param = [], express = [], envrmt = None):
		self.pm = param
		self.exp = express
		self.environment = envrmt

	def set(self, filler = []):
		if len(self.pm) != len(filler):
			raise EvaluationError("EvaluationError")

		new_env = Environment(self.environment)
		ret = Function(self.pm, self.exp, new_env)
		for i in range(len(filler)):
			ret.environment.env[self.pm[i]] = filler[i]
		return ret

def eval_func(func):
	def param(args):
		if isinstance(func, Function):
			ret = func.set(args)
			return result_and_env(ret.exp, ret.environment)[0]
		return func(args)
	return param

def result_and_env(tree, cur_env = None):
	"""Evaluates the expression from parser's output"""
	
	if cur_env is None:
		if __name__ == '__main__':
			cur_env = carlae_builtins
		else:
			cur_env = Environment(carlae_builtins)

	new_env = Environment(parent = cur_env)

	if isinstance(tree, int) or isinstance(tree, float):
		return tree, cur_env

	if isinstance(tree, str):#different from Unicode
		if cur_env.get(tree) is NULL:
			raise EvaluationError("EvaluationError")
		return cur_env.get(tree), cur_env

	if isinstance(tree, list) and len(tree) == 0:
		raise EvaluationError("EvaluationError")

	if tree[0] == 'define':
		name = tree[1]
		if isinstance(name, list):
			param = name[1:]
			name = name[0]
			express = tree[2]
			cur_env.env[name] = Function(param, express, new_env)
		else:
			cur_env.env[name] = result_and_env(tree[2], cur_env)[0]

		return cur_env.get(name), cur_env

	if tree[0] == 'lambda':
		param = tree[1]
		express = tree[2]
		lmbda = Function(param, express, new_env)
		return lmbda, cur_env

	if tree[0] == 'if':
		cond = result_and_env(tree[1], cur_env)[0]
		trueexp = tree[2]
		falseexp = tree[3]
		if cond:
			return result_and_env(trueexp, cur_env)[0], cur_env
		return result_and_env(falseexp, cur_env)[0], cur_env

	if tree[0] == 'and':
		for i in tree[1:]:
			boolean = result_and_env(i, cur_env)[0]
			if not boolean:
				return False, cur_env
		return True, cur_env

	if tree[0] == 'or':
		for i in tree[1:]:
			boolean = result_and_env(i, cur_env)[0]
			if boolean:
				return True, cur_env
		return False, cur_env

	if tree[0] == 'car':
		ll = result_and_env(tree[1], cur_env)[0]
		if ll is None:
			raise EvaluationError("EvaluationError")
		return ll.elt, cur_env

	if tree[0] == 'cdr':
		ll = result_and_env(tree[1], cur_env)[0]
		if ll is None:
			raise EvaluationError("EvaluationError")
		return ll.next, cur_env

	if tree[0] == 'length':
		ll = result_and_env(tree[1], cur_env)[0]
		if ll is None:
			return 0, cur_env
		return ll.length(), cur_env

	if tree[0] == 'elt-at-index':
		ll = result_and_env(tree[1], cur_env)[0]
		index = tree[2]
		if ll is None:
			raise EvaluationError("EvaluationError")
		return ll.at_index(index), cur_env

	if tree[0] == 'map':
		f = result_and_env(tree[1], cur_env)[0]
		ll = result_and_env(tree[2], cur_env)[0]
		if ll is None:
			return None, cur_env
		newll = ll.map(eval_func(f))
		return newll, cur_env

	if tree[0] == 'filter':
		f = result_and_env(tree[1], cur_env)[0]
		ll = result_and_env(tree[2], cur_env)[0]
		if ll is None:
			return None, cur_env
		newll = ll.filter(eval_func(f))
		return newll, cur_env

	if tree[0] == 'reduce':
		f = result_and_env(tree[1], cur_env)[0]
		ll = result_and_env(tree[2], cur_env)[0]
		initval = result_and_env(tree[3], cur_env)[0]
		if ll is None:
			raise EvaluationError("EvaluationError")
		return ll.reduce(eval_func(f), initval), cur_env

	if tree[0] == 'let':
		for pair in tree[1]:
			var = pair[0]
			val = result_and_env(pair[1], cur_env)[0]
			new_env.set(var, val)
		return result_and_env(tree[2], new_env)[0], cur_env

	if tree[0] == 'set!':
		name = tree[1]
		exp = result_and_env(tree[2], cur_env)[0]
		if cur_env.set_bang(name, exp) == None:
			raise EvaluationError("EvaluationError")
		return exp, cur_env

	if not isinstance(tree[0], list) and not isinstance(tree[0], str):
		raise EvaluationError("EvaluationError")

	filler = []
	for i in tree[1:]:
		filler.append(result_and_env(i, cur_env)[0])
	func = result_and_env(tree[0], cur_env)[0]
	return eval_func(func)(filler), cur_env

def evaluate(abt, cur_env = None):#abt = abstract syntax tree
	return result_and_env(abt, cur_env)[0]

def evaluate_file(file_name, cur_env = None):
	"""Evaluate expression within the file"""
	f = open(file_name, 'r')
	s = f.read()
	f.close()
	return evaluate(parse(tokenize(s)), cur_env)

def REPL():
	"""A prompt-read-eval-print loop"""
	repl_env = Environment(carlae_builtins)

	for i in sys.argv[1:]:
		evaluate_file(i, repl_env)

	while True:
		source = raw_input('lab_Archer.py> ')
		if source == 'QUIT':
			return
		try:
			#print('out> ', evaluate(source), repl_env)
			print('out> ', evaluate(parse(tokenize(source)), repl_env))
		except EvaluationError as e:
			print('out> ', e)

# if __name__ == '__main__':
# 	REPL()




