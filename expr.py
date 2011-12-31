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

##### Base types ####################################################

class ET:
  """Expression Type"""
  Bool         = 0
  Int          = 1
  String       = 2
  Size         = 3
  Attachment   = 4
  Var          = 5
  Type         = 6

# Note. Using 'object' as a base class makes this a "new style"
# class, which, among other things, allows to find all
# subclasses using __subclasses__().
class Expr(object):

  #---- to be called by: anybody

  def __init__(self, etype, constParams, params):
    self._etype = etype
    self._constParams = constParams
    self._parent = None

  def copyWithEnv(self, env):
    raise BaseException("Abstract class")

  def setParam(self, name, value):
    raise BaseException("Invalid parameter")

  # RETURN: set of ET
  @staticmethod
  def getPossibleTypes():
    raise BaseException("Abstract class")

  # RETURN: map: string -> ET
  @staticmethod
  def getConstParamTypes(etype):
    return dict()

  # RETURN: map: string -> ET
  @staticmethod
  def getParamTypes(etype, constParams):
    return dict()

  def getParamTypesConcrete(self):
    return self.__class__.getParamTypes(self._etype, self._constParams)

  # RETURN: ET
  def getType(self):
    raise BaseException("Abstract class")

  def isTypeList(self):
    return False

  # Will return False if it is not possible to remove.
  # RETURN: True or False
  def remove(self):
    if self._parent != None:
      return self._parent.removeChild(self)
    else:
      return False

  # RETURN: -
  def replace(self, expr):
    if self._parent != None:
      self._parent.replaceChild(self, expr)

  def getParent(self):
    return self._parent

  #---- to be called by: Expression

  # RETURN: -
  def setParent(self, parent):
    self._parent = parent

  # Will return False if it is not possible to remove the child
  # RETURN: True or False
  def removeChild(self, child):
    raise BaseException("Abstract class")

  # RETURN: -
  def replaceChild(self, child, expr):
    raise BaseException("Abstract class")

  # RETURN: list of Expression
  def getFlatTree(self):
    raise BaseException("Abstract class")

##### NULL Expression ###############################################

#----- to be created by: Expression
class ExprNull(Expr):

  def __init__(self, etype, constParams, params):
    Expr.__init__(self, etype, constParams, params)
    self._etype = etype

  def copyWithEnv(self, env, parent):
    expr = ExprNull(self._etype, self._constParams, dict())
    expr.setParent(parent)

  @staticmethod
  def getPossibleTypes():
    return set((ET.Bool, ET.Int, ET.String, ET.Size, ET.Attachment))

  def getType(self):
    return self._etype

  def removeChild(self, child):
    raise BaseException("Not my child")

  def replaceChild(self, child, expr):
    raise BaseException("Not my child")

  def getFlatTree(self):
    return [self]

##### Concrete Expressions ##########################################

class ExprSubstring(Expr):

  def __init__(self, etype, constParams, params):
    Expr.__init__(self, etype, constParams, params)
    self._childSub = ExprNull(ET.String, dict(), dict())
    self._childSub.setParent(self)
    self._childSuper = ExprNull(ET.String, dict(), dict())
    self._childSuper.setParent(self)

  def copyWithEnv(self, env, parent):
    expr = ExprSubstring(self._etype, self._constParams, dict())
    expr.setParent(parent)
    expr._childSub = self._childSub.copyWithEnv(env, expr)
    expr._childSuper = self._childSuper.copyWithEnv(env, expr)
    return expr

  @staticmethod
  def getPossibleTypes():
    return set((ET.Bool,))

  def getType(self):
    return ET.Bool

  def removeChild(self, child):
    if child is self._childSub:
      self._childSub = ExprNull(ET.String)
      self._childSub.setParent(self)
    elif child is self._childSuper:
      self._childSuper = ExprNull(ET.String)
      self._childSuper.setParent(self)
    else:
      raise BaseException("Not my child")

  def replaceChild(self, child, expr):
    if child is self._childSub:
      self._childSub = expr
      self._childSub.setParent(self)
    elif child is self._childSuper:
      self._childSuper = expr
      self._childSuper.setParent(self)
    else:
      raise BaseException("Not my child")

  def getFlatTree(self):
    l = [self]
    l.extend(self._childSub.getFlatTree())
    l.extend(self._childSuper.getFlatTree())
    return l

class ExprAnd(Expr):

  def __init__(self, etype, constParams, params):
    Expr.__init__(self, etype, constParams, params)
    self._children = [
      ExprNull(ET.Bool, dict(), dict()),
      ExprNull(ET.Bool, dict(), dict())
    ]
    self._children[0].setParent(self)
    self._children[1].setParent(self)

  def copyWithEnv(self, env, parent):
    expr = ExprAnd(self._etype, self._constParams, dict())
    expr.setParent(parent)
    expr._children = []
    for child in self._children:
      expr._children.append(child.copyWithEnv(env, expr))
    return expr

  @staticmethod
  def getPossibleTypes():
    return set((ET.Bool,))

  def getType(self):
    return ET.Bool

  def removeChild(self, child):
    if len(self._children) <= 1:
      return False
    for i in range(len(self._children)):
      if self._children[i] is child:
        del self._children[i]
        return True
    raise BaseException("Not my child")

  def replaceChild(self, child, expr):
    for i in range(len(self._children)):
      if self._children[i] is child:
        self._children[i] = expr
        expr.setParent(self)
        return
    raise BaseException("Not my child")

  def getFlatTree(self):
    l = [self]
    for child in self._children:
      l.extend(child.getFlatTree)
    return l

class ExprOr(Expr):

  def __init__(self, etype, constParams, params):
    Expr.__init__(self, etype, constParams, params)
    self._children = [
      ExprNull(ET.Bool, dict(), dict()),
      ExprNull(ET.Bool, dict(), dict())
    ]
    self._children[0].setParent(self)
    self._children[1].setParent(self)

  def copyWithEnv(self, env, parent):
    expr = ExprOr(self._etype, self._constParams, dict())
    expr.setParent(parent)
    expr._children = []
    for child in self._children:
      expr._children.append(child.copyWithEnv(env, expr))
    return expr

  @staticmethod
  def getPossibleTypes():
    return set((ET.Bool,))

  def getType(self):
    return ET.Bool

  def removeChild(self, child):
    if len(self._children) <= 1:
      return False
    for i in range(len(self._children)):
      if self._children[i] is child:
        del self._children[i]
        return True
    raise BaseException("Not my child")

  def replaceChild(self, child, expr):
    for i in range(len(self._children)):
      if self._children[i] is child:
        self._children[i] = expr
        expr.setParent(self)
        return
    raise BaseException("Not my child")

  def getFlatTree(self):
    l = [self]
    for child in self._children:
      l.extend(child.getFlatTree)
    return l

class ExprForAll(Expr):

  def __init__(self, etype, constParams, params):
    Expr.__init__(self, etype, constParams, params)
    if etype != ET.Bool:
      raise BaseException("Wrong type")
    if not 'variable type' in constParams:
      raise BaseException("Missing const parameter") 
    self._varType = constParams['variable type']
    if 'variable name' in params:
      self._varName = params['variable name']
    else:
      self._varName = '_'
    self._values = [ExprNull(self._varType, dict(), dict())]
    self._values[0].setParent(self)
    self._expr = ExprNull(ET.Bool, dict(), dict())
    self._expr.setParent(self)

  def copyWithEnv(self, env, parent):
    expr = ExprForAll(self._etype, self._constParams, dict())
    expr._varName = self._varName
    expr._expr = self._expr.copyWithEnv(env, expr)
    expr._values = []
    for value in self._values:
      expr._values.append(value.copyWithEnv(env, expr))
    return expr

  def setParam(self, name, value):
    if name == 'variable name':
      self._varName = value
    else:
      raise BaseException("Invalid parameter")

  @staticmethod
  def getPossibleTypes():
    return set((ET.Bool,))

  @staticmethod
  def getConstParamTypes(etype):
    d = dict()
    d['variable type'] = ET.Type
    return d

  @staticmethod
  def getParamTypes(etype, constParams):
    d = dict()
    d['variable name'] = constParams['variable type']
    return d

  def getType(self):
    return ET.Bool

  def removeChild(self, child):
    if child is self._expr:
      return False
    if len(self._values) <= 1:
      return False
    for i in range(len(self._values)):
      if self._values[i] is child:
        del self._values[i]
        return True
    raise BaseException("Not my child")

  def replaceChild(self, child, expr):
    if child is self._expr:
      self._expr = expr
      self._expr.setParent(self)
      return
    for i in range(len(self._values)):
      if self._values[i] is child:
        self._values[i] = expr
        expr.setParent(self)
        return
    raise BaseException("Not my child")

  def getFlatTree(self):
    l = [self]
    for val in self._values:
      l.extend(val.getFlatTree)
    l.extend(self._expr.getFlatTree)
    return l

class ExprExists(Expr):

  def __init__(self, etype, constParams, params):
    Expr.__init__(self, etype, constParams, params)
    if etype != ET.Bool:
      raise BaseException("Wrong type")
    if not 'variable type' in constParams:
      raise BaseException("Missing const parameter") 
    self._varType = constParams['variable type']
    if 'variable name' in params:
      self._varName = params['variable name']
    else:
      self._varName = '_'
    self._values = [ExprNull(self._varType, dict(), dict())]
    self._values[0].setParent(self)
    self._expr = ExprNull(ET.Bool, dict(), dict())
    self._expr.setParent(self)

  def copyWithEnv(self, env, parent):
    expr = ExprExists(self._etype, self._constParams, dict())
    expr.setParent(parent)
    expr._varName = self._varName
    expr._expr = self._expr.copyWithEnv(env, expr)
    expr._values = []
    for value in self._values:
      expr._values.append(value.copyWithEnv(env, expr))
    return expr
 
  def setParam(self, name, value):
    if name == 'variable name':
      self._varName = value
    else:
      raise BaseException("Invalid parameter")

  @staticmethod
  def getPossibleTypes():
    return set((ET.Bool,))

  @staticmethod
  def getConstParamTypes(etype):
    d = dict()
    d['variable type'] = ET.Type
    return d

  @staticmethod
  def getParamTypes(etype, constParams):
    d = dict()
    d['variable name'] = constParams['variable type']
    return d

  def getType(self):
    return ET.Bool

  def removeChild(self, child):
    if child is self._expr:
      return False
    if len(self._values) <= 1:
      return False
    for i in range(len(self._values)):
      if self._values[i] is child:
        del self._values[i]
        return True
    raise BaseException("Not my child")

  def replaceChild(self, child, expr):
    if child is self._expr:
      self._expr = expr
      self._expr.setParent(self)
      return
    for i in range(len(self._values)):
      if self._values[i] is child:
        self._values[i] = expr
        expr.setParent(self)
        return
    raise BaseException("Not my child")

  def getFlatTree(self):
    l = [self]
    for val in self._values:
      l.extend(val.getFlatTree)
    l.extend(self._expr.getFlatTree)
    return l

class ExprConst(Expr):

  def __init__(self, etype, constParams, params):
    Expr.__init__(self, etype, constParams, params)
    self._etype = etype
    if 'value' in params:
      self._value = params['value']
    else:
      if self._etype == ET.String:
        self._value = ""
      elif self._etype == ET.Int:
        self._value = 0
      else:
        raise BaseException("Internal error")

  def copyWithEnv(self, env, parent):
    expr = ExprConst(self._etype, self._constParams, dict())
    expr.setParent(parent)
    expr._value = self._value
    return expr
 
  def setParam(self, name, value):
    if name == 'value':
      self._value = value
    else:
      raise BaseException("Invalid parameter")

  @staticmethod
  def getPossibleTypes():
    return set((ET.Int, ET.String, ET.Size))

  def getType(self):
    return self._etype

  @staticmethod
  def getParamTypes(etype, constParams):
    d = dict()
    if etype == ET.Int:
      d['value'] = ET.Int
    elif etype == ET.String:
      d['value'] = ET.String
    elif etype == ET.Size:
      d['value'] = ET.Size
    return d

  def removeChild(self, child):
    raise BaseException("Not my child")

  def replaceChild(self, child, expr):
    raise BaseException("Not my child")

  def getFlatTree(self):
    return [self]

class ExprVar(Expr):

  def __init__(self, etype, constParams, params):
    Expr.__init__(self, etype, constParams, params)
    self._etype = etype
    if 'id' in params:
      self._id = params['id']
    else:
      self._id = '_'

  def copyWithEnv(self, env, parent):
    if self._id in env:
      expr = env[self._id]
    else:
      expr = ExprVar(self._etype, self._constParams, dict())
      expr._id = self._id
    expr.setParent(parent)
    return expr

  def setParam(self, name, value):
    if name == 'id':
      self._id = value
    else:
      raise BaseException("Invalid parameter")

  @staticmethod
  def getPossibleTypes():
    return set((ET.Int, ET.String, ET.Size, ET.Attachment))

  def getType(self):
    return self._etype

  @staticmethod
  def getParamTypes(etype, constParams):
    d = dict()
    d['id'] = ET.Var
    return d

  def removeChild(self, child):
    raise BaseException("Not my child")

  def replaceChild(self, child, expr):
    raise BaseException("Not my child")

  def getFlatTree(self):
    return [self]

class ExprCustomHeader(Expr):

  def __init__(self, etype, constParams, params):
    Expr.__init__(self, etype, constParams, params)
    if 'name' in params:
      self._name = params['name']
    else:
      self._name = None

  def copyWithEnv(self, env, parent):
    expr = ExprCustomHeader(self._etype, self._constParams, dict())
    expr.setParent(parent)
    expr._name = self._name
    return expr

  def setParam(self, name, value):
    if name == 'name':
      self._name = value
    else:
      raise BaseException("Invalid parameter")

  @staticmethod
  def getPossibleTypes():
    return set((ET.String,))

  def getType(self):
    return ET.String

  @staticmethod
  def getParamTypes(self, constParams):
    d = dict()
    d['name'] = ET.String
    return d

  def removeChild(self, child):
    raise BaseException("Not my child")

  def replaceChild(self, child, expr):
    raise BaseException("Not my child")

  def getFlatTree(self):
    return [self]


class ExprAllAttachments(Expr):

  def __init__(self, etype, constParams, params):
    Expr.__init__(self, etype, constParams, params)

  def copyWithEnv(self, env, parent):
    expr = ExprAllAttachments(self._etype, self._constParams, dict())
    expr.setParent(parent)
    return expr

  def setParam(self, name, value):
    raise BaseException("Invalid parameter")

  @staticmethod
  def getPossibleTypes():
    return set((ET.Attachment,))

  def getType(self):
    return ET.Attachment

  def isTypeList(self):
    return True

  @staticmethod
  def getParamTypes(self, constParams):
    return dict()

  def removeChild(self, child):
    raise BaseException("Not my child")

  def replaceChild(self, child, expr):
    raise BaseException("Not my child")

  def getFlatTree(self):
    return [self]

class ExprAttSize(Expr):

  def __init__(self, etype, constParams, params):
    Expr.__init__(self, etype, constParams, params)
    self._child = ExprNull(ET.Attachment, dict(), dict())
    self._child.setParent(self)

  def copyWithEnv(self, env, parent):
    expr = ExprAttSize(self._etype, self._constParams, dict())
    expr.setParent(parent)
    expr._child = self._child.copyWithEnv(env, expr)
    return expr

  @staticmethod
  def getPossibleTypes():
    return set((ET.Int,))

  def getType(self):
    return ET.Int

  def removeChild(self, child):
    if child is self._child:
      self._child = ExprNull(ET.String)
      self._child.setParent(self)
      self._child.setParent(self)
    else:
      raise BaseException("Not my child")

  def replaceChild(self, child, expr):
    if child is self._child:
      self._child = expr
      self._child.setParent(self)
    else:
      raise BaseException("Not my child")

  def getFlatTree(self):
    l = [self]
    l.extend(self._child.getFlatTree())
    return l

class ExprGt(Expr):

  def __init__(self, etype, constParams, params):
    Expr.__init__(self, etype, constParams, params)
    self._left = ExprNull(ET.Int, dict(), dict())
    self._left.setParent(self)
    self._right = ExprNull(ET.Int, dict(), dict())
    self._right.setParent(self)

  def copyWithEnv(self, env, parent):
    expr = ExprAttSize(self._etype, self._constParams, dict())
    expr.setParent(parent)
    expr._left = self._left.copyWithEnv(env, expr)
    expr._right = self._right.copyWithEnv(env, expr)
    return expr

  @staticmethod
  def getPossibleTypes():
    return set((ET.Bool,))

  def getType(self):
    return ET.Bool

  def removeChild(self, child):
    if child is self._left:
      self._left= ExprNull(ET.String)
      self._left.setParent(self)
      self._left.setParent(self)
    elif child is self._right:
      self._right= ExprNull(ET.String)
      self._right.setParent(self)
      self._right.setParent(self)
    else:
      raise BaseException("Not my child")

  def replaceChild(self, child, expr):
    if child is self._left:
      self._left = expr
      self._left.setParent(self)
    elif child is self._right:
      self._right = expr
      self._right.setParent(self)
    else:
      raise BaseException("Not my child")

  def getFlatTree(self):
    l = [self]
    l.extend(self._left.getFlatTree())
    l.extend(self._right.getFlatTree())
    return l
