#!/usr/bin/ipy

import clr

clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
clr.AddReference("System")

from System.Windows.Forms import Application, Form, FormBorderStyle
from System.Windows.Forms import UserControl, Keys, Timer, StatusBar
from System.Drawing import Size, Color, SolidBrush, Pen
from System.Drawing.Drawing2D import LineCap
from System.ComponentModel import Container
from System import Random

class Tetrominoes(object):
    NoShape = 0
    ZShape = 1
    SShape = 2
    LineShape = 3
    TShape = 4
    SquareShape = 5
    LShape = 6
    MirroredLShape = 7

class Board(UserControl):
    BoardWidth = 10
    BoardHeight = 22
    Speed = 200
    ID_TIMER = 1

    def __init__(self):
        self.Text = 'Snake'

        self.components = Container()
        self.isWaitingAfterLine = False
        self.curPiece = Shape()
        self.nextPiece = Shape()
        self.curX = 0
        self.curY = 0
        self.numLinesRemoved = 0
        self.board = []

        self.DoubleBuffered = True

        self.isStarted = False
        self.isPaused = False

        self.timer = Timer(self.components)
        self.timer.Enabled = True
        self.timer.Interval = Board.Speed
        self.timer.Tick += self.OnTick

        self.Paint += self.OnPaint
        self.KeyUp += self.OnKeyUp

        self.ClearBoard()

    def ShapeAt(self, x, y):
        return self.board[(y * Board.BoardWidth) + x]

    def SetShapeAt(self, x, y, shape):
        self.board[(y * Board.BoardWidth) + x] = shape

    def SquareWidth(self):
        return self.ClientSize.Width / Board.BoardWidth

    def SquareHeight(self):
        return self.ClientSize.Height / Board.BoardHeight

    def Start(self):
        if self.isPaused:
            return

        self.isStarted = True
        self.isWaitingAfterLine = False
        self.numLinesRemoved = 0
        self.ClearBoard()

        self.NewPiece()

    def Pause(self):
        if not self.isStarted:
            return

        self.isPaused = not self.isPaused        
        statusbar = self.Parent.statusbar

        if self.isPaused:
            self.timer.Stop()
            statusbar.Text = 'paused'
        else:
            self.timer.Start()
            statusbar.Text = str(self.numLinesRemoved)

        self.Refresh()

    def ClearBoard(self):
        for i in range(Board.BoardHeight * Board.BoardWidth):
            self.board.append(Tetrominoes.NoShape)

    def OnPaint(self, event):

        g = event.Graphics

        size = self.ClientSize
        boardTop = size.Height - Board.BoardHeight * self.SquareHeight()

        for i in range(Board.BoardHeight):
            for j in range(Board.BoardWidth):
                shape = self.ShapeAt(j, Board.BoardHeight - i - 1)
                if shape != Tetrominoes.NoShape:
                    self.DrawSquare(g,
                        0 + j * self.SquareWidth(),
                        boardTop + i * self.SquareHeight(), shape)

        if self.curPiece.GetShape() != Tetrominoes.NoShape:
            for i in range(4):
                x = self.curX + self.curPiece.x(i)
                y = self.curY - self.curPiece.y(i)
                self.DrawSquare(g, 0 + x * self.SquareWidth(),
                    boardTop + (Board.BoardHeight - y - 1) * self.SquareHeight(),
                    self.curPiece.GetShape())

        g.Dispose()

    def OnKeyUp(self, event): 

        if not self.isStarted or self.curPiece.GetShape() == Tetrominoes.NoShape:
            return

        key = event.KeyCode

        if key == Keys.P:
            self.Pause()
            return

        if self.isPaused:
            return    
        elif key == Keys.Left:
            self.TryMove(self.curPiece, self.curX - 1, self.curY)
        elif key == Keys.Right:
            self.TryMove(self.curPiece, self.curX + 1, self.curY)
        elif key == Keys.Down:
            self.TryMove(self.curPiece.RotatedRight(), self.curX, self.curY)
        elif key == Keys.Up:
            self.TryMove(self.curPiece.RotatedLeft(), self.curX, self.curY)
        elif key == Keys.Space:
            self.DropDown()
        elif key == Keys.D:
            self.OneLineDown()

    def OnTick(self, sender, event):

        if self.isWaitingAfterLine:
            self.isWaitingAfterLine = False
            self.NewPiece()
        else:
            self.OneLineDown()

    def DropDown(self):
        newY = self.curY
        while newY > 0:
            if not self.TryMove(self.curPiece, self.curX, newY - 1):
                break
            newY -= 1

        self.PieceDropped()

    def OneLineDown(self):
        if not self.TryMove(self.curPiece, self.curX, self.curY - 1):
            self.PieceDropped()

    def PieceDropped(self):
        for i in range(4):
            x = self.curX + self.curPiece.x(i)
            y = self.curY - self.curPiece.y(i)
            self.SetShapeAt(x, y, self.curPiece.GetShape())

        self.RemoveFullLines()

        if not self.isWaitingAfterLine:
            self.NewPiece()

    def RemoveFullLines(self):
        numFullLines = 0

        statusbar = self.Parent.statusbar

        rowsToRemove = []

        for i in range(Board.BoardHeight):
            n = 0
            for j in range(Board.BoardWidth):
                if not self.ShapeAt(j, i) == Tetrominoes.NoShape:
                    n = n + 1

            if n == 10:
                rowsToRemove.append(i)

        rowsToRemove.reverse()

        for m in rowsToRemove:
            for k in range(m, Board.BoardHeight):
                for l in range(Board.BoardWidth):
                    self.SetShapeAt(l, k, self.ShapeAt(l, k + 1))

        numFullLines = numFullLines + len(rowsToRemove)

        if numFullLines > 0:
            self.numLinesRemoved = self.numLinesRemoved + numFullLines
            statusbar.Text = str(self.numLinesRemoved)
            self.isWaitingAfterLine = True
            self.curPiece.SetShape(Tetrominoes.NoShape)
            self.Refresh()

    def NewPiece(self):
        self.curPiece = self.nextPiece
        statusbar = self.Parent.statusbar
        self.nextPiece.SetRandomShape()
        self.curX = Board.BoardWidth / 2 + 1
        self.curY = Board.BoardHeight - 1 + self.curPiece.MinY()

        if not self.TryMove(self.curPiece, self.curX, self.curY):
            self.curPiece.SetShape(Tetrominoes.NoShape)
            self.timer.Stop()
            self.isStarted = False
            statusbar.Text = 'Game over'

    def TryMove(self, newPiece, newX, newY):
        for i in range(4):
            x = newX + newPiece.x(i)
            y = newY - newPiece.y(i)
            if x < 0 or x >= Board.BoardWidth or y < 0 or y >= Board.BoardHeight:
                return False
            if self.ShapeAt(x, y) != Tetrominoes.NoShape:
                return False

        self.curPiece = newPiece
        self.curX = newX
        self.curY = newY
        self.Refresh()
        return True

    def DrawSquare(self, g, x, y, shape):
        colors = [ (0, 0, 0), (204, 102, 102), 
            (102, 204, 102), (102, 102, 204), 
            (204, 204, 102), (204, 102, 204), 
            (102, 204, 204), (218, 170, 0) ]

        light = [ (0, 0, 0), (248, 159, 171), 
            (121, 252, 121), (121, 121, 252), 
            (252, 252, 121), (252, 121, 252), 
            (121, 252, 252), (252, 198, 0) ]

        dark = [ (0, 0, 0), (128, 59, 59), 
            (59, 128, 59), (59, 59, 128), 
            (128, 128, 59), (128, 59, 128), 
            (59, 128, 128), (128, 98, 0) ]   

        pen = Pen(Color.FromArgb(light[shape][0], light[shape][1],
            light[shape][2]), 1)
        pen.StartCap = LineCap.Flat
        pen.EndCap = LineCap.Flat

        g.DrawLine(pen, x, y + self.SquareHeight() - 1, x, y)
        g.DrawLine(pen, x, y, x + self.SquareWidth() - 1, y)

        darkpen = Pen(Color.FromArgb(dark[shape][0], dark[shape][1],
            dark[shape][2]), 1)
        darkpen.StartCap = LineCap.Flat
        darkpen.EndCap = LineCap.Flat

        g.DrawLine(darkpen, x + 1, y + self.SquareHeight() - 1,
            x + self.SquareWidth() - 1, y + self.SquareHeight() - 1)
        g.DrawLine(darkpen, x + self.SquareWidth() - 1, 
            y + self.SquareHeight() - 1, x + self.SquareWidth() - 1, y + 1)

        g.FillRectangle(SolidBrush(Color.FromArgb(colors[shape][0], colors[shape][1], 
            colors[shape][2])), x + 1, y + 1, self.SquareWidth() - 1, 
            self.SquareHeight() - 2)

        pen.Dispose()
        darkpen.Dispose()

class Shape(object):
    coordsTable = (
        ((0, 0),     (0, 0),     (0, 0),     (0, 0)),
        ((0, -1),    (0, 0),     (-1, 0),    (-1, 1)),
        ((0, -1),    (0, 0),     (1, 0),     (1, 1)),
        ((0, -1),    (0, 0),     (0, 1),     (0, 2)),
        ((-1, 0),    (0, 0),     (1, 0),     (0, 1)),
        ((0, 0),     (1, 0),     (0, 1),     (1, 1)),
        ((-1, -1),   (0, -1),    (0, 0),     (0, 1)),
        ((1, -1),    (0, -1),    (0, 0),     (0, 1))
    )

    def __init__(self):
        self.coords = [[0,0] for i in range(4)]
        self.pieceShape = Tetrominoes.NoShape

        self.SetShape(Tetrominoes.NoShape)

    def GetShape(self):
        return self.pieceShape

    def SetShape(self, shape):
        table = Shape.coordsTable[shape]
        for i in range(4):
            for j in range(2):
                self.coords[i][j] = table[i][j]

        self.pieceShape = shape

    def SetRandomShape(self):
        rand = Random()
        self.SetShape(rand.Next(1, 7))

    def x(self, index):
        return self.coords[index][0]

    def y(self, index):
        return self.coords[index][1]

    def SetX(self, index, x):
        self.coords[index][0] = x

    def SetY(self, index, y):
        self.coords[index][1] = y

    def MaxX(self):
        m = self.coords[0][0]
        for i in range(4):
            m = max(m, self.coords[i][0])

        return m

    def MinY(self):
        m = self.coords[0][1]
        for i in range(4):
            m = min(m, self.coords[i][1])

        return m

    def RotatedLeft(self):
        if self.pieceShape == Tetrominoes.SquareShape:
            return self

        result = Shape()
        result.pieceShape = self.pieceShape
        for i in range(4):
            result.SetX(i, self.y(i))
            result.SetY(i, -self.x(i))

        return result

    def RotatedRight(self):
        if self.pieceShape == Tetrominoes.SquareShape:
            return self

        result = Shape()
        result.pieceShape = self.pieceShape
        for i in range(4):
            result.SetX(i, -self.y(i))
            result.SetY(i, self.x(i))

        return result   

class IForm(Form):

    def __init__(self):
        self.Text = 'Tetris'
        self.Width = 200
        self.Height = 430
        self.FormBorderStyle = FormBorderStyle.FixedSingle
        board = Board()
        board.Width = 195
        board.Height = 380
        self.Controls.Add(board)

        self.statusbar = StatusBar()
        self.statusbar.Parent = self
        self.statusbar.Text = 'Ready'
        board.Start()
        self.CenterToScreen()

Application.Run(IForm())
