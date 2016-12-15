import sys, pygame
import os
import skimage.io, skimage.transform
import numpy
import bisect
import json
import argparse
import imageio
pygame.init()

import argparse

from rect import Rect

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('video', help = 'Path to video file (preferably .mp4) that contains frames to be annotated')
parser.add_argument('classFile', help = 'File with newline separated list of class names')
parser.add_argument('annotationFile', help = 'File that will hold the project annotations')

args = parser.parse_args()

vid = imageio.get_reader(args.video, 'ffmpeg')

classes = []
with open(args.classFile) as f:
    for line in f:
        line = line.strip()

        if len(line) > 0:
            classes.append(line)

F = vid.get_length()

#print "Reading in video file..."
#for f in range(F):
#    vid.get_data(f)
#print "Done!"

W, H = vid.get_meta_data()['size']

screen = pygame.display.set_mode((W + 200, H))

clock = pygame.time.Clock()
pygame.key.set_repeat(200, 25)
font = pygame.font.SysFont("monospace", 15)

rects = []

selected = None

f = 0

state = None
resize = False
#'creating'
ann = {}

while 1:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()
        if event.type == pygame.MOUSEMOTION:
            if resize == True:
                if selected and selected.keyframe(f):
                    selected.setSecondCorner(f, event.pos)
                else:
                    resize = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if not selected:
                for rect in rects:
                    if rect.contains(f, event.pos):
                        selected = rect
                        break

                if not selected:
                    print "Adding new keyframe"
                    selected = Rect(f, event.pos, (1, 1))

                    rects.append(selected)
                    
                    resize = True
            else:
                if not selected.keyframe(f):
                    print "Adding keyframe to currently selected marker"

                    selected.add(f, event.pos, (1, 1))
                else:
                    print "Moving keyframe in currently selected marker"

                    selected.move(f, event.pos)

                resize = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if resize == True:
                resize = False

            if event.button == 3:
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
                f = min(F - 1, (f + 1))
            elif event.key == pygame.K_LEFT:
                f = max(0, (f - 1))

        if event.type == pygame.KEYUP:
            if event.key in [pygame.K_ESCAPE, pygame.K_RETURN]:
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

                fh = open(outputFile, 'w')
                json.dump(output, fh)
                fh.close()

    clock.tick(50)

    screen.fill((0, 0, 0))

    surf = pygame.surfarray.make_surface(numpy.rollaxis(vid.get_data(f), 1, 0))

    for rect in rects:
        if rect.interpolated(f):
            color = [255, 0, 0]
        else:
            continue

        (x, y), (w, h), keyframe = rect.sample(f)

        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)

        if keyframe:
            color = [0, 255, 0]

        if rect == selected:
            color[2] = 255

        pygame.draw.rect(surf, color, ((x, y), (w, h)), 4)

    screen.blit(surf.convert(), (0, 0))

    #for marker in markers:
    #    (x, y), isRed = marker.sample(f)
    #    dotcolor = None
    #    if marker == selected:
    #        if isRed:
    #            dotcolor = reddot
    #        else:
    #            dotcolor = yellowdot
    #    else:
    #        if isRed:
    #            dotcolor = bluedot
    #        else:
    #            dotcolor = greendot
    #
    #    screen.blit(dotcolor, (x - 10, y - 10))

    label = font.render("Frames: {0} / {1}".format(f, F), 1, (255, 255, 255))

    screen.blit(label, (W, 0))

    pygame.display.flip()
