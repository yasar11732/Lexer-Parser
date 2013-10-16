from Lexer import Lexer
from Queue import Queue

class ParseError(Exception):
    pass

class BaseSymbol(object):
    id = None
    value = None
    parent = None
    first = second = third = None
    beginStatement = False

    def nud(self):
        raise ParseError("Parse error (%r)" % self.id)

    def led(self, left):
        raise ParseError("Unknown operator (%r)" % self.id)

    def __repr__(self):
        if self.id in ["NAME","NUMBER","FLOAT","STRING"]:
            return "(%s %s)" % (self.id, self.value)
        out = [self.id, self.first, self.second, self.third]
        return "(" + " ".join(map(str,filter(None,out))) + ")"
        

class Parser(object):
    def __init__(self, queue):
        self._q = queue
        self._sym = {}
        self._prepareSymTable()
        self.token = self._nextToken()


    def _symbol(self, id, bp=0):
        try:
            s = self._sym[id]
        except KeyError:
            class s(BaseSymbol):
                pass
            s.__name__ = "symbol-" + id
            s.id = id
            s.lbp = bp
            s.parent = self
            self._sym[id] = s
        else:
            s.lbp = max(bp, s.lbp)
        return s

    def _prepareSymTable(self):
        
        def statement(id, std):
            self._symbol(id).beginStatement = True
            self._symbol(id).std = std
            
                
        def infix(id, bp):
            def led(self, left):
                self.first = left
                self.second = self.parent.Expression(bp)
                return self
            self._symbol(id, bp).led = led
            
        def infixr(id, bp):
            def led(self, left):
                self.first = left
                self.second = self.parent.Expression(bp-1)
                return self
            self._symbol(id,bp).led = led

        def suffix(id, bp):
            def led(self, left):
                self.first = left
                return self
            self._symbol(id, bp).led = led

        def prefix(id, bp):
            def nud(self):
                self.first = self.parent.Expression(bp)
                return self
            self._symbol(id, bp).nud = nud

        def literal(id):
            self._symbol(id).nud = lambda self: self
            
        for l in ["NUMBER","FLOAT","NAME"]:
            literal(l)

        infix("+",10); infix("-",10); infix("*",20); infix("/",20)
        infix(">",5); infix("<",5)
        
        prefix("+",100); prefix("-",100)

        suffix("++",100); suffix("--",100);
        prefix("++",100); prefix("--",100)
        
        infixr("=",20)

        for s in ["END","INDENT","DEDENT",":"]:
            self._symbol(s)
            
        # ignore empty lines
        statement("NEWLINE", lambda self: None)

        
        def ifStatement(self):
            self.first = self.parent.Expression()
            self.parent._advance([":"])
            self.parent._advance(["NEWLINE"])
            self.second = self.parent.Block()
            if self.parent.token.id == "else":
                self.parent._advance(["else"])
                self.parent._advance([":"])
                self.third = self.parent.Block()
            return self
            
        def whileStatement(self):
            self.first = self.parent.Expression()
            self.parent._advance([":"])
            self.parent._advance(["NEWLINE"])
            self.second = self.parent.Block()
            return self
            
        statement("if", ifStatement)
        statement("while", whileStatement)

    def _nextToken(self):
        ttype, lineno, tvalue = self._q.get(True, 5) # if we can't get a new token in next 5 secs, raise an exception
        self.lineno = lineno      
        s = self._sym[ttype]()

        if ttype in ["NUMBER","FLOAT","STRING","NAME"]:
            s.value = tvalue
        return s
        
    def Block(self):
        self._advance(["INDENT"])
        stmts = self.Statements()
        self._advance(["DEDENT"])
        return stmts

    def Expression(self, rbp=0):
        t = self.token
        self._advance()
        left = t.nud()
        while rbp < self.token.lbp:
            t = self.token
            self._advance()
            left = t.led(left)
        return left
        
    def _advance(self, idlist=None):

        if self.token.id == "END":
            return

        if idlist and self.token.id in idlist:
            self.token = self._nextToken()
        elif not idlist:
            self.token = self._nextToken()
        else:
            raise ParseError("""Expected one of %s
found %r instead. (line: %i)""" % (" ".join(idlist), self.token.id, self.lineno))
        
    def Statement(self):
        t = self.token
        if t.beginStatement:
            self._advance()
            return t.std() 
        ex = self.Expression(0)
        self._advance(["NEWLINE","END","DEDENT"])
        return ex
        
    def Statements(self):
        statements = []
        while True:
            if self.token.id in ["END","DEDENT"]:
                break
            s = self.Statement()
            if s:
                statements.append(s)
        return statements
        
            
        
            
        
if __name__ == "__main__":
    tokenq = Queue()
    
    with open("test.txt") as dosya:
        myinput = dosya.read()
    
    mylexer = Lexer(myinput, tokenq)
    mylexer.start()

    myparser = Parser(tokenq)

    print "parse result:",myparser.Statements()
