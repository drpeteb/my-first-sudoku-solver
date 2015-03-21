import sys
from PyQt4 import QtCore, QtGui
from numpy import *
from copy import copy, deepcopy


# Main window class - has the state, solver and interface as children
class SdkuWindow(QtGui.QMainWindow):
    def __init__(self):
        super(SdkuWindow, self).__init__()

        # Prettiness
        self.setWindowTitle('Pete\'s Sudoku Solver')
        self.resize(250, 250)

        # Create an array to store numbers in grid
        self.state = SdkuState()

        # Create a backend solver object
        self.solver = SdkuBackend()

        # Create a GUI interface object
        self.interface = SdkuInterface()
        self.setCentralWidget(self.interface)

        # Link children
        self.solver.link(self.state)
        self.interface.link(self.state)
        self.state.link(self.solver, self.interface)



# State class - stores the current knowns and tracks which numbers are from ui
class SdkuState():
    def __init__(self):
        self.numbers = zeros((9,9), dtype=int8)
        self.ui = zeros((9,9), dtype=int8)

    def link(self, solver, interface):
        self.solver = solver
        self.interface = interface

    def getNum(self, i, j):
        return self.numbers[i][j]

    def getUi(self, i, j):
        if self.ui[i][j]>0:
            return True
        else:
            return False

    def uiInput(self, i, j, val):
        # Update the state
        if isinstance(val, int)&(val in range(10)):
            self.ui[i][j] = val

        # Call the solver logical-complete
        valid,output = self.solver.inputNumbers(self.ui)
        print(valid)

        # Update if the solver returns invalid, update otherwise
        if valid:
            self.numbers = copy(output)
        else:
            self.ui[i][j] = 0

        # Call the interface update
        self.interface.setNumbers()

    def reset(self):
        # Clear the state
        self.numbers = zeros((9,9), dtype=int8)
        self.ui = zeros((9,9), dtype=int8)

        # Call reset on the solver
        self.solver.reset()

        # Call the interface update
        self.interface.setNumbers()

    def forceSolve(self):
        # Call the solver backtracker
        valid,output = self.solver.forceSolve()

        # Revert if the solver returns invalid, update otherwise
        if valid:
            self.numbers = copy(output)
            self.interface.setNumbers()
        else:
            # Output a rude message
            pass            



# Interface class - handles display and input
class SdkuInterface(QtGui.QWidget):
    def __init__(self):
        super(SdkuInterface, self).__init__()

        # List acceptable user input
        self.validEntries = ['1', '2', '3', '4', '5', '6', '7', '8', '9']

        # Clear button
        self.clearBut = QtGui.QPushButton("Clear")
        self.connect(self.clearBut, QtCore.SIGNAL("clicked()"), self.pressClearBut)

        # Solve button - force backtrack solve if logical solve has failed
        self.solveBut = QtGui.QPushButton("Solve")
        self.connect(self.solveBut, QtCore.SIGNAL("clicked()"), self.pressSolveBut)

        # Top level grid - this will hold the text boxes and the dividing lines
        self.bigGrid = QtGui.QGridLayout()
        self.bigGrid.setSpacing(10)

        # Create an array to hold the ui boxes
        self.boxes = range(9)
        for i in range(9):
            self.boxes[i] = range(9)

        # Build the interface
        ii = 0
        for i in range(11):
            jj = 0

            for j in range(11):
                if (i==3)|(i==7):
                    line = QtGui.QFrame()
                    line.setFrameShape(QtGui.QFrame.HLine)
                    self.bigGrid.addWidget(line, i, j)
                elif (j==3)|(j==7):
                    line = QtGui.QFrame()
                    line.setFrameShape(QtGui.QFrame.VLine)
                    self.bigGrid.addWidget(line, i, j)
                else:
                    self.boxes[ii][jj] = QtGui.QLineEdit(self)
                    self.boxes[ii][jj].pos = (ii, jj)
                    self.boxes[ii][jj].setMaxLength(1)
                    self.boxes[ii][jj].setAlignment(QtCore.Qt.AlignHCenter)
                    self.connect(self.boxes[ii][jj], QtCore.SIGNAL("textEdited(const QString&)"), self.enterText)
                    self.bigGrid.addWidget(self.boxes[ii][jj], i, j)

                if not((j==3)|(j==7)):
                    jj += 1

            if (i!=3)&(i!=7):
                ii += 1

        # Stick everything in some layout boxes
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(self.clearBut)
        self.hbox.addWidget(self.solveBut)

        self.vbox = QtGui.QVBoxLayout()
        self.vbox.addLayout(self.bigGrid)
        self.vbox.addLayout(self.hbox)
        
        self.setLayout(self.vbox)

    def link(self, state):
        self.state = state

    def enterText(self):

        print('Text Entered. Attempting logical solve')

        # Work out who's been changed
        sentby = self.sender()
        text = sentby.text()
        pos = sentby.pos
        i = pos[0]
        j = pos[1]

        print(pos)

        # Send the location and new value to the state
        if text in self.validEntries:
            self.state.uiInput(i, j, int(text))
        elif text=='':
            self.state.uiInput(i, j, 0)
        else:
            sentby.setText('')     

    def pressSolveBut(self):
        print('Attempting backtrack solve')
        self.state.forceSolve()

    def pressClearBut(self):
        print('Clearing')
        self.state.reset()

    def setNumbers(self):
        print('Update display')

        # Loop through numbers
        for i in range(9):
            for j in range(9):

                # Fetch the value
                val = self.state.getNum(i, j)

                # Update the text box
                if val>0:
                    self.boxes[i][j].setText(str(val))
                else:
                    self.boxes[i][j].setText('')

                # Make it bold if its a ui box
                if self.state.getUi(i, j)==True:
                    font = self.boxes[i][j].font().setBold(True)
                else:
                    font = self.boxes[i][j].font().setBold(False)



# Solver class - runs logical and force solve routines
class SdkuBackend():
    def __init__(self):
        # Create all the variables and constraints
        self.vars = range(9)
        self.rows = range(9)
        self.cols = range(9)
        self.squs = range(9)
        self.cons = range(27)
    
        #Create Variable nodes
        for i in range(9):
            self.vars[i] = range(9)
            for j in range(9):
                self.vars[i][j] = Variable(i, j)
    
        #Create Row Constraint nodes and link
        for i in range(9):
            self.rows[i] = Constraint(i)
            self.cons[i] = self.rows[i]
            for j in range(9):
                self.rows[i].links.append(self.vars[i][j])
                self.vars[i][j].links.append(self.rows[i])

        #Create Column Constraint nodes and link
        for j in range(9):
            self.cols[j] = Constraint(j)
            self.cons[j+9] = self.cols[j]
            for i in range(9):
                self.cols[j].links.append(self.vars[i][j])
                self.vars[i][j].links.append(self.cols[j])

        #Create Square Constraint nodes and link
        for k1 in range(9):
            self.squs[k1] = Constraint(k1)
            self.cons[k1+18] = self.squs[k1]
            x = 3*(k1/3)
            y = 3*(k1-x)
            for j in range(3):
                for i in range(3):
                    self.squs[k1].links.append(self.vars[y+i][x+j])
                    self.vars[y+i][x+j].links.append(self.squs[k1])

    def link(self, state):
        self.state = state

    def inputNumbers(self, numbers):

        # print(numbers)

        # Reset solver
        self.reset()

        # Set knowns
        for i in range(9):
            for j in range(9):
                if numbers[i][j]>0:
                    self.vars[i][j].setKnown(numbers[i][j])

        # Logical solve
        valid = self.logicalSolve_()

        #for i in range(9):
        #    for j in range(9):
        #        print (str(i) + ' ' + str(j) + ' ' + str(self.vars[i][j].pmf))

        # Generate output
        output = zeros([9,9],dtype=int8)
        for i in range(9):
            for j in range(9):
                output[i][j] = self.vars[i][j].getKnown()
        return valid, output

    def reset(self):
        print('Reset solver')
        # Reset all possibilities
        for i in range(9):
            for j in range(9):
                self.vars[i][j].reset()

    def forceSolve(self):
        # Crack this egg with a backtrack
        valid = self.branch_(0)
        
        # Generate output
        output = zeros([9,9],dtype=int8)
        for i in range(9):
            for j in range(9):
                output[i][j] = self.vars[i][j].getKnown()

        return valid, output

    def branch_(self, level):
        # Backup pmfs for when we hit a dead end
        backup = range(9)
        for ii in range(9):
            backup[ii] = range(9)
            for jj in range(9):
                backup[ii][jj] = copy(self.vars[ii][jj].pmf)
                print(backup[ii][jj])

        #backup = range(9)
        #for i in range(9):
        #    backup[i] = range(9)
        #    for j in range(9):
        #        backup[i][j] = self.vars[i][j].__copy__()
                
        #backup = deepcopy(self.vars)

        level = level + 1
        space =  ""
        for i in range(level):
            space = space+"    "

        # Select branch point
        done = False
        for i in range(9):
            for j in range(9):
                if self.vars[i][j].pmf.count(1)>1:
                    branch_loc = (i+1, j+1)
                    done = True
                    break
            if done==True:
                break
        
        if done==False:
            # No possible branch points
            print(space+"No possible branch points")
            return False
        
        # Make a list of possible values
        poss_vals = []
        for t in range(9):
            if self.vars[i][j].pmf[t]==1:
                poss_vals.append(t)

        print(space+"Branch initiated at "+str(branch_loc)+" with index possibilities "+str([p+1 for p in poss_vals]))

        # Loop through possible values
        for t in poss_vals:
            
            print(space+"Trying value: "+str(t+1))

            # Recall the pre-branch state
            #print(backup)
            for ii in range(9):
                for jj in range(9):
                    self.vars[ii][jj].pmf = copy(backup[ii][jj])
            #self.vars = backup
            #for i in range(9):
            #    backup[i] = self.vars[i].copy()
            #self.vars = deepcopy(backup)
                
            # Set this possible value to be the only possible value
            self.vars[i][j].pmf=[0, 0, 0, 0, 0, 0, 0, 0, 0]
            self.vars[i][j].pmf[t]=1

            # Solve logically
            valid = self.logicalSolve_()
            num_solved, num_poss = self.countKnownStates_()
            if valid:
                print(space+"Valid solution with "+str(num_solved)+" boxes solved")
            else:
                print(space+"Invalid solution")

            # If solution is completely and validly solved, return
            if (valid==True)&(num_solved==81):
                print(space+"Solution complete and valid")
                break
            # If valid but not complete, recurse
            elif (valid==True):
                valid = self.branch_(level)
                if valid==True:
                    break
            # If not valid, try next possible value
            else:
                pass
        
        if valid==False:
            print(space+"No valid solution. Returning to pre-branch values")
            #print(backup)
            for ii in range(9):
                for jj in range(9):
                    self.vars[ii][jj].pmf = copy(backup[ii][jj])
            #self.vars = deepcopy(backup)

        return valid

    def logicalSolve_(self):
        # Solve the puzzle as far as possible using logical steps only

        # Main solving loop
        it = 0
        prev_num_poss = 0   # Convergence test
        while it < 100:

            # Apply logical solve steps
            self.eliminateInvalids_()
            self.isolateUniques_()

            it = it + 1

            # Count the number of possible states
            num_solved, num_poss = self.countKnownStates_()
            print("Solved "+str(num_solved)+" boxes after "+str(it)+" iterations.")

            # Test for convergence
            if num_poss==prev_num_poss:
                print("Converged after "+str(it)+" iterations. End loop.")
                print(str(num_poss)+" possibilities remain.")
                break

            prev_num_poss = num_poss

        # Check that solution is valid
        valid = self.checkConstraints_()

        return valid

    def eliminateInvalids_(self):
        # Loops over an array of variables and eliminates invalid possiblities

        # Loop over rows
        for i in range(9):
            # Loop over columns
            for j in range(9):
                curr_var = self.vars[i][j]
                val = curr_var.getKnown()
                if val>0:
                    # Loop through constraints
                    for k in range(3):
                        # Eliminate this possibility from remaining variables
                        curr_var.links[k].eliminate(i,j,val)

        return

    def isolateUniques_(self):
        # Loops over a list of constraints and sets values for unique value occurences

        # Loop over constraints
        for i in range(27):
            # Loop over possible values
            for t in range(9):
                # Test for single location presence
                counts = 0
                idx = -1
                for j in range(9):
                    if self.cons[i].links[j].pmf[t]==1:
                        counts = counts + 1
                        idx = j
                if counts==1:
                    #print('Found a unique at: '+str(self.cons[i].links[idx].pos))
                    self.cons[i].links[idx].pmf = [0, 0, 0, 0, 0, 0, 0, 0, 0]
                    self.cons[i].links[idx].pmf[t] = 1
        return

    def countKnownStates_(self):
        # Count the number of possible values for unsolved variables
        solved = 0
        possibles = 0
        for i in range(9):
            for j in range(9):
                if sum(self.vars[i][j].pmf)==1:
                    solved = solved + 1
                else:
                    possibles = possibles + sum(self.vars[i][j].pmf)
        return solved, possibles
        
    def checkConstraints_(self):

       # Check non-zero variable probabilities
        for i in range(9):
            for j in range(9):
                valid = self.vars[i][j].check()
                if valid==False:
                    return False

        # Check for constraint violations
        for i in range(27):
            valid = self.cons[i].check()
            if valid==False:
                return False
            
        return True



class Variable:
    """Variable node class"""
    def __init__(self, i, j):
        self.pos = (i, j)
        self.pmf = [1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.links = []

    def __copy__(self):
        new = Variable(0,0)
        new.pos = self.pos
        new.pmf = self.pmf
        new.links = self.links
        for i in range(3):
            for j in range(9):
                if new.links[i].links[j].pos == new.pos:
                    new.links[i].links[j] = new

        return new
        
    def reset(self):
        self.pmf = [1, 1, 1, 1, 1, 1, 1, 1, 1]

    def setKnown(self, c):
        self.pmf = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.pmf[c-1] = 1

    def getKnown(self):
        #s = time()
        pmf = self.pmf
        if pmf.count(1)==1:
            c = pmf.index(1)+1
        else:
            c = 0
        #d = time()-s
        #print(d)
        return c

    def check(self):
        # Check that there is at least one possibility for the variable
        if sum(self.pmf)==0:
            valid = False
        else:
            valid = True
        return valid



class Constraint:
    """Constraint node class"""
    def __init__(self, i):
        self.pos = i
        self.links = []

    def check(self):
        # Check that there are no repeated values in the contraint region
        valid = True
        found = zeros([1,9])
        poss = zeros([1,9])
        for j in range(9):
            for t in range(9):
                if self.links[j].pmf[t]==1:
                    poss[0][t] = 1
            val = self.links[j].getKnown()
            if val>0:
                if found[0][val-1]==1:
                    print("Repeated value")
                    valid = False
                    break
                else:
                    found[0][val-1]=1
        if (poss==0).any():
            print("No possible location")
            valid = False
        return valid

    def eliminate(self, ii, jj, c):
        # Eliminate the known value c from all linked variables except (i,j)
        for k in range(9):
            if not(self.links[k].pos==(ii,jj)):
                self.links[k].pmf[c-1] = 0
        return


app = QtGui.QApplication(sys.argv)
main = SdkuWindow()
main.show()
sys.exit(app.exec_())
