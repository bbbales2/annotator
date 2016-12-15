import numpy
import bisect

class Rect(object):
    def __init__(self, f, (x, y), (w, h)):
        self.fs = [f]
        self.xs = [x]
        self.ys = [y]
        self.ws = [w]
        self.hs = [h]
        self.resize = False
        self.label = None

    def add(self, f, (x, y), (w, h)):
        i = bisect.bisect_left(self.fs, f)

        if i != len(self.fs) and f == self.fs[i]:
            self.xs[i] = x
            self.ys[i] = y
        else:
            self.fs.insert(i, f)
            self.xs.insert(i, x)
            self.ys.insert(i, y)
            self.ws.insert(i, w)
            self.hs.insert(i, h)

    def keyframe(self, f):
        i = bisect.bisect_left(self.fs, f)

        if i != len(self.fs) and f == self.fs[i]:
            return True

        return False

    def interpolated(self, f):
        if f >= self.fs[0] and f <= self.fs[-1]:
            return True
        else:
            return False

    def contains(self, f, (x, y)):
        if self.interpolated(f):
            (x_, y_), (w, h), keyframe = self.sample(f)

            if (x_ <= x and x <= x_ + w) and (y_ <= y and y <= y_ + h):
                return True

        return False

    def move(self, f, (x, y)):
        i = bisect.bisect_left(self.fs, f)

        if numpy.abs(x - self.xs[i]) < numpy.abs(x - (self.xs[i] + self.ws[i])):
            self.ws[i] = self.ws[i] - (x - self.xs[i])
            self.xs[i] = x
        else:
            self.ws[i] = x - self.xs[i]

        if numpy.abs(y - self.ys[i]) < numpy.abs(y - (self.ys[i] + self.hs[i])):
            self.hs[i] = self.hs[i] - (y - self.ys[i])
            self.ys[i] = y
        else:
            self.hs[i] = y - self.ys[i]

    def setSecondCorner(self, f, (x, y)):
        i = bisect.bisect_left(self.fs, f)

        if numpy.abs(x - self.xs[i]) < numpy.abs(x - (self.xs[i] + self.ws[i])):
            self.ws[i] = self.xs[i] + self.ws[i] - x
            self.xs[i] = x
        else:
            self.ws[i] = x - self.xs[i]

        if numpy.abs(y - self.ys[i]) < numpy.abs(y - (self.ys[i] + self.hs[i])):
            self.hs[i] = self.ys[i] + self.hs[i] - y
            self.ys[i] = y
        else:
            self.hs[i] = y - self.ys[i]

    def delete(self, f):
        i = bisect.bisect_left(self.fs, f)

        if i != len(self.fs) and f == self.fs[i]:
            self.fs.pop(i)
            self.xs.pop(i)
            self.ys.pop(i)
            self.ws.pop(i)
            self.hs.pop(i)

            return True
        else:
            return False

    def sample(self, f):
        x = int(numpy.round(numpy.interp([f], self.fs, self.xs)))
        y = int(numpy.round(numpy.interp([f], self.fs, self.ys)))
        w = int(numpy.round(numpy.interp([f], self.fs, self.ws)))
        h = int(numpy.round(numpy.interp([f], self.fs, self.hs)))

        return (x, y), (w, h), f in self.fs

