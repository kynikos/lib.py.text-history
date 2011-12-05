# TextHistory - A simple undo/redo engine for plain text and wxPython TextCtrl.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.com>
#
# This file is part of TextHistory.
#
# TextHistory is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# TextHistory is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TextHistory.  If not, see <http://www.gnu.org/licenses/>.

from distutils.core import setup

setup(name='texthistory',
      version='1.0.0pb1',
      description='A simple undo/redo engine for plain text and wxPython '
                  'TextCtrl.',
      author='Dario Giovannetti',
      author_email='dev@dariogiovannetti.com',
      url='https://github.com/kynikos/text-history',
      license='GPLv3',
      packages=['texthistory'])
