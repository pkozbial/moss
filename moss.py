#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Piotr Koźbiał
#
# This file is part of Moss.
# 
# Moss is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Moss is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Moss.  If not, see <http://www.gnu.org/licenses/>.

# external modules
import curses
import curses.wrapper
import curses.ascii
import email
import mailbox
import re
import os
import sys

# application modules
import emailextra
from expr import *
from expr_ui import *
from expr_special import *
from expr_eval import *

##### MAIN SCREEN LAYOUT ############################################

class MainLayout:
  """This class is the top UI layer. It:
     - splits the screen into 4 areas:
         - status line (top)
         - main display
         - status line (bottom)
         - command line
    - it implements the status lines and command line parts
    - the main display is plugged here, but implemented elsewhere
    - it reads and dispatches user input
      (handles the command line, but passes some characters
      to the main area)
    - it handles the WINCH signal (terminal resize) and also 
      dispatches it to the main display plugin"""

  def __init__(self, stdscr):
    self._stdscr = stdscr
    self._cmdline = ''
    self._topStatusText = ''
    self._bottomStatusText = ''
    self._tmpmessage = None
    self._tmpmessagemode = None
    self._inputMode = False
    (self._screenMaxY, self._screenMaxX) = self._stdscr.getmaxyx()      

  def setMainPanel(self, mainpanel):
    self._mainpanel = mainpanel

  def setCmdListener(self, cmdlistener):
    self._cmdlistener = cmdlistener

  def setBottomStatusText(self, text):
    self._bottomStatusText = text

  def setTopStatusText(self, text):
    self._topStatusText = text

  def save(self):
    curses.savetty()

  def restore(self):
    curses.resetty()
    self._stdscr.redrawwin()

  def quickUpdateBottomStatusText(self, text):
    self._bottomStatusText = text
    statusTxt = self._bottomStatusText
    statusAttr = curses.A_REVERSE
 
    self._stdscr.addstr(
      self._screenMaxY-2, 0,
      statusTxt+" "*(self._screenMaxX-len(statusTxt)-1), statusAttr)

    self._stdscr.nooutrefresh()
    curses.doupdate()

  def run(self):
    self._cmdlistener.startup()

    self._paint()
    curses.doupdate()
    while (True):
      curses.halfdelay(2)
      ch = self._stdscr.getch()
      if ch == curses.KEY_RESIZE:
        (self._screenMaxY, self._screenMaxX) = self._stdscr.getmaxyx()
        self._mainpanel.feedResize()
      elif ch in [8, 127, curses.KEY_BACKSPACE]: # backspace
        self._tmpmessage = None
        self._cmdline = self._cmdline[0:len(self._cmdline)-1]
      elif ch == 27: # escape
        self._tmpmessage = None
        self._cmdline = ''
      elif ch == 10: # return
        saveSel = self._mainpanel.getSelected()
        saveTop = self._mainpanel.getTop()
        self._tmpmessage = None
        if self._inputMode:
          self._inputMode = False
          ret = self._cmdlistener.feedInput(self._cmdline)
        else:
          ret = self._cmdlistener.feedCmd(self._cmdline)
        if ret.quit == True:
          break
        if ret.clear == True:
          self._cmdline = ''
        if ret.input == True:
          self._inputMode = True
        self._tmpmessage = ret.msg
        self._tmpmessagemode = ret.msgType
        if ret.change == 'mod':
          self._mainpanel.adjustObj(ret.obj, ret.row, ret.sel)
        elif ret.change == 'rm':
          self._mainpanel.adjustTop(saveTop, saveSel)
        else:
          pass
      elif ch in [ord('j'), ord('k'), ord('J'), ord('K')] and \
           (len(self._cmdline) == 0 and not self._inputMode):
        self._tmpmessage = None
        self._mainpanel.feedChar(ch)
      elif curses.ascii.isprint(ch):
        if not self._inputMode:
          self._tmpmessage = None
        self._cmdline += chr(ch)

      self._paint()
      curses.doupdate()

  def _paint(self):
    self._stdscr.addstr(
      0, 0,
      self._topStatusText+
           " "*(self._screenMaxX-len(self._topStatusText)-1),
           curses.A_REVERSE)
 
    if self._tmpmessage == None:
      statusTxt = self._bottomStatusText
      statusAttr = curses.A_REVERSE
    else:
      statusTxt = self._tmpmessage
      if self._tmpmessagemode == 'info':
        statusAttr = curses.A_REVERSE+curses.A_BOLD
      elif self._tmpmessagemode == 'error':
        statusAttr = curses.A_BOLD
      else: # should not happen
        statusAttr = curses.A_REVERSE+curses.A_BOLD
 
    self._stdscr.addstr(
      self._screenMaxY-2, 0,
      statusTxt+" "*(self._screenMaxX-len(statusTxt)-1), statusAttr)

    l = min(len(self._cmdline), self._screenMaxX-1)
    self._stdscr.addstr(
      self._screenMaxY-1, 0, self._cmdline[0:l]+" "*(self._screenMaxX-l-1))
    self._stdscr.noutrefresh()

    self._mainpanel.paint()

    self._stdscr.move(self._screenMaxY-1, min(l, self._screenMaxX))

class FeedCmdResult:
  """Return value for feedCmd. Members:
     quit   : boolean (False)         - quit application?
     clear  : boolean (True)          - clear cmd line?
     input  : boolean (False)         - enter input mode?
     msg    : string/None (None)      - message
     msgType: 'info'/'error' ('info') - message type
     change : 'mod'/'rm'/None (None)  - type of change to the tree
     sel    : expression node (None)  - select this node (None=keep selected row)
     The following are used when change == 'mod':
     obj    : expression node (None)  - try to keep this in...
     row    : int (None)              - this line
  """
  def __init__(self):
    self.quit    = False
    self.clear   = True
    self.input   = False
    self.msg     = None
    self.msgType = 'info'
    self.change  = None
    self.sel     = None
    self.obj     = None
    self.row     = None
  @staticmethod
  def error(msg):
    r = FeedCmdResult()
    r.msgType = 'error'
    r.msg = msg
    return r
  @staticmethod
  def info(msg):
    r = FeedCmdResult()
    r.msg = msg
    return r
  @staticmethod
  def input(msg):
    r = FeedCmdResult()
    r.msg = msg
    r.input = True
    return r
  @staticmethod
  def mod(obj, row, selectObj):
    r = FeedCmdResult()
    r.change = 'mod'
    r.obj = obj
    r.row = row
    r.sel = selectObj
    return r
  @staticmethod
  def rm():
    r = FeedCmdResult()
    r.change = 'rm'
    return r

class MainPanel:

  # for MAIN -----------------------------

  def __init__(self, stdscr):
    self._stdscr = stdscr
    (self._screenMaxY, self._screenMaxX) = self._stdscr.getmaxyx()      
    
    self._topline = 0
    self._selected = 0
    self._lines = []
    self._userParams = []

  def start(self):
    self._paint()

  # for MainLayout -----------------------

  def feedChar(self, ch):
    if ch == ord('j'):
      if self._selected < len(self._lines)-1:
        self._selected += 1
        if self._selected - self._topline +1 > self._screenMaxY-3:
          self._topline += 1
        
    elif ch == ord('k'):
      if self._selected > 0:
        self._selected -= 1
        if self._selected < self._topline:
          self._topline -= 1 

    if ch == ord('J'):
      if len(self._lines) - self._topline >= self._screenMaxY-2:
        self._topline += 1
      if self._selected < self._topline:
        self._selected += 1
        
    elif ch == ord('K'):
      if self._topline > 0:
        self._topline -= 1 
      if self._selected - self._topline +1 > self._screenMaxY-3:
        self._selected -= 1

  def feedResize(self):
    (self._screenMaxY, self._screenMaxX) = self._stdscr.getmaxyx()      

  def paint(self):
    count = len(self._lines)
    for i in range(1, self._screenMaxY-2):
      idx = self._topline+i-1
      if idx < count:
        attr = curses.A_NORMAL
        if idx == self._selected:
          attr = curses.A_REVERSE
        self._stdscr.addstr(i, 0, self._lines[self._topline+i-1], attr)
      else:
        self._stdscr.move(i, 0)
      self._stdscr.clrtoeol()
     
  def getTop(self):
    return self._topline

  def adjustObj(self, obj, row, sel):
    objLine = self.getLineByUserParam(obj)
    selLine = self.getLineByUserParam(sel)
    self.adjustTop(objLine-row, selLine)

  def adjustTop(self, top, sel):
    self._topline = top
    self._selected = sel
    if self._selected >= len(self._lines):
      self._selected = len(self._lines)-1
    if self._selected < self._topline:
      self._topline = self._selected
    elif self._selected - self._topline + 1 > self._screenMaxY - 3:
      self._topline = self._selected - self._screenMaxY + 4

  # for Engine ---------------------------

  def addLine(self, text, userParam):
    self._lines.append(text)
    self._userParams.append(userParam)

  def insertLineAfter(self, prevNum, text, userParam):
    self._lines.insert(prevNum+1, text)
    self._userParams.insert(prevNum+1, userParam)
    if self._selected > prevNum:
      self._selected += 1
      if self._selected - self._topline +1 > self._screenMaxY-3:
        self._topline += 1

  def insertLineBefore(self, nextNum, text, userParam):
    self.insertLineAfter(nextNum-1, text, userParam)

  def removeLine(self, lineNum):
    del self._lines[lineNum]
    del self._userParams[lineNum]
    if self._selected == len(self._lines):
      self._selected -= 1
      if self._selected < self._topline:
        if self._topline > 0:
          self._topline -= 1

  def select(self, lineNum):
    self._selected = lineNum
    if self._selected < self._topline:
      self._topline = self._selected
    elif self._selected - self._topline + 1 > self._screenMaxY - 3:
      self._topline = self._selected - self._screenMaxY + 4

  def selectByUserParam(self, userParam):
    self.select(self.getLineByUserParam(userParam))

  def getSelected(self):
    return self._selected

  def getLineUserParam(self, lineNum):
    return self._userParams[lineNum]

  def getLineByUserParam(self, userParam):
    for i in range(len(self._userParams)):
      if self._userParams[i] is userParam:
        return i
    return None

  def clear(self):
    self._lines = []
    self._userParams = []
    self._selected = 0
    self._topline = 0

class Engine:
  def setMainLayout(self, mainLayout):
    self._mainLayout = mainLayout

  def setMainPanel(self, mainPanel):
    self._mainPanel = mainPanel

  def setStatusInterface(self, statusInterface):
    self._statusInterface = statusInterface

  def setMailbox(self, mboxName):
    self._mboxName = mboxName

  def startup(self):
    self._statusInterface.setTopStatusText('MailMan version 0.1')
    if os.path.isdir(self._mboxName):
      self._mailbox = mailbox.Maildir(self._mboxName, None)
    else:
      self._mailbox = mailbox.mbox(self._mboxName)
    self._query = ExprNull(ET.Bool, dict(), dict())
    for (indent, text, obj) in self._query.uiGetRendering():
      self._mainPanel.addLine('  '*indent+text, obj)
    def allSubclasses(cls):
      s = set()
      s.add(cls)
      for subcls in cls.__subclasses__():
        s |= allSubclasses(subcls)
      return s
    self._exprCommands = dict()
    for cls in allSubclasses(Expr):
      try:
        cmd = cls.uiGetCmdName()
        self._exprCommands[cmd] = cls
      except:
        pass
    ##### query status:
    # the list of all messages resulted in last search
    self._results = None
    # boolean: True if the query didn't change since _results were obtained
    self._resultsFresh = None
    #####
    self.updateStatus()

  def defaultValue(self, ptype):
    if ptype == ET.Int: return 0
    if ptype == ET.String: return ''
    if ptype == ET.Size: return None
    if ptype == ET.Bool: return True
    if ptype == ET.Var: return '_'
    if ptype == ET.Type: return ET.String
    raise BaseException("Internal error")

  def valueFromString(self, ptype, arg):
    if ptype == ET.Int: return int(arg)
    if ptype == ET.String: return arg
    if ptype == ET.Size: raise BaseException("To be implemented")
    if ptype == ET.Bool:
      if arg == 'true':
        return True
      elif arg == 'false':
        return False
      else:
        raise BaseException("Invalid boolean constant")
    if ptype == ET.Var: return arg
    if ptype == ET.Type:
       return ET.fromStr(arg)

  def standardCreateHelper(self, cmd, arg, etype):
    exprClass = self._exprCommands[cmd]
    genType = exprClass.getPossibleTypes()
    if not etype in genType:
      return None # FeedCmdResult.error('ERROR: Wrong type')
    constParTypes = exprClass.getConstParamTypes(etype)
    constParams = dict()
    if len(constParTypes) == 0:
      pass
    elif len(constParTypes) == 1:
      pname = constParTypes.keys()[0]
      ptype = constParTypes[pname]
      if arg == None:
        # take default
        pvalue = self.defaultValue(ptype)
      else:
        pvalue = self.valueFromString(ptype, arg)
        if pvalue == None:
          return FeedCmdResult.error('incorrect value >'+arg+'< for type '+ET.toStr(ptype))
      constParams[pname] = pvalue
    else:
      raise BaseException("NOT IMPLEMENTED: multiple constant parameters")
    return exprClass(etype, constParams, dict())

  def standardCreateCommand(self, cmd, arg, current, currentLine):
    expr = self.standardCreateHelper(cmd, arg, current.getType())
    if expr == None:
      return FeedCmdResult.error('ERROR: Wrong type')
    if current is self._query:
      self._query = expr
    else:
      current.replace(expr)
    return FeedCmdResult.mod(expr, currentLine, expr.uiPosHintCreate())

  def addAndOrSiblingCommand(self, cmd, arg, current, currentLine):
    sibling = ExprNull(ET.Bool, dict(), dict())
    current.getParent().addChild(sibling)
    return FeedCmdResult.mod(current, currentLine, sibling.uiPosHintCreate())

  def pushDownWithAndOrCommand(self, cmd, arg, current, currentLine):
    if cmd == 'and':
      expr = ExprAnd(ET.Bool, dict(), dict())
    elif cmd == 'or':
      expr = ExprOr(ET.Bool, dict(), dict())
    if current is self._query:
      self._query = expr
    else:
      current.replace(expr)
    expr.replaceChildren([current, ExprNull(ET.Bool, dict(), dict())])
    return FeedCmdResult.mod(expr, currentLine, expr.uiPosHintCreate())
 
  def pushDownWithQuantifier(self, cmd, arg, current, currentLine):
    expr = self.standardCreateHelper(cmd, arg, ET.Bool)
    if current is self._query:
      self._query = expr
    else:
      current.replace(expr)
    expr.replaceExpr(current)
    return FeedCmdResult.mod(expr, currentLine, expr.uiPosHintCreate())

  def pushFarDownWithQuantifier(self, cmd, arg, current, currentLine):
    parent = current.getParent()
    parentLine = self._mainPanel.getLineByUserParam(parent)
    if current.getType() == ET.String:
      arg1 = None
    elif current.getType() == ET.Int:
      arg1 = 'int'
    elif current.getType() == ET.Size:
      arg1 == 'size'
    expr = self.standardCreateHelper(cmd, arg1, ET.Bool)
    if parent is self._query:
      self._query = expr
    else:
      parent.replace(expr)
    expr.replaceExpr(parent)
    expr.replaceValues([current])
    parent.replaceChild(current, ExprVar(current.getType(), dict(), dict()))
    return FeedCmdResult.mod(expr, parentLine, expr.uiPosHintCreate())

  def modCommand(self, current, currentLine):
    paramTypes = current.getParamTypesConcrete()
    if len(paramTypes) == 0:
      return FeedCmdResult.error('This expression takes no parameters')
    elif len(paramTypes) == 1:
      # enter input mode
      pname = paramTypes.keys()[0]
      ptype = paramTypes[pname]
      return FeedCmdResult.input('Enter parameter \''+pname+'\' ('+ET.toStr(ptype)+'):')
    else:
      return FeedCmdResult.error('NOT IMPLEMENTED: multiple parameters')

  def moreCommand(self, current, currentLine):
    currentLine = self._mainPanel.getSelected()
    current = self._mainPanel.getLineUserParam(currentLine)
    if isinstance(current.getParent(), ExprForAll) or\
       isinstance(current.getParent(), ExprExists):
      etype = current.getType()
      sibling = ExprNull(etype, dict(), dict())
      lineCount = len(current.getParent().uiGetRendering())
      parentLine = self._mainPanel.getLineByUserParam(current.getParent())
      for i in range(lineCount):
        self._mainPanel.removeLine(parentLine)
      current.getParent().addValue(sibling)
      basicIndent = current.getParent().uiGetBaseIndent()
      lnum = 0
      for (indent, text, obj) in current.getParent().uiGetRendering():
        self._mainPanel.insertLineAfter(parentLine-1+lnum,
                                        '  '*(basicIndent+indent)+text, obj)
        lnum += 1
      self._mainPanel.selectByUserParam(sibling.uiPosHintCreate())
      if self._resultsFresh == True: self._resultsFresh = False
      return FeedCmdResult()
    else:
      return FeedCmdResult.error('cannot add sibling here')
  
  def expandCommand(self, current, currentLine):
    expr = current.copyExpanded(current.getParent())
    if current is self._query:
      self._query = expr
    else:
      current.replace(expr)
    return FeedCmdResult.mod(expr, currentLine, expr.uiPosHintCreate())
      
  # this will be called by the UI when input mode had been initiated
  # and the user has just entered a text
  def feedInput(self, input):
    currentLine = self._mainPanel.getSelected()
    current = self._mainPanel.getLineUserParam(currentLine)

    lineCount = len(current.uiGetRendering())
    for i in range(lineCount):
      self._mainPanel.removeLine(currentLine)

    paramTypes = current.getParamTypesConcrete()
    #TODO - we assume here that len(paramTypes)==1  -- need to do other cases
    pname = paramTypes.keys()[0]
    ptype = paramTypes[pname]
    # TODO - need to check if valueFromString returns None
    current.setParam(pname, self.valueFromString(ptype, input))
    basicIndent = current.uiGetBaseIndent()
    lnum = 0
    for (indent, text, obj) in current.uiGetRendering():
      self._mainPanel.insertLineAfter(currentLine-1+lnum,
                                      '  '*(basicIndent+indent)+text, obj)
      lnum += 1
    #self._mainPanel.removeLine(currentLine)
    self._mainPanel.selectByUserParam(current.uiPosHintCreate())
    if self._resultsFresh == True: self._resultsFresh = False
    self.updateStatus()
    return FeedCmdResult()

  def defCommand(self):
    currentLine = self._mainPanel.getSelected()
    current = self._mainPanel.getLineUserParam(currentLine)
    paramTypes = current.getParamTypesConcrete()
    if len(paramTypes) == 0:
      return None
    elif len(paramTypes) == 1:
      return 'mod'
    else:
      return None
   
  def searchCommand(self):
    count = 0
    st= "searching..."
    self._statusInterface.quickUpdateBottomStatusText(st)
    iter = self._mailbox.items()
    self._results = []
    for (key, message) in iter:
      if self._query.evaluate(message, dict(), dict()) == True:
        self._results.append(message)
    self._resultsFresh = True
    return FeedCmdResult()

  def showCommand(self, force):
    if self._results == None:
      return FeedCmdResult.error('No results to show yet (use \'search\' command first).')
    if self._resultsFresh == False and not force:
      return FeedCmdResult.error('The query has been changed. To show the previous '+\
                                 'results, use \'show!\' command.')
    mbox = mailbox.Maildir('.tmp.mail.dir', None, True)
    mbox.clear()
    for message in self._results:
      mbox.add(message)
    mbox.close()
    self._mainLayout.save()
    curses.savetty()
    os.system('mutt -f .tmp.mail.dir')
    self._mainLayout.restore()
    curses.resetty()
    return FeedCmdResult()

  def updateStatus(self):
    if self._query.isComplete():
      if self._resultsFresh == True:
        text = str(len(self._results))+' messages found'
      elif self._resultsFresh == False:
        text = 'query changed (previously: '+str(len(self._results))+' messages found)'
      else: # None - no results yet
        text = ''
    else:
      if self._resultsFresh == True:
        raise BaseException("Internal error") # means we've evaluated an incomplete query
      elif self._resultsFresh == False:
        text = 'query changed and incomplete (was: '+str(len(self._results))+' messages found)'
      else: # None - no results yet
        text = 'query incomplete'
    self._statusInterface.setBottomStatusText(text) 

  def feedCmd(self, cmdline):
    """Processes a command.
       Returns structure:
         (boolean, boolean, boolean, string, 'info'/'error')
       boolean means 'quit application'
       the other boolean means 'clear the cmd line'
       the third boolean means 'enter input mode'"""
    parts = re.split('\s+', cmdline)
    forceReplace = False
    if len(parts) == 1:
      cmd = parts[0]
      arg = None
    elif len(parts) == 2:
      if parts[0] == 'r':
        forceReplace = True
        cmd = parts[1]
        arg = None
      else:
        cmd = parts[0]
        arg = parts[1]
    elif len(parts) == 3 and parts[0] == 'r':
      forceReplace = True
      cmd = parts[1]
      arg = parts[2]
    else:
      return FeedCmdResult.error('Syntax error')

    if cmd == '':
      defCmd = self.defCommand()
      if defCmd != None:
        ret = self.feedCmd(defCmd)
      else:
        ret = FeedCmdResult()
    elif cmd == 'quit':
      ret = FeedCmdResult()
      ret.quit = True
    elif cmd == 'search':
      ret = self.searchCommand()
    elif cmd == 'show':
      ret = self.showCommand(False)
    elif cmd == 'show!':
      ret = self.showCommand(True)
    elif cmd == 'rm':
      currentLine = self._mainPanel.getSelected()
      current = self._mainPanel.getLineUserParam(currentLine)
      if current.remove():
        ret = FeedCmdResult.rm()
      else:
        ret = FeedCmdResult.error('Cannot remove this expression')
    elif cmd == 'mod':
      currentLine = self._mainPanel.getSelected()
      current = self._mainPanel.getLineUserParam(currentLine)
      ret = self.modCommand(current, currentLine)
    elif cmd == 'more':
      currentLine = self._mainPanel.getSelected()
      current = self._mainPanel.getLineUserParam(currentLine)
      ret = self.moreCommand(current, currentLine)
    elif cmd == 'expand':
      currentLine = self._mainPanel.getSelected()
      current = self._mainPanel.getLineUserParam(currentLine)
      if isinstance(current, ExprForAll) or isinstance(current, ExprExists):
        ret = self.expandCommand(current, currentLine)
      else:
        ret = FeedCmdResult.error("Cannot expand this expression")
    elif cmd in self._exprCommands:
      currentLine = self._mainPanel.getSelected()
      current = self._mainPanel.getLineUserParam(currentLine)
      if cmd == 'and' or cmd == 'or':
        if forceReplace or current.uiCanReplaceWoWarning():
          ret = self.standardCreateCommand(cmd, arg, current, currentLine)
        elif not forceReplace and current.getType() == ET.Bool:
          if isinstance(current.getParent(), ExprAnd) and cmd == 'and' or\
             isinstance(current.getParent(), ExprOr) and cmd == 'or':
            ret = self.addAndOrSiblingCommand(cmd, arg, current, currentLine)
          else:
            ret = self.pushDownWithAndOrCommand(cmd, arg, current, currentLine)
        else:
          ret = FeedCmdResult.error('ERROR: You must use r[epl[ace]] to replace this expression')
      elif not forceReplace and (cmd == 'forall' or cmd == 'exists'):
        if current.getType() == ET.Bool:
          ret = self.pushDownWithQuantifier(cmd, arg, current, currentLine)
        elif current.getParent().getType() == ET.Bool:
          ret = self.pushFarDownWithQuantifier(cmd, arg, current, currentLine)
      else:
        if forceReplace or current.uiCanReplaceWoWarning():
          ret = self.standardCreateCommand(cmd, arg, current, currentLine)
        else:
          ret = FeedCmdResult.error('ERROR: You must use r[epl[ace]] to replace this expression')
    else:
      ret = FeedCmdResult.error('ERROR: Unknown command: >'+cmdline+'<')
    if ret.change != None:
      if self._resultsFresh == True: self._resultsFresh = False
      self._mainPanel.clear()
      for (indent, text, obj) in self._query.uiGetRendering():
        self._mainPanel.addLine('  '*indent+text, obj)
    self.updateStatus()
    return ret


global errorMsg
errorMsg = None

def main(stdscr, *args, **kwds):
  if (len(sys.argv) != 2):
    global errorMsg
    errorMsg = "Usage: moss <mailbox/maildir path>"
    return

  mboxName = sys.argv[1]

  mainLayout = MainLayout(stdscr)
  mainPanel = MainPanel(stdscr)

  engine = Engine()

  mainLayout.setMainPanel(mainPanel)
  mainLayout.setCmdListener(engine)

  engine.setMainPanel(mainPanel)
  engine.setStatusInterface(mainLayout)
  engine.setMainLayout(mainLayout)
  engine.setMailbox(mboxName)

  mainLayout.run()

curses.wrapper( main )
if errorMsg != None:
  print errorMsg

