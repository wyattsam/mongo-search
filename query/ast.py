# Copyright 2014 MongoDB Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import json

class InternalVisitor(object):
    class DummyQuery(object):
        def __init__(self):
            self.args = {}

    def __init__(self):
        self.doc = {"$text": {"$search": ""}}
        self.query = InternalVisitor.DummyQuery()

    def keyval(self):
        k = self.doc.keys()[0]
        return (k, self.doc[k])

def parse_advanced(k, arg):
    ineqs = {
        '+': '$gte',
        '-': '$lte'
    }
    #make sure we go all the way down if there is a tree
    if isinstance(arg, dict):
        for k1 in arg.keys():
            #TODO there should be a better way around this
            if not k1 == '$search':
                upd_dict = parse_advanced(k1, arg[k1])
                if upd_dict:
                    arg.update(upd_dict)
        return None
    elif isinstance(arg, str) or isinstance(arg, unicode):
        lastchar = arg[-1:]
        if lastchar in ineqs.keys():
            rest = json.loads(arg[:-1])
            if isinstance(rest, int):
                return {k: {ineqs[lastchar]: rest}}
        else:
            try:
                return {k: json.loads(arg)}
            except:
                return {k: arg}
    else:
        return None

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

        #do extra transforming, very simple rules
        #could probably bake this in somewhere else...?
        #also do we need to do this to args? probably not
        for k in vis.doc.keys():
            if vis.doc[k]:
                upd_dict = parse_advanced(k, vis.doc[k])
                if upd_dict:
                    vis.doc.update(upd_dict)
        return vis.doc

    def __repr__(self):
        return '[QUERY]\n' \
                + "\n".join([repr(s) for s in self.terms]) \
                + "\n" \
                + "\n".join([repr(s) for s in self.selectors])

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
        return '[SELECTOR]\n' + repr(self.sel) + ":\n\t"

class SourceSelector(Selector):
    def __init__(self, sel, src, ssrc):
        Selector.__init__(self, sel)
        self.source = src.lower()
        self.subsource = ssrc

    def accept(self, vis):
        vis.doc['source'] = self.source
        vis.query.args['source'] = self.source
        if self.subsource:
            vis.doc['subsource'] = self.subsource.lower()
            vis.query.args['subsource'] = self.subsource.lower()

    def __str__(self):
        return 'source=' + self.source + ('/' + self.subsource if self.subsource else '')

    def __repr__(self):
        s = Selector.__str__(self)
        ssrc = '[SUBSOURCE] ' + str(self.subsource) if self.subsource else ''
        return s + '[SOURCE] ' + str(self.source) + '\n\t' + ssrc

class GenericSelector(Selector):
    def __init__(self, sel, val):
        Selector.__init__(self, sel)
        self.val = val

    def accept(self, vis):
        vis.query.args[self.sel] = self.val
        vis.doc[self.sel] = self.val

    def __repr__(self):
        s = Selector.__str__(self)
        return s + '[GENERIC]\n' + str(self.sel) + '=' + str(self.val)

class NegativeSelector(Selector):
    def __init__(self, sel):
        Selector.__init__(self, sel)

    def accept(self, vis):
        if isinstance(self.sel, Selector):
            # recurse! we got this.
            vis2 = InternalVisitor()
            self.sel.accept(vis2)
            key,val = vis2.keyval()
            # the $not directive requires a regex here
            if isinstance(val, basestring):
                val = re.compile(val)
            vis.query.args[key] = {'$not': val}
            vis.doc[key] = {'$not': val}

    def __str__(self):
        return 'not(' + str(self.sel) + ')'

    def __repr__(self):
        s = Selector.__str__(self)
        return s + '[NOT]\n' + repr(self.sel)

class ListSelector(Selector):
    def __init__(self, sels):
        self.sels = sels

    def accept(self, vis):
        for sel in self.sels:
            attrs = dir(sel)
            for attr in attrs:
                field = getattr(sel, attr)
                if not (attr[0] == '_' and attr[1] == '_') and (isinstance(field, str) or isinstance(field, unicode)) and not attr == 'sel': #TODO this should only ignore clownshoes
                    if attr not in vis.query.args:
                        vis.query.args[attr] = { '$in': [field] }
                    else:
                        vis.query.args[attr]['$in'].append(field)
                    if attr not in vis.doc:
                        vis.doc[attr] = { '$in': [field] }
                    else:
                        vis.doc[attr]['$in'].append(field)

    def __str__(self):
        return 'list(' + " ".join([str(s) for s in self.sels]) + ')'

    def __repr__(self):
        return '[LIST]\n\t' + "\t".join([repr(s)+'\n' for s in self.sels])

class IdentTerm(Node):
    def __init__(self, val):
        self.val = val

    def accept(self, vis):
        # FIXME: we currently render multiple terms as individual phrases.
        # This is a limitation of the server-side search engine
        # in regards to conjuncting results together
        # instead of disjuncting them. For now this will cause
        # mediocre performance. Fix is on the way!
        vis.doc['$text']['$search'] += '"' + self.val + '" '

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
        vis.doc['$text']['$search'] += '"' + ' '.join(self.vals) + '" '

    def __str__(self):
        return '"' + ' '.join(str(v) for v in self.vals) + '"'

    def __repr__(self):
        return '[QUOTED] ' +  " ".join(repr(v) for v in self.vals)

    def __contains__(self, item):
        return item in self.vals

class NotTerm(Node):
    def __init__(self, term):
        self.term = term

    def accept(self, vis):
        vis2 = InternalVisitor()
        self.term.accept(vis2)
        k,v = vis2.keyval()
        vis.doc['$text']['$search'] += '-'+v['$search']

class DisjunctionTerm(Node):
    def __init__(self, vals):
        self.vals = vals

    def accept(self, vis):
        vis.doc['$text']['$search'] += ' '.join(self.vals) + ' '

    def __str__(self):
        return ' '.join(str(v) for v in self.vals)

    def __repr__(self):
        return '[DISJUNCT] ' +  " ".join(repr(v) for v in self.vals)

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
        self.debug = False
        if self.debug:
            print "[BACKTRACK]", value

    def __str__(self):
        return repr(self.value)

class QueryParseEOF(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class QueryParseException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
