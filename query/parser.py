import query_token
from ast import Query, Selector, SourceSelector, \
                IdentTerm, QuotedTerm, ConjTerm, \
                NegativeSelector, ListSelector, \
                GenericSelector, ParseEnd
from ast import Backtrack, QueryParseException, QueryParseEOF
from werkzeug.datastructures import ImmutableMultiDict

### Base parser
class Parser(object):
    def __init__(self, args):
        self.args = args
        if isinstance(args, ImmutableMultiDict):
            self.args = args.to_dict()
        text = args['query']
        self.query = text
        tokenizer = query_token.Tokenizer(text)
        self.tokens = [t for t in tokenizer.tokenize()]
        self.index = 0
        self.curr = self.tokens[self.index]

    def advance(self):
        self.index += 1
        if not self.has_more:
            raise QueryParseEOF(self.curr)
        self.curr = self.tokens[self.index]

    def peek(self, n):
        if len(self.tokens) > self.index + n:
            return self.tokens[self.index + n]

    def many1(self, t):
        while self.curr.t == t and self.has_more:
            yield self.curr
            self.advance()

    def expect1(self, t):
        return self.curr.t == t

    def lookahead(self, t):
        t1 = self.peek(1)
        if t1:
            return t1.t == t

    def vlookahead(self, v):
        v1 = self.peek(1)
        if v1:
            return v1.v == v

    def skip_any(self):
        if self.has_more:
            self.advance()
            return True
        return False

    def try_(self, parser, *args):
        curr_index = self.index
        try:
            return parser(*args) or True
        except QueryParseException:
            self.index = curr_index
            self.curr = self.tokens[self.index]
            return None
        except Backtrack:
            self.index = curr_index
            self.curr = self.tokens[self.index]
            return None

    def consume(self, t):
        if self.expect1(t):
            self.advance()
        else:
            raise Backtrack("expecting %s" % t)

    def conjunct(self, parsers):
        for p, args in parsers:
            try:
                result = p(*args)
                if result:
                    return result
            except:
                continue

    def sep_by(self, list_t, sep_t, list_parser, *args):
        accum = []
        state = list_t
        while self.expect1(list_t) or self.expect1(sep_t):
            if self.expect1(list_t) and state == list_t:
                it = list_parser(*args)
                accum.append(it)
                state = sep_t
            elif self.expect1(sep_t) and state == sep_t:
                self.skip_any()
                state = list_t
            else:
                raise Backtrack("encountered some error in sep_by")
        return accum

    @property
    def has_more(self):
        return self.index < len(self.tokens)

### Parsing
class BasicQuery(Parser):
    def __init__(self, args, ss):
        Parser.__init__(self, args)
        self.subsources = ss
        self._selectors = ['source']

        self.ast = self._query()

    ## Parse rules
    def _query(self):
        selectors = []
        terms = []
        while True:
            try:
                self._do_query(terms, selectors)
                self.advance()
            except QueryParseEOF:
                break
        if not self.expect1('EOF'):
            self._do_query(terms, selectors)
        return Query(terms, selectors)

    def _do_query(self, terms, selectors):
        p = self.peek(1)
        if p and p.t == 'COLON': # it is a selector
            c = self.curr
            try:
                self.advance()
                selectors.append(self.selector(c))
            except Backtrack:
                #thought it was a selector, turned out we were wrong
                #this is probably not necessary anymore. oh well.
                terms.append(IdentTerm(c.v))
        else: # it is a term TODO or a generic selector!
            terms.append(self.term())

    def selector(self, sel):
        self.consume('COLON')
        return self.conjunct([
            (self.not_selector, (sel,)),
            (self.list_selector, (sel,)),
            (self.try_, (self.named_selector, sel)),
            (self.generic_selector, (sel,))
        ])

    def generic_selector(self, sel):
        if not self.expect1('IDENT'):
            raise QueryParseException("expecting ident in generic selector")
        val = self.curr.v
        return GenericSelector(sel, val)

    def named_selector(self, sel):
        return getattr(self, 'selector_'+sel.v)(sel)

    def not_selector(self, sel):
        self.consume('BANG')
        return NegativeSelector(self.named_selector(sel))

    def list_selector(self, sel):
        self.consume('OP_BRACK')
        lst = self.sep_by('IDENT', 'COMMA', self.named_selector, sel)
        self.consume('CL_BRACK')
        return ListSelector(lst)

    def selector_source(self, sel):
        if not self.expect1('IDENT'):
            raise QueryParseException("expecting ident in source selector")
        src = self.curr.v
        if self.lookahead('SLASH'):
            self.advance()
            has_ssrc = self.try_(self.consume, 'SLASH')
            if has_ssrc:
                ret = SourceSelector(sel, src, self.curr.v)
                self.advance()
                return ret
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
        if self.lookahead('AMP') or self.vlookahead('and'):
            self.advance() # skip over peeked token
            if self.skip_any():
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
