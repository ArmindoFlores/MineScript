grammar MineScript;            // Define a grammar called MineScript

prog:   stat+ ;

stat
    :   expr NEWLINE                                            # statement
    |   igexpr NEWLINE                                          # igStatement
    |   '{' stat* '}'                                           # blockstat
    |   variableDeclaration NEWLINE                             # assignStat
    |   igVariableDeclaration NEWLINE                           # igAssignStat
    |   'print' '(' expr (',' expr)* ')' NEWLINE                # print
    |   'for' forControl stat                                   # for
    |   'while' '(' expr ')' stat                               # while
    |   'if' '(' expr ')' stat ('else' stat)?                   # ifElse
    |   'function' ID stat                                      # funcDef      
    |   '$function' ID stat                                     # igFuncDef
    |   '$if' '(' igexpr ')' stat ('$else' stat)?               # igIfElse
    |   '$setdisplay' '(' igexpr ',' DSPL_MODE ')' NEWLINE      # setDisplay
    |   '$for' igForControl stat                                # igFor
    |   '$while' '(' genexpr ')' stat                           # igWhile
    |   '$forentity' '(' expr ';' ID ')' stat                   # igForEntity 
    |   '$execute' '(' expr ')' stat                            # execute
    |   '$mc' '(' expr ')' NEWLINE                              # command
    |   NEWLINE                                                 # blank
    ;

expr
    :   expr op=('*'|'/'|'-'|'+'|'%'|'^') expr     # op
    |   ID                                          # id
    |   literal                                     # constant
    |   array                                       # constantArray
    |   '(' expr ')'                                # parens
    |   expr op=('>'|'<'|'>='|'<='|'=='|'!=') expr  # comparison
    |   '!' expr                                    # not
    |   ID '()'                                     # funcCall
    |   expr '[' expr ']'                           # arrayIndex
    |   expr '.' ID '()'                            # attributeCallEmpty
    |   expr '.' ID '(' expr ')'                    # attributeCall
    |   expr '.' ID                                 # attribute
    |   'len' '(' expr ')'                          # len
    |   'str' '(' expr ')'                          # str
    |   'int' '(' expr ')'                          # int
    |   'float' '(' expr ')'                        # float
    ;

igexpr
    :   '$' ID                                                 # igId
    |   '$' ID '()'                                            # igFuncCall
    |   igexpr op=('>'|'<'|'>='|'<='|'=='|'!=') igexpr         # igComparisonIg
    |   igexpr op=('*'|'/'|'+'|'-'|'%'|'^') igexpr             # igOpIg
    |   igexpr op=('>'|'<'|'>='|'<='|'=='|'!=') expr           # igComparison
    |   igexpr op=('*'|'/'|'+'|'-'|'%'|'^') expr               # igOp
    |   expr op=('>'|'<'|'>='|'<='|'=='|'!=') igexpr           # igComparisonM
    |   expr op=('*'|'/'|'+'|'-'|'%'|'^') igexpr               # igOpM
    |   '(' igexpr ')'                                         # igParens
    |   '$pos(' expr ',' expr ')'                              # getPos
    |   '$isblock' '(' expr ',' expr ',' expr ')'              # isBlock
    |   '$count' '(' expr ')'                                  # count
    |   '$getscore' '(' expr ',' expr ')'                      # getScore
    |   '$hastag' '(' expr ',' expr ')'                        # hasTag
    |   '$print' igPrintControl                                # igPrint
    |   '$tp' '(' expr ',' expr ')'                            # teleport
    |   '$addtag' '(' expr ',' expr ')'                        # addTag
    |   '$remtag' '(' expr ',' expr ')'                        # remTag
    |   '$addobj' '(' expr ',' expr ')'                        # addObj
    |   '$setscore' '(' expr ',' expr ',' genexpr ')'          # setScore
    |   '$getdata' '(' expr ',' expr (',' expr)? ')'           # getData
    ;

genexpr
    :   igexpr 
    |   expr
    ;

forControl
    :   '(' forInit ';' expr ';' forUpdate ')'
    ;

forInit
    :   variableDeclaration
    ;

forUpdate
    :   variableDeclaration
    ;

igForControl
    :   '(' igForInit ';' igexpr ';' igForUpdate ')'
    ;

igForInit
    :   igVariableDeclaration
    ;

igForUpdate
    :   igVariableDeclaration
    ;

igPrintControl
    :   '(' igPrintArg (',' igPrintArg)*  ')'
    ;

igPrintArg
    :   genexpr ('|' COLOR)?
    ;


variableDeclaration
    :   ID '=' expr                                 # assign  
    |   ID op=('++' | '--')                         # assignUnit
    |   ID op=('+='|'-='|'*='|'/='|'%=') expr       # assignOp
    ;

igVariableDeclaration
    :   '$' ID '=' expr                                 # igAssign
    |   '$' ID '=' igexpr                               # igAssignIg
    |   '$' ID op=('++'|'--')                           # igAssignUnit
    |   '$' ID op=('+='|'-='|'*='|'/='|'%=') expr       # igAssignOp
    |   '$' ID op=('+='|'-='|'*='|'/='|'%=') igexpr     # igAssignIgOp
    ;


literal
    : Integer
    | StringLiteral
    | Boolean
    | Float
    ;

array
    : '[' expr? (',' expr)* ']'
    ;

StringLiteral
    : '"' StringCharacter* '"'
    {
    s = self.text
    s = s.replace("\\\"", "\"");
    self.text = s
    }
    ;

Float
    : '-'? [0-9]+ '.' [0-9]+
    ;

Integer
    : '-'? [0-9]+
    ;

Boolean
    : 'true' | 'false'
    ;

DSPL_MODE
    :   'list'
    |   'belowName'
    |   'sidebar' ('.team.' COLOR)?
    ;

COLOR
    :   'aqua'
    |   'black'
    |   'blue'
    |   'dark_aqua'
    |   'dark_blue'
    |   'dark_gray'
    |   'dark_green'
    |   'dark_purple'
    |   'dark_red'
    |   'gold'
    |   'gray'
    |   'green'
    |   'light_purple'
    |   'red'
    |   'white'
    |   'yellow'
    ;


fragment
StringCharacter
    :   ~('\n'|'\r'|'"')
    |   ESCAPED_QUOTE
    ;

fragment ESCAPED_QUOTE
    : '\\"'
    ;

MUL :   '*' ;            // assigns token name to '*' used above in grammar
DIV :   '/' ;
ADD :   '+' ;
SUB :   '-' ;
POW :   '^' ;
MOD :   '%' ;
GT  :   '>' ;
LT  :   '<' ;
GET :   '>=';
LET :   '<=';
EQ  :   '==';
DIF :   '!=';
NOT :   '!' ;
USUM:   '++';
USUB:   '--';
PE  :   '+=';
DE  :   '/=';
MLE :   '*=';
MDE :   '%=';
SE  :   '-=';
ID  :   [a-zA-Z0-9]+ ;   // match identifiers
NEWLINE:'\r'? '\n' ;     // return newlines to parser (is end-statement signal)
WS  :   [ \t]+ -> skip ; // toss out whitespace
COMMENT : '#' ~[\r\n]* -> skip;
