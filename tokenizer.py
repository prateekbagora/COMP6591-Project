import ply.lex as lex

literals = [ '+','-','*','/' ]

tokens = ['OPEN_CURLY',    # {
          'CLOSE_CURLY',   # }
          'OPEN_SQUARE',   # [
          'CLOSE_SQUARE',  # ]
          'OPEN_ROUND',    # (
          'CLOSE_ROUND',   # )
          'IMPLY',         # :-
          'COLON',         # :
          'COMMA',         # ,
          'PERIOD',        # .
          'THETA',         # >
          'QUESTION_MARK', # ?
          'ANNOTATION',    # @
          'UPPER_NAME',    # name starting with uppercase
          'LOWER_NAME'     # name starting with lowercase
          ]
    
t_OPEN_CURLY = r'\{'
t_CLOSE_CURLY = r'\}'
t_OPEN_SQUARE = r'\['
t_CLOSE_SQUARE = r'\]'
t_OPEN_ROUND = r'\('
t_CLOSE_ROUND = r'\)'
t_IMPLY = r'\:\-'
t_COLON = r'\:'
t_COMMA = r'\,'
t_PERIOD = r'\.'
t_THETA = r'!=|<=|>=|<|>|='
t_QUESTION_MARK = r'\?'
t_ANNOTATION = r'\@'
t_UPPER_NAME = r'[A-Z][A-Za-z0-9_]*'
t_LOWER_NAME = r'[a-z0-9_][A-Za-z0-9_]*'

t_ignore = ' \t'

def t_comment(token):
    r'[%].*'

def t_error(token):
    print("Illegal character '%s'" % token.value[0])
    token.lexer.skip(1)

def t_newline(token):
    r'\n+'
    token.lexer.lineno += len(token.value)
    
lexer = lex.lex()

if __name__ == '__main__':
    data = """
              % Contexts
              c1 = {from : [east], to : [right]}.
              c2 = {from : [west], to : [left]}.
              % Facts
              p(john,east).
              p(rose,west).
              % Rules
              p(X, Y)@C   p(X, Y), from(Y)@C.
              side(X, Z)@C   p(X, Y)@C, to(Z)@C.
           """
    lexer = lex.lex()
    lexer.input(data)
    
    # Tokenize
    while True:
        token = lexer.token()
        if not token: break
        print(token)