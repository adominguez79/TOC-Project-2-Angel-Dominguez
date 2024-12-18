import csv
from collections import defaultdict, deque

DEPTH_MAX = 500

#Class that helps NTM travel through and modify the tape
class Tape:
    def __init__(self,blank, string = '', head = 0):
        self.blank = blank
        self.loadString(string, head)

    #converts string input into list
    def loadString(self, string, head):
        self.symbols = list(string)
        self.head = head
    
    #returns symbol at head
    def readSymbol(self):
        if self.head < len(self.symbols):
            return self.symbols[self.head]
        else:
            return self.blank
        
    #writes into head 
    def writeSymbol(self, newSymbol):
        if newSymbol == '':
            newSymbol = self.symbols[self.head] #if no new symbol, use old one
        if self.head < len(self.symbols):
            self.symbols[self.head] = newSymbol 
        else:
            self.symbols.append(newSymbol)

    #moves head
    def moveHead(self, movement):
        if movement == 'L':
            self.head -= 1
        elif movement == 'R':
            self.head += 1
        else:
            pass
    
    #dereferences tape for new branches
    def clone(self):
        return Tape(self.blank, self.symbols, self.head)

    def output(self):
        return ''.join(self.symbols[:self.head]),''.join(self.symbols[self.head:])

class NTM:

    #Initializes NTM components
    def __init__(self,name,start,final, blank = '_'):
        self.name = name
        self.start = self.state = start
        self.final = final
        self.blank = blank
        self.tape = Tape(blank)
        self.trans = defaultdict(list)
    
    #Loads string into NTM
    def restart(self, string):
        self.state = self.start
        self.tape.loadString(string,0)

    #Adds transition to NTM
    def addTrans(self, state, read_sym, new_state, moves):
        # accounts if no new state is provided
        if new_state == '':
            new_state = state
        self.trans[(state, read_sym)].append((new_state, moves))

    #Retruns transitions to determine nondeterminism 
    def getTrans(self):
        key = (self.state, self.tape.readSymbol())
        return self.trans[key] if key in self.trans else None
    
    #Executes transitions
    def execTrans(self,trans):
        self.state, direction = trans
        self.tape.writeSymbol(direction[0])
        self.tape.moveHead(direction[1])
        return self
    
    #Duplicates NTM for nondeterministic branching
    def clone(self):
        tm = NTM(self.name, self.start, self.final)
        tm.state = self.state
        tm.tape = self.tape.clone()
        tm.trans = self.trans 
        return tm


    def accepts(self, string):
        depth = 0
        configurationCount = 0
        parentMap = {}
        self.restart(string)
        queue = deque([(self,None,0)])

        while len(queue) > 0:
            if depth >= DEPTH_MAX:
                print("Execution Stoped: Depth limit reached")
                return self.name, "Ran too long", depth, configurationCount
            tm, parent, curDepth = queue.popleft()
            transitions =    tm.getTrans()
            depth = max(depth, curDepth) #gets highest depth
      #      print([x.to_list() for x, _, _ in queue], curDepth)
            try: configurationCount += len(transitions) #transitions create a configuration
            except(TypeError):
                pass

            if transitions is None:
                # Break if queue empty, accept if state is qaccept
                if tm.state in tm.final: # trace path
                    path = []
                    while tm:
                        path.append(tm.to_list())
                        tm = parentMap.get(tm)
                    return self.name, path[::-1], depth, configurationCount
           
            else:
                # Add copy of NTM if not deterministic
                for trans in transitions[1:]:
                    clonedTM = tm.clone().execTrans(trans)
                    queue.append((clonedTM,tm,curDepth+1))
                    parentMap[clonedTM] = tm
                # execute and add the deterministic transition
                determTM = tm.clone().execTrans(transitions[0])
                queue.append((determTM,tm,curDepth+1))
                parentMap[determTM] = tm
        return self.name, 'Rejected', depth, configurationCount
    
    def to_list(self):
        tempTape = self.tape.clone()
        left, right = tempTape.output()
        return [left,self.state,right]

    
#Parse CSV file into NTM
def parseNTM(file) -> NTM:

    with open(file, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=' ', quotechar='|')

        name = ' '.join(next(csvreader))
        states = next(csvreader)[0]
        sigma = next(csvreader)[0].split(',')
        tapeLang = next(csvreader)[0].split(',')
        innitState = next(csvreader)[0].split(',')[0]
        finalStates = next(csvreader)[0].split(',')
        rejectState = None

        ntm = NTM(name,innitState,finalStates,tapeLang[-1])
        
        #add transitions
        for line in csvreader:
            if ['qreject'] == line:
                rejectState = 'qreject'
                continue
            trans = line[0].split(',')
            ntm.addTrans(trans[0],trans[1],trans[2],(trans[3],trans[4]))

        return ntm
    
if __name__ == '__main__':
    machineFile = input("Please enter machine file name: ")
    N1_ntm = parseNTM(machineFile)
    inputFile = input("Please enter name of input file: ")
    with open(inputFile, 'r') as inputs:
        for input in inputs:
            input = input.rstrip()
            result = None
            name,path,depth,configCount = N1_ntm.accepts(input)
            if type(path) == list:
                result = 'Success'
                print(f'Machine Name: {name}\n"{input}" accepted in {depth} steps.\nLevel of nondeterminism:= {configCount/depth}\nPath:\n{path}\n')
            else:
                result = path
                print(f'Machine Name:{name}\n"{input}" rejected after {depth} steps.\n')
            with open('output.csv', 'a',newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow([name,input,result,depth,configCount,configCount/depth])





