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

"""
TextHistory - A simple undo/redo engine for plain text and wxPython TextCtrl.

@author: Dario Giovannetti
@copyright: Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.com>
@license: GPLv3
@version: 1.0.0pb1
@date: 2011-12-03
"""

from difflib import SequenceMatcher
import sys

try:
    from threading import Timer
except ImportError:
    Timer = None

try:
    import wx
except ImportError:
    wx = None


class TextHistory():
    current = None
    stack = None
    currid = None
    MAX_CHANGES = None
    
    def __init__(self, text, maxchanges=0):
        if not self.checktext(text):
            raise InvalidTextError()
        if maxchanges < 0:
            raise InvalidMaxChangesError()
        
        self.current = text
        self.stack = []
        self.currid = -1
        self.MAX_CHANGES = maxchanges
    
    @staticmethod
    def checktext(text):
        if sys.version_info.major < 3:
            return (isinstance(text, str) or isinstance(text, unicode))
        else:
            return isinstance(text, str)
    
    def _get_changes(self, new):
        s = SequenceMatcher(None, self.current, new)
        opcodes = s.get_opcodes()
        
        changes = []
        
        for op in opcodes:
            if op[0] == 'insert':
                changes.append(('i', None, op[3], op[4]))
            elif op[0] == 'delete':
                changes.append(('d', self.current[op[1]:op[2]], op[3], None))
            elif op[0] == 'replace':
                changes.append(('r', self.current[op[1]:op[2]], op[3], op[4]))
                
        if not changes:
            raise TextUnchangedError()
        
        return changes
    
    def _update_text(self, id_):
        ret = self.current
        shift = 0
        for op in self.stack[id_]:
            if op[0] == 'i':
                ret = ''.join((ret[:op[2] + shift], ret[op[3] + shift:]))
                shift += op[2] - op[3]
            elif op[0] == 'd':
                ret = ''.join((ret[:op[2] + shift], op[1],
                               ret[op[2] + shift:]))
                shift += len(op[1])
            elif op[0] == 'r':
                ret = ''.join((ret[:op[2] + shift], op[1],
                               ret[op[3] + shift:]))
                shift += len(op[1]) - (op[3] - op[2])
        
        self.stack[id_] = self._get_changes(ret)
        self.current = ret
        
        return ret
    
    def add(self, new):
        changes = self._get_changes(new)
        
        if self.currid < 0:
            self.stack = []
        elif self.MAX_CHANGES == 0 or self.currid < self.MAX_CHANGES - 1:
            self.stack = self.stack[:self.currid + 1]
        else:
            base = self.MAX_CHANGES - self.currid
            self.stack = self.stack[base:self.currid + 1]
        
        self.stack.append(changes)
        
        self.current = new
        self.currid = len(self.stack) - 1
        
        return self.currid
    
    def can_undo(self):
        return self._can_undo()
    
    def can_redo(self):
        return self._can_redo()
    
    def _can_undo(self):
        if self.currid < 0:
            return False
        else:
            return True
    
    def _can_redo(self):
        if self.currid >= len(self.stack) - 1:
            return False
        else:
            return True
    
    def undo(self):
        self._undo()
    
    def redo(self):
        self._redo()
    
    def _undo(self):
        if not self._can_undo():
            raise UndoLimitError()
        
        id_ = self.currid
        ret = self._update_text(id_)
        self.currid -= 1
        
        return ret
    
    def _redo(self):
        if not self._can_redo():
            raise RedoLimitError()
        
        id_ = self.currid + 1
        ret = self._update_text(id_)
        self.currid += 1
        
        return ret


class WxTextHistory(TextHistory):
    MIN_UPD_TIME = None
    ctrl = None
    doinghistory = None
    htimer = None
    tmrunning = None
    
    def __init__(self, ctrl, text, maxchanges=0, minupdtime=1):
        if sys.version_info.major != 2:
            raise Python2RequiredError()
        if not Timer:
            raise ThreadingModNotFoundError()
        if not wx:
            raise WxPythonNotFoundError()
        if not isinstance(ctrl, wx._controls.TextCtrl):
            raise InvalidTextCtrlError()
        if not isinstance(minupdtime, int):
            raise InvalidMinUpdTimeError()
        
        TextHistory.__init__(self, text, maxchanges)
        self.MIN_UPD_TIME = minupdtime
        self.ctrl = ctrl
        self.doinghistory = False
        self.tmrunning = False
        
        self.ctrl.Bind(wx.EVT_TEXT, self._on_text)
    
    def _update_text(self, id_):
        ret = self.current
        shift = 0
        for op in self.stack[id_]:
            if op[0] == 'i':
                self.ctrl.Remove(op[2] + shift, op[3] + shift)
                shift += op[2] - op[3]
            elif op[0] == 'd':
                self.ctrl.SetInsertionPoint(op[2] + shift)
                self.ctrl.WriteText(op[1])
                shift += len(op[1])
            elif op[0] == 'r':
                self.ctrl.Replace(op[2] + shift, op[3] + shift, op[1])
                shift += len(op[1]) - (op[3] - op[2])
            ret = self.ctrl.GetValue()
        
        self.stack[id_] = self._get_changes(ret)
        self.current = ret
        
        return ret

    def _on_text(self, event):
        if not (self.tmrunning or self.doinghistory):
            try:
                self.add(self.ctrl.GetValue())
            except TextUnchangedError:
                pass
            else:
                self.tmrunning = True
                self.htimer = Timer(self.MIN_UPD_TIME, self._reset_timer)
                self.htimer.start()
        event.Skip()
    
    def _reset_timer(self):
        self.tmrunning = False
    
    def _add_ctrl_value(self):
        try:
            self.add(self.ctrl.GetValue())
        except TextUnchangedError:
            pass
    
    def can_undo(self):
        self.doinghistory = True
        self._add_ctrl_value()
        ret = self._can_undo()
        self.doinghistory = False
        return ret
    
    def can_redo(self):
        self.doinghistory = True
        self._add_ctrl_value()
        ret = self._can_redo()
        self.doinghistory = False
        return ret
    
    def undo(self):
        self.doinghistory = True
        self._add_ctrl_value()
        try:
            self._undo()
        except UndoLimitError:
            pass
        self.doinghistory = False
    
    def redo(self):
        self.doinghistory = True
        self._add_ctrl_value()
        try:
            self._redo()
        except RedoLimitError:
            pass
        self.doinghistory = False


class TextHistoryError(Exception):
    pass


class InvalidTextError(TextHistoryError):
    pass


class InvalidMaxChangesError(TextHistoryError):
    pass


class TextUnchangedError(TextHistoryError):
    pass


class UndoLimitError(TextHistoryError):
    pass


class RedoLimitError(TextHistoryError):
    pass


class WxPythonNotFoundError(TextHistoryError):
    pass


class InvalidTextCtrlError(TextHistoryError):
    pass


class ThreadingModNotFoundError(TextHistoryError):
    pass


class InvalidMinUpdTimeError(TextHistoryError):
    pass


class Python2RequiredError(TextHistoryError):
    pass
