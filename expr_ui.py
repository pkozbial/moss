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

from expr import *

### class ET

@staticmethod
def _ET_toStr(val):
  if val == ET.Bool:
    return 'Bool'
  elif val == ET.Int:
    return 'Int'
  elif val == ET.String:
    return 'String'
  elif val == ET.Size:
    return 'Size'
  elif val == ET.Attachment:
    return 'Attachment'
  elif val == ET.Var:
    return 'Var'
  else:
    raise BaseException("Unknown ET value")
ET.toStr = _ET_toStr

@staticmethod
def _ET_fromStr(str):
  if str == 'bool':
    return ET.Bool
  elif str == 'int':
    return ET.Int
  elif str == 'string':
    return ET.String
  elif str == 'size':
    return ET.Size
  elif str == 'attachment':
    return ET.Attachment
  else:
    return None
ET.fromStr = _ET_fromStr

### class Expr

def _Expr_uiGetRendering(self):
  raise BaseException("Abstract class")
Expr.uiGetRendering = _Expr_uiGetRendering

def _Expr_uiGetBaseIndent(self):
  if self._parent == None:
    return 0
  else:
    return self._parent.uiGetBaseIndent() + \
           self._parent._uiGetIndentForChild(self)
Expr.uiGetBaseIndent = _Expr_uiGetBaseIndent
  
def _Expr__uiGetIndentForChild(self, child):
  raise BaseException("Abstract class")
Expr._uiGetIndentForChild = _Expr__uiGetIndentForChild

def _Expr_uiPosHintCreate(self):
  raise BaseException("Abstract class")
Expr.uiPosHintCreate = _Expr_uiPosHintCreate

def _Expr_uiPosHintRemove(self):
  raise BaseException("Abstract class")
Expr.uiPosHintRemove = _Expr_uiPosHintRemove

@staticmethod
def _Expr_uiGetCmdName():
  raise BaseException("Abstract class")
Expr.uiGetCmdName = _Expr_uiGetCmdName

@staticmethod
def _Expr_uiCanReplaceWoWarning():
  return False
Expr.uiCanReplaceWoWarning = _Expr_uiCanReplaceWoWarning

### class ExprNull

def _ExprNull_uiGetRendering(self):
  return [(0, '<?:'+ET.toStr(self._etype)+'>', self)]
ExprNull.uiGetRendering = _ExprNull_uiGetRendering

def _ExprNull__uiGetIndentForChild(self, child):
  raise BaseException("Not my child")
ExprNull._uiGetIndentForChild = _ExprNull__uiGetIndentForChild

def _ExprNull_uiPosHintCreate(self):
  return self
ExprNull.uiPosHintCreate = _ExprNull_uiPosHintCreate

def _ExprNull_uiPosHintRemove(self):
  return self._parent
ExprNull.uiPosHintRemove = _ExprNull_uiPosHintRemove

@staticmethod
def _ExprNull_uiGetCmdName():
  return 'null'
ExprNull.uiGetCmdName = _ExprNull_uiGetCmdName

@staticmethod
def _ExprNull_uiCanReplaceWoWarning():
  return True
ExprNull.uiCanReplaceWoWarning = _ExprNull_uiCanReplaceWoWarning

### class ExprSubstring

def _ExprSubstring_uiGetRendering(self):
  l = [(0, 'SUBSTRING', self)]
  for (indent, text, obj) in self._childSub.uiGetRendering():
    l.append((1+indent, text, obj))
  for (indent, text, obj) in self._childSuper.uiGetRendering():
    l.append((1+indent, text, obj))
  return l
ExprSubstring.uiGetRendering = _ExprSubstring_uiGetRendering

def _ExprSubstring__uiGetIndentForChild(self, child):
  if child is self._childSub:
    return 1
  elif child is self._childSuper:
    return 1
  else:
    raise BaseException("Not my child")
ExprSubstring._uiGetIndentForChild = _ExprSubstring__uiGetIndentForChild

def _ExprSubstring_uiPosHintCreate(self):
  return self._childSub
ExprSubstring.uiPosHintCreate = _ExprSubstring_uiPosHintCreate

def _ExprSubstring_uiPosHintRemove(self):
  return self._parent
ExprSubstring.uiPosHintRemove = _ExprSubstring_uiPosHintRemove

@staticmethod
def _ExprSubstring_uiGetCmdName():
  return 'substring'
ExprSubstring.uiGetCmdName = _ExprSubstring_uiGetCmdName

### class ExprAnd

def _ExprAnd_uiGetRendering(self):
  l = [(0, 'AND', self)]
  for child in self._children:
    for (indent, text, obj) in child.uiGetRendering():
      l.append((1+indent, text, obj))
  return l
ExprAnd.uiGetRendering = _ExprAnd_uiGetRendering
  
def _ExprAnd__uiGetIndentForChild(self, child):
  if child in self._children:
    return 1
  else:
    raise BaseException("Not my child")
ExprAnd._uiGetIndentForChild = _ExprAnd__uiGetIndentForChild

def _ExprAnd_uiPosHintCreate(self):
  return self._children[0]
ExprAnd.uiPosHintCreate = _ExprAnd_uiPosHintCreate

def _ExprAnd_uiPosHintRemove(self):
  return self._parent
ExprAnd.uiPosHintRemove = _ExprAnd_uiPosHintRemove

@staticmethod
def _ExprAnd_uiGetCmdName():
  return 'and'
ExprAnd.uiGetCmdName = _ExprAnd_uiGetCmdName

@staticmethod
def _ExprAnd_uiCanReplaceWoWarning():
  return False
ExprAnd.uiCanReplaceWoWarning = _ExprAnd_uiCanReplaceWoWarning

### class ExprOr

def _ExprOr_uiGetRendering(self):
  l = [(0, 'OR', self)]
  for child in self._children:
    for (indent, text, obj) in child.uiGetRendering():
      l.append((1+indent, text, obj))
  return l
ExprOr.uiGetRendering = _ExprOr_uiGetRendering
  
def _ExprOr__uiGetIndentForChild(self, child):
  if child in self._children:
    return 1
  else:
    raise BaseException("Not my child")
ExprOr._uiGetIndentForChild = _ExprOr__uiGetIndentForChild

def _ExprOr_uiPosHintCreate(self):
  return self._children[0]
ExprOr.uiPosHintCreate = _ExprOr_uiPosHintCreate

def _ExprOr_uiPosHintRemove(self):
  return self._parent
ExprOr.uiPosHintRemove = _ExprOr_uiPosHintRemove

@staticmethod
def _ExprOr_uiGetCmdName():
  return 'or'
ExprOr.uiGetCmdName = _ExprOr_uiGetCmdName

@staticmethod
def _ExprOr_uiCanReplaceWoWarning():
  return False
ExprOr.uiCanReplaceWoWarning = _ExprOr_uiCanReplaceWoWarning

### class ExprForAll

def _ExprForAll_uiGetRendering(self):
  l = [(0, 'FOR ALL '+self._varName+':'+ET.toStr(self._varType), self)]
  for value in self._values:
    for (indent, text, obj) in value.uiGetRendering():
      l.append((2+indent, text, obj))
  for (indent, text, obj) in self._expr.uiGetRendering():
    l.append((1+indent, text, obj))
  return l
ExprForAll.uiGetRendering = _ExprForAll_uiGetRendering
  
def _ExprForAll__uiGetIndentForChild(self, child):
  if child == self._expr:
    return 1
  elif child in self._values:
    return 2
  else:
    raise BaseException("Not my child")
ExprForAll._uiGetIndentForChild = _ExprForAll__uiGetIndentForChild

def _ExprForAll_uiPosHintCreate(self):
  return self._values[0]
ExprForAll.uiPosHintCreate = _ExprForAll_uiPosHintCreate

def _ExprForAll_uiPosHintRemove(self):
  return self._parent
ExprForAll.uiPosHintRemove = _ExprForAll_uiPosHintRemove

@staticmethod
def _ExprForAll_uiGetCmdName():
  return 'forall'
ExprForAll.uiGetCmdName = _ExprForAll_uiGetCmdName

@staticmethod
def _ExprForAll_uiCanReplaceWoWarning():
  return False
ExprForAll.uiCanReplaceWoWarning = _ExprForAll_uiCanReplaceWoWarning

### class ExprExists

def _ExprExists_uiGetRendering(self):
  l = [(0, 'EXISTS '+self._varName+':'+ET.toStr(self._varType), self)]
  for value in self._values:
    for (indent, text, obj) in value.uiGetRendering():
      l.append((2+indent, text, obj))
  for (indent, text, obj) in self._expr.uiGetRendering():
    l.append((1+indent, text, obj))
  return l
ExprExists.uiGetRendering = _ExprExists_uiGetRendering
  
def _ExprExists__uiGetIndentForChild(self, child):
  if child == self._expr:
    return 1
  elif child in self._values:
    return 2
  else:
    raise BaseException("Not my child")
ExprExists._uiGetIndentForChild = _ExprExists__uiGetIndentForChild

def _ExprExists_uiPosHintCreate(self):
  return self._values[0]
ExprExists.uiPosHintCreate = _ExprExists_uiPosHintCreate

def _ExprExists_uiPosHintRemove(self):
  return self._parent
ExprExists.uiPosHintRemove = _ExprExists_uiPosHintRemove

@staticmethod
def _ExprExists_uiGetCmdName():
  return 'exists'
ExprExists.uiGetCmdName = _ExprExists_uiGetCmdName

@staticmethod
def _ExprExists_uiCanReplaceWoWarning():
  return False
ExprExists.uiCanReplaceWoWarning = _ExprExists_uiCanReplaceWoWarning


### class ExprConst

def _ExprConst_uiGetRendering(self):
  if self._etype == ET.String:
    l = [(0, '"'+self._value+'"', self)]
  elif self._etype == ET.Int:
    l = [(0, 'TODO: Const Int rendering', self)]
  elif self._etype == ET.Size:
    l = [(0, 'TODO: Const Size rendering', self)]
  elif self._etype == ET.Bool:
    l = [(0, 'TODO: Const Size rendering', self)]
  else:
    l = [(0, 'ERROR: unknown type in Const', self)]
  return l
ExprConst.uiGetRendering = _ExprConst_uiGetRendering
  
def _ExprConst__uiGetIndentForChild(self, child):
  raise BaseException("Not my child")
ExprConst._uiGetIndentForChild = _ExprConst__uiGetIndentForChild

def _ExprConst_uiPosHintCreate(self):
  return self
ExprConst.uiPosHintCreate = _ExprConst_uiPosHintCreate

def _ExprConst_uiPosHintRemove(self):
  return self._parent
ExprConst.uiPosHintRemove = _ExprConst_uiPosHintRemove

@staticmethod
def _ExprConst_uiGetCmdName():
  return 'const'
ExprConst.uiGetCmdName = _ExprConst_uiGetCmdName

@staticmethod
def _ExprConst_uiCanReplaceWoWarning():
  return False
ExprConst.uiCanReplaceWoWarning = _ExprConst_uiCanReplaceWoWarning

### class ExprVar

def _ExprVar_uiGetRendering(self):
  return [(0, self._id+' : '+ET.toStr(self._etype), self)]
ExprVar.uiGetRendering = _ExprVar_uiGetRendering
  
def _ExprVar__uiGetIndentForChild(self, child):
  raise BaseException("Not my child")
ExprVar._uiGetIndentForChild = _ExprVar__uiGetIndentForChild

def _ExprVar_uiPosHintCreate(self):
  return self
ExprVar.uiPosHintCreate = _ExprVar_uiPosHintCreate

def _ExprVar_uiPosHintRemove(self):
  return self._parent
ExprVar.uiPosHintRemove = _ExprVar_uiPosHintRemove

@staticmethod
def _ExprVar_uiGetCmdName():
  return 'var'
ExprVar.uiGetCmdName = _ExprVar_uiGetCmdName

@staticmethod
def _ExprVar_uiCanReplaceWoWarning():
  return False
ExprVar.uiCanReplaceWoWarning = _ExprVar_uiCanReplaceWoWarning

### class ExprCustomHeader

def _ExprCustomHeader_uiGetRendering(self):
  if self._name == None:
    return [(0, 'HEADER ?', self)]
  else:
    return [(0, 'HEADER: '+self._name, self)]
ExprCustomHeader.uiGetRendering = _ExprCustomHeader_uiGetRendering
  
def _ExprCustomHeader__uiGetIndentForChild(self, child):
  raise BaseException("Not my child")
ExprCustomHeader._uiGetIndentForChild = _ExprCustomHeader__uiGetIndentForChild

def _ExprCustomHeader_uiPosHintCreate(self):
  return self
ExprCustomHeader.uiPosHintCreate = _ExprCustomHeader_uiPosHintCreate

def _ExprCustomHeader_uiPosHintRemove(self):
  return self._parent
ExprCustomHeader.uiPosHintRemove = _ExprCustomHeader_uiPosHintRemove

@staticmethod
def _ExprCustomHeader_uiGetCmdName():
  return 'header'
ExprCustomHeader.uiGetCmdName = _ExprCustomHeader_uiGetCmdName

@staticmethod
def _ExprCustomHeader_uiCanReplaceWoWarning():
  return False
ExprCustomHeader.uiCanReplaceWoWarning = _ExprCustomHeader_uiCanReplaceWoWarning
