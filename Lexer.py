# -*- coding: utf-8 -*-
from Queue import Queue
from threading import Thread
from string import ascii_letters, digits
from syntax_elements import *

class Consumed(Exception):
    pass

class LexException(Exception):
    pass


class Lexer(Thread):
    keywords = ("if","else","or","and","while","for","switch","case")
    operators = "+-*/^=~:><"
    def __init__(self,inp, que, name="unnamed lexer"):
        super(Lexer, self).__init__()
        self._inp = inp
        self._que = que
        self._start = 0
        self._pos = 0
        self.name = name
        self.line = 1
        self.indentlevels = [0]

    def _lexInitial(self):
        "Starting State"
        while True:
            current = self._currentChar()

            if current in ascii_letters:
                return self._lexName
            elif current in digits:
                return self._lexNumber
            elif current == '"':
                self._pos += 1
                return self._lexString
            elif current in " \t\n": # ignore whitespace
                self._pos += 1
                self._start = self._pos
                if current == "\n":
                    self.line+=1
                    self._emit("NEWLINE")
                    return self._lexIndentation

            elif current in self.operators:
                return self._lexOperator
            else:
                raise LexException("Unrecognized chracter in line %i" % self.line)

    def _lexOperator(self):

        prev = self._currentChar()
        self._pos+=1
        current = self._currentChar()
        two_chars = prev + current
        if two_chars in ["++","--",">>","<<","==",">","<","!="]:
            self._pos += 1
            self._emit(two_chars)
        else:
            self._emit(prev)
        return self._lexInitial
        

    def _lexIndentation(self):
        current_indent = 0
        while True:
            current = self._currentChar()
            if current == " ":
                self._pos += 1
                current_indent+=1
            elif current == "\t":
                self._pos += 1
                current_indent+=4
            else:
                if current_indent < self.indentlevels[-1]:
                    if current_indent in self.indentlevels:
                        while True:
                            if current_indent < self.indentlevels[-1]:
                                self._emit("DEDENT")
                                self.indentlevels.pop()
                            else:
                                return self._lexInitial
                    else:
                        raise LexException("Congratz! Your indentation is all messed up!")
                elif current_indent > self.indentlevels[-1]:
                    self._emit("INDENT")
                    self.indentlevels.append(current_indent)
                    return self._lexInitial
                else:
                    # yeni tokeni indentten sonra başlat
                    self._start = self._pos
                    return self._lexInitial
                               

    def _lexString(self):
        escape = False
        while True:
            try:
                current = self._currentChar()
            except Consumed:
                raise LexException("Bizim bi string vardi, o nooldu?")
            self._pos += 1
            if escape:
                escape = False
                continue

            if current == '\\':
                escape = True

            elif current == '"':
                    self._emit("STRING")
                    return self._lexInitial()
            elif current == "\n":
                self.line += 1

                

    def _lexName(self):
        def keywordOrName():
            token = self._inp[self._start:self._pos]
            return token in self.keywords and token or "NAME"
        
        while True:
            try:
                current = self._currentChar()
            except Consumed:
                self._emit(keywordOrName())
                raise
            if current in ascii_letters:
                self._pos += 1
            else:
                self._emit(keywordOrName())
                return self._lexInitial

    def _lexNumber(self):
        while True:
            try:
                current = self._currentChar()
            except Consumed:
                self._emit("NUMBER")
                raise
            if current in digits:
                self._pos += 1
            elif current == ".":
                self._pos +=1
                return self._lexFloat
            else:
                self._emit("NUMBER")
                return self._lexInitial

    def _lexFloat(self):
        while True:
            try:
                current = self._currentChar()
            except Consumed:
                self._emit("FLOAT")
                raise
            if current in digits:
                self._pos += 1
            else:
                self._emit("FLOAT")
                return self._lexInitial

    def _currentChar(self):
        try:
            return self._inp[self._pos]
        except IndexError:
            raise Consumed("Input stream is consumed")
                

    def _emit(self, token_type):
        self._que.put((token_type, self.line, self._inp[self._start:self._pos]))
        self._start = self._pos

    def _cleanup(self):
        current_indentation = self.indentlevels.pop()
        while current_indentation != 0:
            self._emit("DEDENT")
            current_indentation = self.indentlevels.pop()
        self._emit("END")

    def run(self):
        state = self._lexInitial
        while True:
            try:
                state = state()
            except Consumed:
                self._cleanup()
                break
            except LexException as e:
                print e.message
                self._emit("END")
                break

if __name__ == "__main__":
    tokenq = Queue()

    with open("test.txt") as dosya:
        myinput = dosya.read()
    
    mylexer = Lexer(myinput, tokenq)
    mylexer.start()
    
    while True:
        ttype, line, value = tokenq.get()
        print "%s: \"%s\"" % (ttype, value) #, line, value
        if ttype == "END":
            break


