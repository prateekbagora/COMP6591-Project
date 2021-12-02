import ply.yacc as yacc

from tokenizer import tokens
from elements import Fact, Rule, Query, Predicate, Constraint, Context

def p_program(p):
    """
    program : contexts facts rules queries
            | contexts facts queries rules
            | contexts rules facts queries
            | contexts rules queries facts
            | contexts queries facts rules
            | contexts queries rules facts
            | contexts facts rules
            | contexts rules facts
            | contexts rules queries
            | contexts queries rules
            | facts rules queries
            | facts queries rules
            | rules facts queries
            | rules queries facts
            | queries facts rules
            | queries rules facts
            | contexts facts
            | contexts rules
            | contexts queries
            | facts rules
            | rules facts            
            | facts queries
            | queries facts    		
            | rules queries
    		| queries rules    		
            | contexts
            | facts
    		| rules
    		| queries
    """
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = p[1] + p[2]
    elif len(p) == 4:
        p[0] = p[1] + p[2] + p[3]
    elif len(p) == 5:
        p[0] = p[1] + p[2] + p[3] + p[4]

def p_contexts_list(p):
    """
    contexts : contexts context
             | context
    """
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 3:
        p[0] = p[1] + [p[2]]

def p_context(p):
    """
    context : LOWER_NAME THETA OPEN_CURLY pairs CLOSE_CURLY PERIOD
    """
    p[0] = Context(p[1], p[4])

def p_pairs_list(p):
    """
    pairs : pairs COMMA pair
          | pair
    """
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 4:
        p[0] = p[1] + [p[3]]

def p_pair(p):
    """
    pair : LOWER_NAME COLON OPEN_SQUARE elements CLOSE_SQUARE
    """
    p[0] = Predicate(name = p[1], arguments = p[4], type = 'contextual_predicate')

def p_elements_list(p):
    """
    elements : elements COMMA element
             | element
    """
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 4:
        p[0] = p[1] + [p[3]]

def p_element(p):
    """
    element : attribute
            | OPEN_SQUARE attributes CLOSE_SQUARE
    """
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 4:
        p[0] = p[2]

def p_attributes_list(p):
    """
    attributes : attributes COMMA attribute
               | attribute
    """
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 4:
        p[0] = p[1] + [p[3]]

def p_attribute(p):
    """
    attribute : LOWER_NAME
    """
    p[0] = p[1]

def p_facts_list(p):
    """
    facts : facts fact
          | fact
    """
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 3:
        p[0] = p[1] + [p[2]]

def p_fact(p):
    """
    fact : predicate PERIOD
    """
    p[0] = Fact(p[1])

def p_rules_list(p):
    """
    rules : rules rule
          | rule
    """
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 3:
        p[0] = p[1] + [p[2]]

def p_rule(p):
    """
    rule : head IMPLY body PERIOD
    """
    p[0] = Rule(p[1], p[3])

def p_queries_list(p):
    """
    queries : queries query
            | query
    """
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 3:
        p[0] = p[1] + [p[2]]

def p_query(p):
    """
    query : predicate_list QUESTION_MARK
    """
    p[0] = Query(p[1])

def p_head(p):
    """
    head : predicate
    """
    p[0] = p[1]

def p_body(p):
    """
    body : predicate_list
    """
    p[0] = p[1]

def p_predicate_list_normal(p):
    """
    predicate_list : predicate_list COMMA predicate
    """
    p[0] = p[1] + [p[3]]

def p_predicate_list_built_in(p):
    """
    predicate_list : predicate_list COMMA constraint
    """
    p[0] = p[1] + [p[3]]

def p_predicate_list_normal_last(p):
    """
    predicate_list : predicate
    """
    p[0] = [p[1]]

def p_predicate_list_built_in_last(p):
    """
    predicate_list : constraint
    """
    p[0] = [p[1]]

def p_predicate(p):
    """
    predicate : LOWER_NAME OPEN_ROUND term_list CLOSE_ROUND
              | LOWER_NAME OPEN_ROUND term_list CLOSE_ROUND ANNOTATION context_name
    """
    if len(p) == 5:
        p[0] = Predicate(p[1], p[3])
    elif len(p) == 7:
        p[0] = Predicate(p[1], p[3], p[6])

def p_context_name(p):
    """
    context_name : LOWER_NAME
                 | UPPER_NAME
    """
    p[0] = p[1]

def p_term_list(p):
    """
    term_list : term_list COMMA term
              | term
    """
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 4:
        p[0] = p[1] + [p[3]]

def p_term_variable(p):
    """
    term : UPPER_NAME
    """
    p[0] = p[1]

def p_term_constant(p):
    """
    term : LOWER_NAME
    """
    p[0] = p[1]
      
def p_constraint_variable(p):
    """
    constraint : UPPER_NAME THETA UPPER_NAME
    """
    p[0] = Constraint(p[1], p[2], p[3])

def p_constraint_constant(p):
    """
    constraint : UPPER_NAME THETA LOWER_NAME
    """
    p[0] = Constraint(p[1], p[2], p[3])

error_list = []

def p_error(p):
    error_list.append("Syntax error in input! " + str(p) + "\n")
    print("Syntax error in input! ", p)

out = open('p.res', 'w')
parser = yacc.yacc(start='program', write_tables = False, debug = False)

if __name__ == '__main__':
    parser = yacc.yacc(start = 'program')
    program = []
    while True:
        try:
            s = input('datalog > ')
        except EOFError:
            break
        if not s: continue
        program = parser.parse(s)
        for element in program:
            print(element)