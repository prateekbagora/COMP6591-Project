class Predicate(object):

    def __init__(self, name = '', arguments = [], context = 'none', type = 'predicate'):
        """
        types: predicate, contextual_predicate
        """
        self.name = name
        self.arguments = arguments

        if isinstance(context, list):
            self.context = '+'.join(context)
        else:
            self.context = context

        self.type = type

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '%r' % (self.__dict__)

class Constraint(object):

    def __init__(self, term_x = '', theta = '', term_y = '', type = 'constraint'):
        self.term_x = term_x
        self.theta = theta
        self.term_y = term_y
        self.type = type

    def __repr__(self):
        return '%r' % (self.__dict__)

class Context(object):

    def __init__(self, name = '', contextual_predicates = [], type = 'context'):
        self.name = name
        self.contextual_predicates = contextual_predicates
        self.type = type

        for predicate in self.contextual_predicates:
            predicate.context = self.name

    def __repr__(self):
        return '%r' % (self.__dict__)

class Rule(object):

    def __init__(self, head = {}, body = {}, type = 'rule'):
        self.head = head 
        self.body = body
        self.type = type

    def __repr__(self):
        return '%r' % (self.__dict__)

class Query(object):

    def __init__(self, predicates, type = 'query'):
        self.predicates = predicates
        self.type = type

    def __repr__(self):
        return '%r' % (self.__dict__)

class Fact(object):

    def __init__(self, predicate, type = "fact"):

        self.predicate = predicate
        self.type = type

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '%r' % (self.__dict__)