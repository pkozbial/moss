#/usr/bin/env python
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

import email
import email.header
import re


# TODO !!!
# What about multiline headers?
# Like the subject in:
#   message-id b46f87d41076c0d5d2537eb910c17209@sympatycypis.pl

# This (pattern and function headerDecodeSafely)
# was inspired by the discussion under:
#   http://bugs.python.org/issue10574
# especially:
#   http://bugs.python.org/msg122774
# But in fact my code doesn't much resemble
# that one.

headerDecodeSafely_pattern = re.compile( \
  r'(=\?.*?\?[qb]\?.*?\?=)', \
  re.VERBOSE | re.IGNORECASE | re.MULTILINE)

def headerDecodeSafely(headerText):
  """A wrapper/replacement for email.header.decode_header(),
     because that last one fails in some cases"""
  # TODO !!!
  # Some messasges (e.g. ones from mailing@poczta.fm,
  # example message-id dcf05231c492569270f19d3f1780e475@interia.pl)
  # use non-ASCII encoding in "Subject" header, but without
  # properly marking it (with =?...).
  # We could detect this: if we have a part of "Subject" (what about
  # other headers?) that is not apparently encoded (with =?...),
  # but fails to decode as ascii, we could try to decode it as
  # the encoding content-type of the message body (or something).
  text = headerText
  if text == None:
    text = ''
  out = []
  while True:
    match = headerDecodeSafely_pattern.search(text)
    if match == None:
      out.append((text, None))
      return out
    else:
      if match.start() > 0:
        out.append((text[:match.start()], None))
        text = text[match.start():]
      out.extend(email.header.decode_header(match.group(0)))
      text = text[len(match.group(0)):]

def headerToUnicode(message, headerName):
  """Take the header named `headerName' from the Message
     `message', decode it (as international email header),
     then concatenate all the decoded parts into one
     Unicode string.
     PARAM message : Message
     PARAM headerName : string
     RETURNS Unicode string
     !!
     WARNING. May raise exceptions.
     !!
     TODO. Catch the exceptions and deal with them."""
  list = message.get(headerName)
  out = u""
  for pair in headerDecodeSafely(message.get(headerName)):
    (text, encoding) = pair
#    print "TEXT >>{0}<< enc >>{1}<<".format( text, encoding )
    if encoding == None:
      out += unicode(text, 'ascii', 'replace')
    else:
      out += unicode(text, encoding, 'replace')
  return out




