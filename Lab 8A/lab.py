import sys

class EvaluationError(Exception):
	pass

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
			return None
		return self.parent.get(v)

carlae_builtins = Environment(init_dict = {
    '+': sum,
    '-': lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),   
    '*': lambda args: mult(args),
    '/': lambda args: div(args),
})

glob_env = Environment(carlae_builtins)

class Function():
	def __init__(self, param = [], express = [], envrmt = None):
		self.pm = param
		self.exp = express
		self.environment = envrmt

	def set(self, filler = [], new_env = None):
		if len(self.pm) != len(filler):
			raise EvaluationError("EvaluationError")
		for i in range(len(filler)):
			new_env.env[self.pm[i]] = filler[i]

def result_and_env(tree, cur_env = None):
	"""Evaluates the expression from parser's output"""
	if cur_env == None:
		cur_env = Environment(glob_env)#What is going on????

	if isinstance(tree, int) or isinstance(tree, float):
		return tree, cur_env

	if isinstance(tree, str):#different from Unicode
		if cur_env.get(tree) == None:
			raise EvaluationError("EvaluationError")
		return cur_env.get(tree), cur_env

	if isinstance(tree, list) and len(tree) == 0:
		raise EvaluationError("EvaluationError")

	new_env = Environment(parent = cur_env)#a;doifja;osdijf;oaidsjf

	if tree[0] == 'define':
		name = tree[1]
		if isinstance(name, list):
			param = name[1:]
			name = name[0]
			express = tree[2]
			tree[2] = ['lambda' , param, express]
		cur_env.env[name] = result_and_env(tree[2], new_env)[0]
		return cur_env.get(name), cur_env

	if tree[0] == 'lambda':
		param = tree[1]
		express = tree[2]
		lmbda = Function(param, express, cur_env)
		return lmbda, cur_env

	if tree[0] == 'if':
		cond = result_and_env(tree[1], new_env)[0]
		if cond == '#t':
			return result_and_env(trueexp, new_env)
		elif cond == '#f':
			return result_and_env(falseexp, new_env)

	filler = []
	for i in tree[1:]:
		filler.append(result_and_env(i, new_env)[0])
	func = result_and_env(tree[0], new_env)[0]

	if isinstance(func, Function):#func = lmbda
		new_env = Environment(parent = func.environment)
		func.set(filler, new_env)
		return result_and_env(func.exp, new_env)[0], cur_env
	if not isinstance(tree[0], list) and not isinstance(tree[0], str):
		raise EvaluationError("EvaluationError")
	return func(filler), cur_env

def evaluate(abt, cur_env = None):#abt = abstract syntax tree
	return result_and_env(abt, cur_env)[0]

def REPL():
	"""A prompt-read-eval-print loop"""
	env = glob_env
	while True:
		source = input('lab_Archer.py> ')
		if source == 'QUIT':
			return
		try:
			print('out> ', evaluate(parse(tokenize(source))))
		except EvaluationError as e:
			print('out> ', e)

# print(evaluate([
#     "define",
#     "x",
#     [
#       "-",
#       [
#         "define",
#         "y",
#         [
#           "*",
#           2,
#           [
#             "define",
#             "z",
#             [
#               "+",
#               [
#                 "define",
#                 "a",
#                 3
#               ],
#               1
#             ]
#           ]
#         ]
#       ],
#       1
#     ]
#   ]))





