import numpy
import bisect

class Circle(object):
    # Args: frane #, x pos, y pos, label, radius of marker
    def __init__(self, f, (x, y), r, label):
        self.f = f
        self.y = y
        self.x = x
        self.label = label
        self.r = r

    def contains(self, f, (x, y)):
        if self.f != f:
            return False

        if numpy.sqrt((self.x - x)**2 + (self.y - y)**2) <= self.r:
            return True
        else:
            return False

    def move(self, (x, y)):
        self.x = x
        self.y = y

class Rect(object):
    KEYFRAME = 1
    INTERPOLATE = 2
    EXTRAPOLATE = 3

    def __init__(self, f, (x, y), (w, h), label):
        self.f = f
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.label = None

    def contains(self, f, (x, y)):
        if self.f == f:
            if (self.x <= x and x <= self.x + self.w) and (self.y <= y and y <= self.y + self.h):
                return True

        return False

    def move(self, (x, y)):
        if numpy.abs(x - self.x) < numpy.abs(x - (self.x + self.w)):
            self.w = self.w - (x - self.x)
            self.x = x
        else:
            self.w = x - self.x

        if numpy.abs(y - self.y) < numpy.abs(y - (self.y + self.h)):
            self.h = self.h - (y - self.y)
            self.y = y
        else:
            self.h = y - self.y

    def setSecondCorner(self, (x, y)):
        if numpy.abs(x - self.x) < numpy.abs(x - (self.x + self.w)):
            self.w = self.x + self.w - x
            self.x = x
        else:
            self.w = x - self.x

        if numpy.abs(y - self.y) < numpy.abs(y - (self.y + self.h)):
            self.h = self.y + self.h - y
            self.y = y
        else:
            self.h = y - self.y
