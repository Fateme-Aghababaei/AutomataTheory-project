class Grammar:
    class GrammarRule:
        def __init__(self, state: str, terminal: str, variable=''):
            self.state = state
            self.terminal = terminal
            self.variable = variable

        def __str__(self):
            return f'{self.state}-->{self.terminal}{self.variable}'

    def __init__(self, alphabet: list, ruleList=[]):
        self.alphabet = alphabet
        self.alphabet.append('@')
        self.rules = dict()
        for rule in ruleList:
            self.addRule(rule)

    def addRule(self, rule: str):
        rule = rule.split('#')
        state = rule[0]
        terminal = ''
        variable = ''
        if rule[1][-1] not in self.alphabet:
            terminal = rule[1][:-1]
            variable = rule[1][-1]
        else:
            terminal = rule[1]
        if state not in self.rules.keys():
            self.rules[state] = list()
        self.rules[state].append(self.GrammarRule(state, terminal, variable))

    def print(self):
        for state, ruleList in self.rules.items():
            for rule in ruleList:
                print(rule)

    def removeTraps(self):
        for state, ruleList in self.rules.items():
            removeList = list()
            for rule in ruleList:
                if rule.variable != '' and rule.variable not in self.rules.keys():
                    removeList.append(rule)
            for rule in removeList:
                ruleList.remove(rule)

    def substituteVariableIfPossible(self, rule):
        if rule.variable != '' and len(self.rules[rule.variable]) == 1 and rule.variable != 'S':
            deletedVar = rule.variable
            rule.terminal = rule.terminal + (self.rules[rule.variable][0].terminal)
            rule.variable = self.rules[rule.variable][0].variable
            return deletedVar
        return None

    def simplify(self):
        self.removeTraps()
        removeStates = set()
        while True:
            found = False
            for state, ruleList in self.rules.items():
                for rule in ruleList:
                    var = self.substituteVariableIfPossible(rule)
                    if var is not None:
                        removeStates.add(var)
                        found = True
            if not found:
                break
        for state in removeStates:
            del self.rules[state]


class NFA:
    class NFARule:
        def __init__(self, startState: str, endState: str, rule: str):
            self.startState = startState
            self.endState = endState
            self.rule = rule
            self.isLoop = (startState == endState)

    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.statesList = {'S': {'in': set(), 'out': set(), 'rules': list()},
                           '$': {'in': set(), 'out': set(), 'rules': list()}}
        for state, grammarRules in self.grammar.rules.items():
            for grammarRule in grammarRules:
                out = grammarRule.variable if grammarRule.variable != '' else '$'
                if state not in self.statesList.keys():
                    self.statesList[state] = {'in': set(), 'out': set(), 'rules': list()}
                if out not in self.statesList.keys():
                    self.statesList[out] = {'in': set(), 'out': set(), 'rules': list()}
                nfaRule = self.NFARule(state, out, grammarRule.terminal)
                self.statesList[state]['rules'].append(nfaRule)
                self.statesList[state]['out'].add(out)
                self.statesList[out]['in'].add(state)

    def __str__(self):
        s = ''
        for state, prop in self.statesList.items():
            s += state + '-->' + ' | '.join(
                map(lambda rule: rule.rule + (rule.endState if rule.endState != '$' else ''), prop['rules']))
            s += '\n\tIn:' + str(prop['in']) + '\tOut' + str(prop['out']) + '\n'
        return s

    def hasLoop(self, state: str):
        for rule in self.statesList[state]['rules']:
            if rule.isLoop:
                return True
        return False

    def findRule(self, startState: str, endState: str):
        rules = list()
        for rule in self.statesList[startState]['rules']:
            if rule.endState == endState:
                rules.append(rule)
        return rules

    def TransitionNumber(self, state: str):
        transitions = set()
        for d in self.statesList.values():
            if state in d['out']:
                for rule in d['rules']:
                    if rule.endState == state:
                        transitions.add(rule)
            if state in d['in']:
                for rule in d['rules']:
                    if rule.startState == state:
                        transitions.add(rule)
        num = len(transitions)
        return num

    def findMinTransition(self):
        d = {}
        for state in self.statesList.keys():
            d[state] = self.TransitionNumber(state)
        min_state = None
        min_num = 0
        for state, num in d.items():
            if state == 'S' or state == '$':
                continue
            if min_state is None:
                min_state = state
                min_num = num
            elif num < min_num:
                min_state = state
                min_num = num
        return min_state

    def findLoopRegex(self, state):
        hasLoop = self.hasLoop(state)
        loop_regex = ''
        if hasLoop:
            loops = list()
            for r in self.statesList[state]['rules']:
                if r.isLoop:
                    loops.append(r)
            if len(loops) > 1:
                loop_regex = '(' + '+'.join(map(lambda rule: rule.rule, loops)) + ')*'
            else:
                loops = loops[0]
                if len(loops.rule) > 1:
                    loop_regex = '(' + loops.rule + ')*'
                else:
                    loop_regex = loops.rule + '*'
        return loop_regex

    def findRegex(self):
        while True:
            if len(self.statesList.keys()) == 2:
                break
            state = self.findMinTransition()
            inStates = self.statesList[state]['in']
            inStates.discard(state)
            outStates = self.statesList[state]['out']
            outStates.discard(state)

            addedRules = set()
            removedRules = set()

            for i in inStates:
                for o in outStates:
                    i2state = self.findRule(i, state)
                    for r in i2state:
                        removedRules.add(r)
                    if len(i2state) > 1:
                        i2state = '(' + '+'.join(map(lambda r: r.rule, i2state)) + ')'
                    else:
                        i2state = i2state[0].rule

                    state2o = self.findRule(state, o)
                    for r in state2o:
                        removedRules.add(r)
                    if len(state2o) > 1:
                        state2o = '(' + '+'.join(map(lambda r: r.rule, state2o)) + ')'
                    else:
                        state2o = state2o[0].rule

                    newRule = self.NFARule(i, o, i2state + self.findLoopRegex(state) + state2o)
                    addedRules.add(newRule)

            for r in addedRules:
                self.statesList[r.startState]['rules'].append(r)

            for r in removedRules:
                try:
                    self.statesList[r.startState]['rules'].remove(r)
                except:
                    pass

            for i in self.statesList[state]['in']:
                self.statesList[i]['out'].discard(state)

            for o in self.statesList[state]['out']:
                self.statesList[o]['in'].discard(state)

            for i in inStates:
                for o in outStates:
                    self.statesList[i]['out'].add(o)
                    self.statesList[o]['in'].add(i)

            del self.statesList[state]

        S2F = self.findRule('S', '$')
        regex = ''
        if len(S2F) > 1:
            regex = '(' + '+'.join(map(lambda r: r.rule, S2F)) + ')'
        else:
            regex = S2F[0].rule
        regex = self.findLoopRegex('S') + regex
        if regex[-1] == '@':
            regex = regex[:-1]

        for i in range(1, len(regex)-1):
            if regex[i] == '@' and regex[i-1] in self.grammar.alphabet and regex[i-1] in self.grammar.alphabet:
                regex = regex[:i] + '~' + regex[i+1:]
        regex.replace('~', '')
        return regex

if __name__ == '__main__':
    alphabet = input('Alphabet:\n').split()

    print('Grammar:')
    grammarList = list()
    while True:
        s = input()
        if s == '0':
            break
        grammarList.append(s)

    grammar = Grammar(alphabet, grammarList)

    grammar.simplify()

    nfa = NFA(grammar)
    print(nfa.findRegex())
