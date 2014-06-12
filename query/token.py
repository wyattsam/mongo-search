
TK_SPECIAL = ['"', '&', '$']
WHITESPACE = [' ', '\n', '\r', '\t', '\f'] # nevar 4get

class Token(object):
    def __init__(self, value, typ):
        self.v = value
        self.t = typ
    def __str__(self):
        return "%s(%s)" % (self.t, self.v)

class Tokenizer(object):
    def __init__(self, text):
        self.text = list(text)
        self.curr = ""
        self.curr_tok = ""

    def _advance(self):
        self.curr = self.text.pop(0)
        self.curr_tok += self.curr

    def _token(self, t):
        tok = Token(self.curr_tok.strip(), t)
        self.curr_tok = ""
        return tok

    def _get_type(self, ch):
        m = {'"': 'QUOTE',
             '&': 'AMP',
             '$': 'DOLLAR'
             }
        return m[ch]

    def tokenize(self):
        while len(self.text) > 0:
            self._advance()

            # special token
            if len(self.curr_tok) == 1:
                if self.curr_tok in TK_SPECIAL:
                    yield self._token(self._get_type(self.curr_tok))
                    continue
                elif self.curr_tok in WHITESPACE:
                    self._advance()
                    continue
            # ident token
            if self.curr in TK_SPECIAL:
                self.curr_tok = self.curr_tok[:len(self.curr_tok)-1]
                yield self._token("IDENT")
                self.curr_tok = self.curr
                yield self._token(self._get_type(self.curr))

            if self.curr in WHITESPACE:
                yield self._token("IDENT")
        # pinch off the last token
        if len(self.curr_tok) == 1:
            if self.curr_tok in TK_SPECIAL:
                yield self._token(self._get_type(self.curr_tok))
            elif self.curr_tok in WHITESPACE:
                return
        else:
            yield self._token("IDENT")

if __name__ == "__main__":
    import sys
    t = Tokenizer(sys.argv[1])
    for tok in t.tokenize():
        print tok
