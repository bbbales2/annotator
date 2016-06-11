import sys, pygame
import os
import skimage.io, skimage.transform
import numpy
import bisect
import json
pygame.init()

size = width, height = 256, 256
speed = [2, 2]
black = 0, 0, 0

screen = pygame.display.set_mode(size)

print "Loading images..."
frames = []
for fname in sorted(os.listdir('images')):
    im = skimage.io.imread('images/{0}'.format(fname), as_grey = True)

    w, h = ((256.0 / max(im.shape)) * numpy.array(im.shape)).astype('int')

    im = skimage.transform.resize(im, (w, h))

    im = ((im / im.max()) * 255.0).astype('uint8')

    im = numpy.array((im, im, im))

    im = numpy.rollaxis(im, 1, 0)
    im = numpy.rollaxis(im, 2, 1)

    frames.append(pygame.surfarray.make_surface(im).convert())
print "Images loaded!"

reddot = pygame.image.load('reddot.png').convert_alpha()
greendot = pygame.image.load('greendot.png').convert_alpha()
yellowdot = pygame.image.load('yellowdot.png').convert_alpha()
bluedot = pygame.image.load('bluedot.png').convert_alpha()

clock = pygame.time.Clock()
pygame.key.set_repeat(200, 50)
font = pygame.font.SysFont("monospace", 15)

markers = []

class Marker(object):
    def __init__(self, f, (x, y)):
        self.fs = [f]
        self.xs = [x]
        self.ys = [y]

    def add(self, f, (x, y)):
        i = bisect.bisect_left(self.fs, f)

        if i != len(self.fs) and f == self.fs[i]:
            self.xs[i] = x
            self.ys[i] = y
        else:
            self.fs.insert(i, f)
            self.xs.insert(i, x)
            self.ys.insert(i, y)

    def delete(self, f):
        i = bisect.bisect_left(self.fs, f)

        if i != len(self.fs) and f == self.fs[i]:
            self.fs.pop(i)
            self.xs.pop(i)
            self.ys.pop(i)

            return True
        else:
            return False

    def sample(self, f):
        x = int(numpy.round(numpy.interp([f], self.fs, self.xs)))
        y = int(numpy.round(numpy.interp([f], self.fs, self.ys)))

        return (x, y), f in self.fs

selected = None

f = 0
while 1:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if selected:
                    if f not in marker.fs:
                        print "Adding keyframe to currently selected marker"
                    else:
                        print "Moving keyframe in currently selected marker"

                    selected.add(f, event.pos)
                else:
                    print "Adding new keyframe"
                    markers.append(Marker(f, event.pos))

                    selected = markers[-1]
            elif event.button == 3:
                dr = None

                x_, y_ = event.pos

                for marker in markers:
                    for i in range(len(marker.fs)):
                        dr_ = numpy.sqrt((marker.xs[i] - x_)**2 + (marker.ys[i] - y_)**2)

                        if dr_ < dr or dr is None:
                            selected = marker
                            dr = dr_
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                f = min(len(frames) - 1, (f + 1))
            elif event.key == pygame.K_LEFT:
                f = max(0, (f - 1))

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_ESCAPE:
                selected = None
            elif event.key == pygame.K_d:
                if selected:
                    if selected.delete(f):
                        print "Removing keyframe from selected marker"
                    else:
                        print "No keyframes at current frame! (only yellow selections can be deleted -- not blues)"

                    if len(selected.fs) == 0:
                        markers.remove(selected)
                        selected = None

                        print "No keyframes left in marker... Removing marker"
                else:
                    print "No marker selected!"
            elif event.key == pygame.K_w:
                print "Output written!"
                output = []
                for f_ in range(len(frames)):
                    outputT = []
                    for marker in markers:
                        outputT.append(marker.sample(f_)[0])
                    output.append(outputT)

                fh = open('output.txt', 'w')
                json.dump(output, fh)
                fh.close()

    clock.tick(50)

    screen.fill(black)
    screen.blit(frames[f], (0, 0))

    for marker in markers:
        (x, y), isRed = marker.sample(f)
        dotcolor = None
        if marker == selected:
            if isRed:
                dotcolor = reddot
            else:
                dotcolor = yellowdot
        else:
            if isRed:
                dotcolor = bluedot
            else:
                dotcolor = greendot

        screen.blit(dotcolor, (x - 10, y - 10))

    label = font.render("{0} / {1}".format(f, len(frames)), 1, (255, 255, 255))

    screen.blit(label, (0, 240))

    pygame.display.flip()
