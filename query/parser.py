import token

### AST definition
# TODO should be in its own file maybe
class Node(object):
    def accept(self, vis):
        pass

class Query(Node):
    def __init__(self, terms, selectors):
        self.terms = terms
        self.selectors = selectors
    def accept(self, vis):
        for t in self.terms:
            t.accept(vis)

        #if we have a source/subsource option from the U:, use that
        if 'source' in vis.query.args and vis.query.args['source']:
            vis.doc['source'] = vis.query.args['source']
            ss = vis.query.subsources
            for k in vis.query.subsources.keys():
                if ss[k] and ss[k]['name'] in vis.query.args and vis.query.args[ss[k]['name']]:
                    vis.doc['subsource'] = vis.query.args[ss[k]['field']]

        for s in self.selectors:
            s.accept(vis)
        vis.doc['$text']['$search'] = vis.doc['$text']['$search'].strip()
        return vis.doc

    def __repr__(self):
        return '[QUERY]\n' \
                + "\n".join([str(s) for s in self.terms]) \
                + "\n" \
                + "\n".join([str(s) for s in self.selectors])

    def __contains__(self, item):
        for t in self.terms:
            if item in t:
                return True
        for s in self.selectors:
            if item == s.sel:
                return True
        return False

    def __getitem__(self, key):
        #only search selectors; terms don't have logical name
        for s in self.selectors:
            if key == s.sel:
                return s

class Selector(Node):
    def __init__(self, sel):
        self.sel = sel

    def __str__(self):
        return ''

    def __repr__(self):
        return '[SELECTOR]\n' + str(self.sel) + ":\n\t"

class SourceSelector(Selector):
    def __init__(self, sel, src, ssrc):
        Selector.__init__(self, sel)
        self.src = src
        self.ssrc = ssrc

    def accept(self, vis):
        vis.query.args['source'] = self.src
        if self.ssrc:
            vis.query.args['subsource'] = self.ssrc

    def __str__(self):
        return 'source=' + self.src + ('/' + self.ssrc if self.ssrc else '')

    def __repr__(self):
        s = Selector.__str__(self)
        ssrc = '[SUBSOURCE] ' + str(self.ssrc) if self.ssrc else ''
        return s + '[SOURCE] ' + str(self.src) + '\n\t' + ssrc

class IdentTerm(Node):
    def __init__(self, val):
        self.val = val

    def accept(self, vis):
        vis.doc['$text']['$search'] += self.val + " "

    def __str__(self):
        return str(self.val)

    def __repr__(self):
        return '[IDENT] ' + str(self.val)

    def __contains__(self, item):
        return self.val == item

class QuotedTerm(Node):
    def __init__(self, vals):
        self.vals = vals

    def accept(self, vis):
        vis.doc['$text']['$search'] += '"' + ' '.join([q.val for q in self.vals]) + '" '

    def __str__(self):
        return '"' + ' '.join(str(v) for v in self.vals) + '"'

    def __repr__(self):
        return '[QUOTED] ' +  " ".join(repr(v) for v in self.vals)

    def __contains__(self, item):
        return item in self.vals

class ConjTerm(Node):
    def __init__(self, l, r):
        self.l = l
        self.r = r
    def accept(self, vis):
        vis.doc['$text']['$search'] += '"'
        self._accept(vis)
        vis.doc['$text']['$search'] = vis.doc['$text']['$search'].strip()
        vis.doc['$text']['$search'] += '" '

    def _accept(self, vis):
        if isinstance(self.l, ConjTerm):
            self.l._accept(vis)
        else:
            self.l.accept(vis)

        if isinstance(self.r, ConjTerm):
            self.r._accept(vis)
        else:
            self.r.accept(vis)

    def __str__(self):
        return ' and '.join([str(self.l), str(self.r)])

    def __repr__(self):
        return '[CONJUNCTION] ' +  repr(self.l) + " " + repr(self.r)

    def __contains__(self, item):
        return (item in self.l) or (item in self.r)

class ParseEnd(Node):
    def __repr__(self):
        return '[EOF]\n'

    def __str__(self):
        return ''

    def accept(self, vis):
        vis.doc['$text']['$search'] = vis.doc['$text']['$search'].strip()

    def __contains__(self, item):
        return False

### Exceptions
class Backtrack(Exception):
    def __init__(self, value):
        print "[BACKTRACK]", value

    def __str__(self):
        return repr(self.value)

class QueryParseException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class Parser(object):
    def advance(self):
        self.curr = self.tokens.pop(0)

    def peek(self, n):
        if len(self.tokens) > n:
            return self.tokens[n]

    def many1(self, t):
        while self.curr.t == t and self.has_more:
            yield self.curr
            self.advance()

    def expect1(self, t):
        return self.curr.t == t

    def lookahead(self, t):
        return self.peek(0).t == t

    def skip1(self, t):
        if self.lookahead(t) and self.has_more:
            self.advance()
            return True
        return False

### Parsing
class BasicQuery(Parser):
    def __init__(self, args, ss):
        self.subsources = ss
        self.args = args.to_dict()
        self._selectors = ['source']

        text = args['query']
        self.query = text
        tokenizer = token.Tokenizer(text)
        self.tokens = [t for t in tokenizer.tokenize()]
        self.curr = self.tokens.pop(0)
        self.ast = self._query()

    ## Parse rules
    def _query(self):
        selectors = []
        terms = []
        while True:
            self._do_query(terms, selectors)
            if not self.has_more:
                break
            self.advance()
        # don't forget the last token
        if not self.expect1('EOF'):
            self._do_query(terms, selectors)
        return Query(terms, selectors)

    def _do_query(self, terms, selectors):
        if self.curr.v in self._selectors:
            c = self.curr
            try:
                self.advance()
                selectors.append(self.selector(c))
            except Backtrack:
                terms.append(IdentTerm(c.v))
        else: # it is a term
            terms.append(self.term())

    def selector(self, sel):
        if not self.expect1('COLON'):
            raise Backtrack("expecting :")
        self.advance()
        return getattr(self, 'selector_'+sel.v)(sel)

    def selector_source(self, sel):
        if not self.expect1('IDENT'):
            raise QueryParseException("expecting ident in selector value")
        src = self.curr.v
        if self.peek(0).t == 'SLASH':
            self.advance()
            if self.has_more:
                self.advance()
                return SourceSelector(sel, src, self.curr.v)
        return SourceSelector(sel, src, None)

    def term(self):
        if self.expect1('QUOTE'):
            self.advance()
            ids = [IdentTerm(n.v) for n in self.many1('IDENT')]
            if not self.expect1('QUOTE'):
                raise QueryParseException("expecting close quote")
            return QuotedTerm(ids)
        return self.conj_or_id()

    def conj_or_id(self):
        t1 = None
        if self.expect1('IDENT'):
            t1 = IdentTerm(self.curr.v)
        elif self.expect1('EOF'):
            t1 = ParseEnd()
        p = self.peek(0)
        if p and (p.t == '&' or p.v.lower() == 'and'):
            self.advance() # skip over peeked token
            if self.has_more:
                self.advance()
                return ConjTerm(t1, self.term())
        return t1

    ## Properties
    @property
    def terms(self):
        return " ".join([str(s) for s in self.ast.terms]).strip()

    @property
    def selectors(self):
        return self.ast.selectors

    @property
    def constraints(self):
        return " ".join([str(s) for s in self.ast.selectors]).strip()

    @property
    def has_more(self):
        return len(self.tokens) > 0

class BasicQueryVisitor(object):
    def __init__(self, query):
        self.query = query
        self.doc = {
            '$text': {
                '$search': ''
            }
        }

    def visit_all(self):
        return self.query.ast.accept(self)
