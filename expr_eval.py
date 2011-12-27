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

import mailbox

from expr import *
import emailextra

### class Expr

def _Expr_isComplete(self):
  raise BaseException("Abstract class")
Expr.isComplete = _Expr_isComplete

# message - the email message to match
# tenv - type environment (var name -> ET)
# venv - value environment (var name -> value)
def _Expr_evaluate(self, message, tenv, venv):
  raise BaseException("Abstract class")
Expr.evaluate = _Expr_evaluate

### class ExprNull

def _ExprNull_isComplete(self):
  return False
ExprNull.isComplete = _ExprNull_isComplete

def _ExprNull_evaluate(self, message, tenv, venv):
  raise BaseException("Evaluation error")
ExprNull.evaluate = _ExprNull_evaluate

### class ExprSubstring

def _ExprSubstring_isComplete(self):
  return self._childSub.isComplete() and self._childSuper.isComplete()
ExprSubstring.isComplete = _ExprSubstring_isComplete

def _ExprSubstring_evaluate(self, message, tenv, venv):
  valueSub = self._childSub.evaluate(message, tenv, venv)
  valueSuper = self._childSuper.evaluate(message, tenv, venv)
  return valueSub in valueSuper
ExprSubstring.evaluate = _ExprSubstring_evaluate

### class And 

def _ExprAnd_isComplete(self):
  for child in self._children:
    if not child.isComplete():
      return False
  return True
ExprAnd.isComplete = _ExprAnd_isComplete

def _ExprAnd_evaluate(self, message, tenv, venv):
  for child in self._children:
    if child.evaluate(message, tenv, venv) == False:
      return False
  return True
ExprAnd.evaluate = _ExprAnd_evaluate

### class Or

def _ExprOr_isComplete(self):
  for child in self._children:
    if not child.isComplete():
      return False
  return True
ExprOr.isComplete = _ExprOr_isComplete

def _ExprOr_evaluate(self, message, tenv, venv):
  for child in self._children:
    if child.evaluate(message, tenv, venv) == True:
      return True
  return False
ExprOr.evaluate = _ExprOr_evaluate

### class ExprForAll

def _ExprForAll_isComplete(self):
  return True
ExprForAll.isComplete = _ExprForAll_isComplete

def _ExprForAll_evaluate(self, message, tenv, venv):
  for value in self._values:
    tenv1 = tenv
    venv1 = venv
    tenv1[self._varName] = self._varType
    venv1[self._varName] = value.evaluate(message, tenv, venv)
    res = self._expr.evaluate(message, tenv1, venv1)
    if res == False:
      return False
  return True
ExprForAll.evaluate = _ExprForAll_evaluate

### class ExprExists

def _ExprExists_isComplete(self):
  return True
ExprExists.isComplete = _ExprExists_isComplete

def _ExprExists_evaluate(self, message, tenv, venv):
  for value in self._values:
    tenv1 = tenv
    venv1 = venv
    tenv1[self._varName] = self._varType
    venv1[self._varName] = value.evaluate(message, tenv, venv)
    res = self._expr.evaluate(message, tenv1, venv1)
    if res == True:
      return True
  return False
ExprExists.evaluate = _ExprExists_evaluate

### class ExprConst

def _ExprConst_isComplete(self):
  return True
ExprConst.isComplete = _ExprConst_isComplete

def _ExprConst_evaluate(self, message, tenv, venv):
  return self._value
ExprConst.evaluate = _ExprConst_evaluate

### class ExprVar

def _ExprVar_isComplete(self):
  return True
ExprVar.isComplete = _ExprVar_isComplete

def _ExprVar_evaluate(self, message, tenv, venv):
  return venv[self._id]
ExprVar.evaluate = _ExprVar_evaluate

### class ExprCustomHeader

def _ExprCustomHeader_isComplete(self):
  return self._name != None
ExprCustomHeader.isComplete = _ExprCustomHeader_isComplete

def _ExprCustomHeader_evaluate(self, message, tenv, venv):
  return emailextra.headerToUnicode(message, self._name)
ExprCustomHeader.evaluate = _ExprCustomHeader_evaluate
