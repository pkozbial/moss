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

### class ExprAnd

def _ExprAnd_addChild(self, expr):
  self._children.append(expr)
  expr.setParent(self)
ExprAnd.addChild = _ExprAnd_addChild

def _ExprAnd_replaceChildren(self, newChildren):
  self._children = []
  for child in newChildren:
    self.addChild(child)
ExprAnd.replaceChildren = _ExprAnd_replaceChildren

### class ExprOr

def _ExprOr_addChild(self, expr):
  self._children.append(expr)
  expr.setParent(self)
ExprOr.addChild = _ExprOr_addChild

def _ExprOr_replaceChildren(self, newChildren):
  self._children = []
  for child in newChildren:
    self.addChild(child)
ExprOr.replaceChildren = _ExprOr_replaceChildren

### class ExprForAll

def _ExprForAll_addValue(self, expr):
  self._values.append(expr)
  expr.setParent(self)
ExprForAll.addValue = _ExprForAll_addValue

def _ExprForAll_replaceExpr(self, expr):
  self._expr = expr
  expr.setParent(self)
ExprForAll.replaceExpr = _ExprForAll_replaceExpr

def _ExprForAll_replaceValues(self, newValues):
  self._values = []
  for value in newValues:
    self.addValue(value)
ExprForAll.replaceValues = _ExprForAll_replaceValues

def _ExprForAll_copyExpanded(self, parent):
  if len(self._values) == 1:
    env = dict()
    env[self._varName] = self._values[0]
    expr = self._expr.copyWithEnv(env, parent)
  else:
    expr = ExprAnd(ET.Bool, dict(), dict())
    children = []
    for value in self._values:
      env = dict()
      env[self._varName] = value
      children.append(self._expr.copyWithEnv(env, expr))
    expr.replaceChildren(children)
    expr.setParent(parent)
  return expr
ExprForAll.copyExpanded = _ExprForAll_copyExpanded

### class ExprExists

def _ExprExists_addValue(self, expr):
  self._values.append(expr)
  expr.setParent(self)
ExprExists.addValue = _ExprExists_addValue

def _ExprExists_replaceExpr(self, expr):
  self._expr = expr
  expr.setParent(self)
ExprExists.replaceExpr = _ExprExists_replaceExpr

def _ExprExists_replaceValues(self, newValues):
  self._values = []
  for value in newValues:
    self.addValue(value)
ExprExists.replaceValues = _ExprExists_replaceValues

def _ExprExists_copyExpanded(self, parent):
  if len(self._values) == 1:
    env = dict()
    env[self._varName] = self._values[0]
    expr = self._expr.copyWithEnv(env, parent)
  else:
    expr = ExprOr(ET.Bool, dict(), dict())
    children = []
    for value in self._values:
      env = dict()
      env[self._varName] = value
      children.append(self._expr.copyWithEnv(env, expr))
    expr.replaceChildren(children)
    expr.setParent(parent)
  return expr
ExprExists.copyExpanded = _ExprExists_copyExpanded
