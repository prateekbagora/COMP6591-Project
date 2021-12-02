import argparse
import contelog_parser
import copy
import pandas as pd
import numpy as np
import operator
import itertools
from elements import Fact, Rule, Query, Predicate, Constraint, Context

parser = argparse.ArgumentParser(description = 'Contelog implementation with bottom-up semi-naive evaluation')
parser.add_argument('file', help = 'Contelog program file')
args = parser.parse_args()

theta_operations = {'<' : operator.lt, '>' : operator.gt, '<=' : operator.le, '>=' : operator.ge, '!=' : operator.ne, '=' : operator.eq}

def main():

    # stores various types of program program statements
    contexts = []
    facts = []
    rules = []
    queries = []

    # dictionaries of data frames for the relations/predicates
    EDB = {}
    IDB = {}
    CDB = {}

    # lists of relation/predicate names
    EDB_relations = []
    IDB_relations = []
    CDB_relations = []

    # contelog parser to read and parse the input program
    parser = contelog_parser.parser
    file = open(args.file, 'r')
    program = parser.parse(file.read())

    # return if the program is empty
    if not program:
        return

    # reorder program statements in the order: context, facts, rules, queries
    program = reorder_program(program)

    # processing each program statement
    # segregating them in different lists
    # generating the corresponding data frames and name lists for relations/predicates
    for element in program:

        # processing context type statements
        if element.type == 'context':
            contexts.append(element)

            # for each dimension in the context, generate data frames of records with the structure
            # (dimension attribute, context) that is from: (east, c1), (west, c2)

            for predicate in element.contextual_predicates:
                argument_list = predicate.arguments
                records = []

                # if argument list is a list of lists
                if isinstance(argument_list[0], list):
                    for argument in argument_list:
                        records.append(argument + [predicate.context])

                # if argument list is a list of elementary types
                else:
                    for argument in argument_list:
                        records.append([argument, predicate.context])

                if predicate.name not in CDB_relations:

                    # create a new data frame in CDB if it does not already exist
                    CDB[predicate.name] = pd.DataFrame(data = records, index = None)
                    CDB_relations.append(predicate.name)

                else:

                    # append the context information to the data frame if it already exists
                    CDB[predicate.name] = CDB[predicate.name].append(records, ignore_index = True)

        # for facts, generate data frames of records with the structure
        # (argument_1, argument_2,..., context) that is per: (john, east, none), (rose, west, none)
        elif element.type == 'fact':
            facts.append(element)
            record = element.predicate.arguments + [element.predicate.context]

            if element.predicate.name not in EDB_relations:

                # create a new data frame in EDB if it does not already exist
                EDB[element.predicate.name] = pd.DataFrame(data = [record], index = None)
                EDB_relations.append(element.predicate.name)

            else:
                # append the fact to the corresponding data frame if it already exists
                EDB[element.predicate.name] = EDB[element.predicate.name].append([record], ignore_index = True)

        # processing rule type statements
        elif element.type == 'rule':
            rules.append(element)

            # create a new empty data frame for rule head predicate in IDB if it does not already exist in IDB
            # with columns (argument1, argument2,..., context) that is side: (X, Z, C)
            if not element.head.name in IDB_relations:
                column_header = element.head.arguments + [element.head.context]
                IDB[element.head.name] = pd.DataFrame(columns = column_header)
                IDB_relations.append(element.head.name)

            for predicate in element.body:
                if predicate.type != 'constraint':

                    # changing the type of contextual predicates for later use
                    if predicate.name in CDB_relations:
                        predicate.type = 'contextual_predicate'

                    # if predicate does not already occur in EDB and IDB then create a new data frame for it
                    elif not ((predicate.name in EDB_relations) or (predicate.name in IDB_relations)):
                        column_header = predicate.arguments + [predicate.context]
                        IDB[predicate.name] = pd.DataFrame(columns = column_header)
                        IDB_relations.append(predicate.name)

        # processing query type statements
        elif element.type == 'query':
            queries.append(element)

    # if a predicate is found in both EDB and IDB, move it to IDB only
    for relation in EDB_relations:
        if relation in IDB_relations:
            IDB[relation] = EDB[relation]
            EDB.pop(relation)
            EDB_relations.remove(relation)

    # reordering rule body predicates in the order: IDB predicates, CDB predicates, EDB predicates, constraints
    rules = reorder_rule_bodies(rules, EDB_relations, IDB_relations, CDB_relations)

    # semi-naive bottom-up evaluation to derive all facts
    IDB = bottom_up_evaluation(rules, EDB, IDB, CDB, EDB_relations, IDB_relations, CDB_relations)

    # display results
    print_results(EDB, IDB, queries)

def check_safety(element):
    #safety checks
    isSafe = True
    unsafe_vars = []
    #check that variables in the head occur in the body as well
    if(element.type == 'rule'):
        # 'body' arguments: [['X','Y'],['Y','Z']]
        body_variables = np.hstack([i.arguments for i in element.body])
        head_variables = element.head.arguments
        for var_head in head_variables:
            if var_head not in body_variables:
                unsafe_vars.append(var_head)
                isSafe = False
                print('Unsafe rule found:\n',element)
                
    #check that facts are all ground
    if(element.type == 'fact'):
        record = element.predicate.arguments + [element.predicate.context]
        constants = [argument for argument in record if not is_upper_case(argument)]
        if(len(record) != len(constants)):
            isSafe = False
            unsafe_vars.append(args)
            print('Facts must be gound. Variable found in fact:\n',record)
            
    #check that context arguments are all constants
    if(element.type == 'context'):
        for context in element.contextual_predicates:
            constants = [argument for argument in context.arguments if not is_upper_case(argument)]
            if(len(context.arguments) != len(constants)):
                isSafe = False
                print('Context attributes must be constants:',constants)
        
    return isSafe, unsafe_vars

def reorder_program(program):
    """
    reorders program statements in the order: context, facts, rules, queries
    """
    contexts = []
    facts = []
    rules = []
    queries = []

    for element in program:
        
        if not check_safety(element)[0]:
            continue
            
        if element.type == 'context':
            contexts.append(element)
        elif element.type == 'fact':
            facts.append(element)
        elif element.type == 'rule':
            rules.append(element)
        elif element.type == 'query':
            queries.append(element)

    return contexts + facts + rules + queries

def reorder_rule_bodies(rules, EDB_relations, IDB_relations, CDB_relations):
    """
    reordering all rules bodies to get predicates in the order: IDB predicates, CDB predicates, EDB predicates, constraints
    """
    for rule in rules:
        EDB_predicates = []
        IDB_predicates = []
        CDB_predicates = []
        constraints = []

        for predicate in rule.body:
            if predicate.type == 'constraint':
                constraints.append(predicate)
            elif predicate.name in EDB_relations:
                EDB_predicates.append(predicate)
            elif predicate.name in IDB_relations:
                IDB_predicates.append(predicate)
            elif predicate.name in CDB_relations:
                CDB_predicates.append(predicate)            

        rule.body = IDB_predicates + CDB_predicates + EDB_predicates + constraints

    return rules

def bottom_up_evaluation(rules, EDB, IDB, CDB, EDB_relations, IDB_relations, CDB_relations):

    # copies of relation/predicate dictionaries holding the dataframes
    EDB = copy.deepcopy(EDB)
    CDB = copy.deepcopy(CDB)

    # create an empty data frames structure of IDB
    IDB_empty = copy.deepcopy(IDB)

    for key in IDB_empty.keys():
        IDB_empty[key].drop(IDB_empty[key].index, inplace = True)

    # holds IDB facts from T(i-2)
    IDB_old = copy.deepcopy(IDB_empty)

    # holds IDB facts from T(i-1)
    IDB_delta = copy.deepcopy(IDB)

    # holds IDB facts derived in current step T(i)
    IDB_new = copy.deepcopy(IDB_empty)

    while(True):

        # processing each rule
        for rule in rules:

            # stores facts generated by the current rule
            new_facts = pd.DataFrame()

            # lists relation/predicate indices for local use
            EDB_list = []
            IDB_list = []
            CDB_list = []

            # stores temporary copies of predicate data frames filtered according to the rule
            EDB_temp = {}
            IDB_old_temp = {}
            IDB_delta_temp = {}
            CDB_temp = {}

            # counters to update relation/predicate index lists 
            EDB_counter = 0
            IDB_counter = 0
            CDB_counter = 0

            # empty data frame flag
            not_empty = True

            # holds constraints as tuples of the form (variable, theta operator, variable/constant)
            constraint_list = []

            # processing each predicate in the rule
            for predicate in rule.body:

                # add constraint conditions to constraint list
                if predicate.type == 'constraint':
                    constraint_condition = (predicate.term_x, predicate.theta, predicate.term_y)
                    constraint_list.append(constraint_condition)

                else:

                    if predicate.name in EDB_relations:

                        # if an EDB predicate's data frame is empty, the result of the rule will also be empty
                        # hence, skip the rule
                        if EDB[predicate.name].empty:
                            not_empty = False
                            break

                        # add a copy of the predicate's data frame to temporary data frame dictionary with counter as the key
                        EDB_list.append(EDB_counter)
                        EDB_temp[EDB_counter] = copy.deepcopy(EDB[predicate.name])

                        # rename the data frame's columns according to the predicate's arguments and context
                        column_header = predicate.arguments + [predicate.context]
                        EDB_temp[EDB_counter].columns = column_header

                        # for each constant in the predicate's arguments or context, filter the data frame records for the constant
                        for constant in get_constants(column_header):
                            EDB_temp[EDB_counter] = EDB_temp[EDB_counter][EDB_temp[EDB_counter][constant] == constant]

                        # if the context is variable, filter out none context
                        if is_upper_case(predicate.context):
                            EDB_temp[EDB_counter] = EDB_temp[EDB_counter][EDB_temp[EDB_counter][predicate.context] != 'none']

                        EDB_counter += 1

                    elif predicate.name in CDB_relations:

                        # if a CDB predicate's data frame is empty, the result of the rule will also be empty
                        # hence, skip the rule
                        if CDB[predicate.name].empty:
                            not_empty = False
                            break

                        # add a copy of the predicate's data frame to temporary data frame dictionary with counter as the key
                        CDB_list.append(CDB_counter)
                        CDB_temp[CDB_counter] = copy.deepcopy(CDB[predicate.name])

                        # rename the data frame's columns according to the predicate's arguments and context

                        column_header = predicate.arguments + [predicate.context]
                        CDB_temp[CDB_counter].columns = column_header

                        # for each constant in the predicate's arguments or context, filter the data frame records for the constant
                        for constant in get_constants(column_header):
                            CDB_temp[CDB_counter] = CDB_temp[CDB_counter][CDB_temp[CDB_counter][constant] == constant]

                        # if the context is variable, filter out none context
                        if is_upper_case(predicate.context):
                            CDB_temp[CDB_counter] = CDB_temp[CDB_counter][CDB_temp[CDB_counter][predicate.context] != 'none']

                        CDB_counter += 1

                    else:

                        # if IDB predicate's old and delta both data frames are empty, the result of the rule will also be empty
                        # hence, skip the rule
                        if (IDB_old[predicate.name].empty) and (IDB_delta[predicate.name].empty):
                            not_empty = False
                            break

                        # add copies of the predicate's old and delta data frames to corresponding temporary data frame dictionaries with counter as the key
                        IDB_list.append(IDB_counter)
                        IDB_old_temp[IDB_counter] = copy.deepcopy(IDB_old[predicate.name])
                        IDB_delta_temp[IDB_counter] = copy.deepcopy(IDB_delta[predicate.name])

                        # rename the data frames' columns according to the predicate's arguments and context
                        column_header = predicate.arguments + [predicate.context]
                        IDB_old_temp[IDB_counter].columns = column_header
                        IDB_delta_temp[IDB_counter].columns = column_header

                        # for each constant in the predicate's arguments or context, filter the data frame records for the constant
                        for constant in get_constants(column_header):
                            IDB_old_temp[IDB_counter] = IDB_old_temp[IDB_counter][IDB_old_temp[IDB_counter][constant] == constant]
                            IDB_delta_temp[IDB_counter] = IDB_delta_temp[IDB_counter][IDB_delta_temp[IDB_counter][constant] == constant]

                        # if the context is variable, filter out none context
                        if is_upper_case(predicate.context):
                            IDB_old_temp[IDB_counter] = IDB_old_temp[IDB_counter][IDB_old_temp[IDB_counter][predicate.context] != 'none']
                            IDB_delta_temp[IDB_counter] = IDB_delta_temp[IDB_counter][IDB_delta_temp[IDB_counter][predicate.context] != 'none']

                        IDB_counter += 1

            # check for empty data frame flag
            if(not_empty):

                # if there is at least one IDB predicate in the rule body
                if len(IDB_list):

                    # get all combinations of old and delta data frames for predicates we need to consider for joins in the semi-naive evaluation
                    # if there two predicates, the combinations would be (0, 1), (1, 0) and (1, 1)
                    # 0 stands for old data frame and 1 stands for new data frame of the predicate in question
                    combinations = get_combinations(IDB_list)

                    for combination in combinations:

                        # flag to check for empty combination results
                        non_empty_combination = True

                        # stores records derived from the current combination
                        combination_facts = pd.DataFrame()

                        # if first data frame in the combination is empty, continue to check next combination
                        if combination[0] == 0:
                            if IDB_old_temp[0].empty:
                                continue
                            combination_facts = IDB_old_temp[0]

                        elif combination[0] == 1:
                            if IDB_delta_temp[0].empty:
                                continue
                            combination_facts = IDB_delta_temp[0]

                        # proceed to check next predicates in the current combination
                        for relation_index in IDB_list[1 : len(IDB_list)]:

                            # if current combination element is 0 use old data frame, otherwise use delta data frame of the predicate 
                            join_using = IDB_old_temp if combination[relation_index] == 0 else IDB_delta_temp

                            # if an empty data frame in encountered in the combination, mark the empty combination flag
                            # continue to check next combination
                            if join_using[relation_index].empty:
                                non_empty_combination = False
                                break

                            # find common arguments between the predicates by finding out common headings between the data frames
                            join_on = get_common_arguments(combination_facts, join_using[relation_index])

                            # if common arguments are found, perform an inner join
                            if len(join_on):
                                combination_facts = combination_facts.merge(join_using[relation_index], left_on = join_on, right_on = join_on, how = 'inner')

                            # if common arguments are not found, perform a cross join
                            else:

                                # using a dummy column key to perform cross join
                                combination_facts['key'] = 0
                                join_using[relation_index]['key'] = 0
                                combination_facts = combination_facts.merge(join_using[relation_index], on = 'key', how = 'outer').drop(['key'], axis = 1)

                        # if at least one record is derived by the combination, accumulate the records for later operations
                        if non_empty_combination:
                            if new_facts.empty:
                                new_facts = combination_facts
                            else:
                                new_facts.append(combination_facts, ignore_index = True)

                # if there is at least one CDB predicate in the rule body, and
                #   either there are no IDB predicates in the rule body, or
                #   if there are IDB predicates in the rule body, then at least one record was derived from them
                if len(CDB_list) and ((len(IDB_list) == 0) or (len(IDB_list) and (not new_facts.empty))):
                    start = 0

                    # if there were no IDB predicates in the rule body, initialize the new facts data frame from the first CDB predicate's data frame
                    if new_facts.empty:
                        new_facts = CDB_temp[0]
                        start = 1

                    # if there are more than one CDB predicates in the rule body
                    if len(CDB_list) > 0:

                        # proceed to check next CDB predicates in the rule body
                        for relation_index in CDB_list[start : len(CDB_list)]:

                            # find common arguments between the predicates by finding out common headings between the data frames
                            join_on = get_common_arguments(new_facts, CDB_temp[relation_index])

                            # if common arguments are found, perform an inner join
                            if len(join_on):
                                new_facts = new_facts.merge(CDB_temp[relation_index], left_on = join_on, right_on = join_on, how = 'inner')

                            # if common arguments are not found, perform a cross join
                            else:

                                # using a dummy column key to perform cross join
                                new_facts['key'] = 0
                                CDB_temp[relation_index]['key'] = 0
                                new_facts = new_facts.merge(CDB_temp[relation_index], on = 'key', how = 'outer').drop(['key'], axis = 1)

                # if there is at least one EDB predicate in the rule body
                # and
                #   either there are no IDB predicates in the rule body
                #   or
                #   if there are IDB predicates in the rule body, then at least one record was derived from them    
                # and
                #   either there are no CDB predicates in the rule body
                #   or
                #   if there are CDB predicates in the rule body, then at least one record was derived from them    

                if len(EDB_list) and ((len(IDB_list) == 0) or (len(IDB_list) and (not new_facts.empty))) and ((len(CDB_list) == 0) or (len(CDB_list) and (not new_facts.empty))):
                    start = 0

                    # if there were no IDB or CDB predicates in the rule body, initialize the new facts data frame from the first EDB predicate's data frame
                    if new_facts.empty:
                        new_facts = EDB_temp[0]
                        start = 1

                    # if there are more than one EDB predicates in the rule body
                    if len(EDB_list) > 0:

                        # proceed to check next EDB predicates in the rule body
                        for relation_index in EDB_list[start : len(EDB_list)]:

                            # find common arguments between the predicates by finding out common headings between the data frames
                            join_on = get_common_arguments(new_facts, EDB_temp[relation_index])

                            # if common arguments are found, perform an inner join
                            if len(join_on):
                                new_facts = new_facts.merge(EDB_temp[relation_index], left_on = join_on, right_on = join_on, how = 'inner')

                            # if common arguments are not found, perform a cross join
                            else:

                                # using a dummy column key to perform cross join
                                new_facts['key'] = 0
                                EDB_temp[relation_index]['key'] = 0
                                new_facts = new_facts.merge(EDB_temp[relation_index], on = 'key', how = 'outer').drop(['key'], axis = 1)

                # is at least one record was derived from the rule body
                if not new_facts.empty:

                    # apply comparison operations or costraints
                    for constraint in constraint_list:

                        # comparison operation between two variables
                        # applied on columns with the column headings which correspond to these variables
                        if is_upper_case(constraint[2]):
                            new_facts = new_facts[theta_operations[constraint[1]](new_facts[constraint[0]], new_facts[constraint[2]])]

                        # comparison operation between a variables and a constant
                        # applied on the column with the column heading corresponding to the variable
                        elif not is_upper_case(constraint[2]):
                            new_facts = new_facts[theta_operations[constraint[1]](new_facts[constraint[0]], constraint[2])]

                    # column header created from the arguments and context of the rule head
                    column_header = rule.head.arguments + [rule.head.context]              

                    # for each constant in the rule head's arguments or context, add a column with the constant value in the new facts data frame
                    constants = get_constants(column_header)
                    for constant in constants:
                        new_facts[constant] = constant

                    # get the required columns from new facts data frame as suggested by the rule head's arguments and context
                    new_facts = new_facts[column_header]

                    # add the facts derived to IDB new
                    new_facts.columns = IDB_new[rule.head.name].columns
                    IDB_new[rule.head.name] = IDB_new[rule.head.name].append(new_facts, ignore_index = True)

                    # drop any duplicate facts from IDB new
                    IDB_new[rule.head.name] = IDB_new[rule.head.name].drop_duplicates()

        # update IDB old by merging IDB old with IDB delta
        IDB_old = get_merged_DB(IDB_old, IDB_delta)

        # update IDB delta with the set difference of IDB_old and IDB new
        IDB_delta = get_delta_DB(IDB_old, IDB_new)

        # if no new facts are derived, then the evaluation is complete
        count = get_count(IDB_delta)
        if count == 0:
            break

        # set IDB new to empty for next iteration
        IDB_new = copy.deepcopy(IDB_empty)

    return IDB_old

def get_merged_DB(DB_old, DB_delta):
    """
    merges two dictionaries of data frames
    """
    DB_merged = {}

    for predicate in DB_old.keys():
        DB_merged[predicate] = copy.deepcopy(DB_old[predicate])
        if predicate in DB_delta.keys():
            DB_merged[predicate] = DB_merged[predicate].append(DB_delta[predicate], ignore_index = True)
        DB_merged[predicate] = DB_merged[predicate].drop_duplicates()

    for predicate in DB_delta.keys():
        if predicate not in DB_old.keys():
            DB_merged[predicate] = copy.deepcopy(DB_delta[predicate])

    return DB_merged

def get_delta_DB(DB_old, DB_new):
    """
    returns the set difference of two data frames
    """
    DB_delta = {}

    for predicate in DB_new.keys():
        DB_delta[predicate] = DB_new[predicate].merge(DB_old[predicate], how = 'left', indicator = True)
        DB_delta[predicate] = DB_delta[predicate][DB_delta[predicate]['_merge'] == 'left_only'].drop(columns = ['_merge'])

    return DB_delta

def get_count(DB):
    """
    returns the count of all the rows in all the data frames in a dictionary of data frames
    """
    count = 0

    for key in DB.keys():
            count += len(DB[key].axes[0])

    return count

def get_constants(columns):
    """
    returns a list of all the constants (column names starting with lower case letters)
    """
    return [argument for argument in columns if not is_upper_case(argument)]

def get_variables(columns):
    """
    returns a list of all the variables (column names starting with upper case letters)
    """
    return [argument for argument in columns if is_upper_case(argument)]

def is_upper_case(s):
	return isinstance(s, str) and s[0].isupper()

def get_common_arguments(table_1, table_2):
    """
    returns a list of all the common columns between the two tables
    """
    return np.intersect1d(table_1.columns._data, table_2.columns._data).tolist()

def get_combinations(predicates):
    """
    returns a list of all the ways of selecting n elements from two lists of length n
    where the element at index i can be selected from either list 1 or list 2
    for example, for a list of length 3 passed as an argument to the function, the combinations generated will be
    [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1]]
    where 0 indicates a selection from list 1 and 1 indicates a selection from list 2 
    """
    predicate_count = len(predicates)
    predicate_indices = range(0, predicate_count)
    subsets = []

    for subset_size in range(1, predicate_count + 1):
        for subset in itertools.combinations(predicate_indices, subset_size):
            subsets.append(subset)

    predicate_combinations = []

    for set in subsets:
        predicate_combination = [1 if index in set else 0 for index in range(0, predicate_count)]
        predicate_combinations.append(predicate_combination)

    return predicate_combinations 

def print_results(EDB, IDB, queries):
    """
    prints the results obtained from the evaluation
    if no queries are passed, it will print all the obtained results
    if queries are passed, it will generate responses to the queries
    """
    if not len(queries):
        print('>>> All inferences from the program:')

        for key in IDB.keys():
            print_data_frame(IDB[key], key)

def print_data_frame(data_frame, predicate):

    for index, row in data_frame.iterrows():
        row_len = len(row)

        if row[row_len - 1] == 'none':
            print('    ' + predicate + '(' + ', '.join(row[0 : row_len - 1]) + ').')
        else:
            print('    ' + predicate + '(' + ', '.join(row[0 : row_len - 1]) + ')@' + row[row_len - 1] + '.')

main()