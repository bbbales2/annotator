import sys, pygame
import os
import re
#import skimage.io, skimage.transform
import numpy
import bisect
import json
import argparse
import imageio
import pickle
import googlenet
import matplotlib.pyplot as plt
import tensorflow as tf
import sklearn.linear_model

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

print "Loading nn"
tf.reset_default_graph()

sess = tf.Session()

tens = tf.placeholder(tf.float32, shape = [1, H, W, 3])

net = googlenet.GoogleNet({'data' : tens})

net.load('googlenet.tf', sess, ignore_missing = True)

target = [net.layers[name] for name in net.layers if name == 'inception_5b_output'][0]
lgr = None

print "nn loaded!"

screen = pygame.display.set_mode((W + 200, H))

clock = pygame.time.Clock()
pygame.key.set_repeat(200, 25)
font = pygame.font.SysFont("monospace", 15)

if os.path.exists(args.annotationFile):
    with open(args.annotationFile) as fh:
        rects = pickle.load(fh)
else:
    rects = []

selected = None

f = 0

state = None
resize = False
labeling = False

s = 1
step_sizes = [1, 5, 10, 15, 25, 50, 100]

msg = ""

while 1:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()
        if event.type == pygame.MOUSEMOTION:
            if resize == True:
                if selected and selected.keyframe(f):
                    selected.setSecondCorner(f, event.pos)
                else:
                    resize = False

                    msg = "Done resizing"

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if not selected:
                for rect in rects:
                    if rect.contains(f, event.pos):
                        selected = rect

                        if selected.label:
                            msg = "{0} selected".format(selected.label)
                        else:
                            msg = "Selected keyframe"
                        break

                if not selected:
                    msg = "Adding keyframe"

                    print "Adding new keyframe"

                    selected = Rect(f, event.pos, (1, 1))

                    rects.append(selected)
                    
                    resize = True
            else:
                if not selected.keyframe(f):
                    msg = "Adding keyframe"

                    print "Adding keyframe to currently selected marker"

                    selected.add(f, event.pos, (1, 1))
                else:
                    msg = "Resizing keyframe"

                    print "Moving keyframe in currently selected marker"

                    selected.move(f, event.pos)

                resize = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if resize == True:
                resize = False

                msg = "Done resizing"
            
        if event.type == pygame.KEYDOWN:
            if selected and not (pygame.key.get_mods() & (pygame.KMOD_RCTRL | pygame.KMOD_LCTRL)):
                if event.key == pygame.K_BACKSPACE:
                    if selected.label > 0:
                        selected.label = selected.label[:-1]

                    msg = "Modifying label (del)"
                elif re.match("[A-Za-z]", event.unicode):
                    if selected.label == None:
                        selected.label = str(event.unicode)
                    else:
                        selected.label += str(event.unicode)

                    msg = "Modifying label ({0})".format(event.unicode)

            if event.key == pygame.K_RIGHT:
                if pygame.key.get_mods() & (pygame.KMOD_RCTRL | pygame.KMOD_LCTRL):
                    if selected:
                        i = bisect.bisect_right(selected.fs, f)

                        if i != len(selected.fs):
                            f = selected.fs[i]
                        else:
                            f = F - 1
                    else:
                        f = F - 1
                else:
                    f = min(F - 1, (f + s))

                msg = "Nav right"
            elif event.key == pygame.K_LEFT:
                if pygame.key.get_mods() & (pygame.KMOD_RCTRL | pygame.KMOD_LCTRL):
                    if selected:
                        i = bisect.bisect_left(selected.fs, f) - 1

                        if i >= 0 and i < len(selected.fs):
                            f = selected.fs[i]
                        else:
                            f = 0
                    else:
                        f = 0
                else:
                    f = max(0, (f - s))

                msg = "Nav left"

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                i = bisect.bisect_right(step_sizes, s)

                if i < len(step_sizes):
                    s = step_sizes[i]

                msg = "Step size increased"
            elif event.key == pygame.K_MINUS:
                i = bisect.bisect_left(step_sizes, s) - 1

                if i >= 0:
                    s = step_sizes[i]
                else:
                    s = 1

                msg = "Step size decreased"
            elif event.key in [pygame.K_ESCAPE, pygame.K_RETURN]:
                selected = None
            elif event.key == pygame.K_DELETE:
                if selected:
                    if selected.delete(f):
                        msg = "Removing keyframe"
                        print "Removing keyframe from selected marker"
                    else:
                        msg = "No keyframe in frame"
                        print "No keyframes at current frame! (only yellow selections can be deleted -- not blues)"

                    if len(selected.fs) == 0:
                        rects.remove(selected)
                        selected = None

                        msg = "Removing marker"
                        print "No keyframes left in marker... Removing marker"
                else:
                    msg = "No marker selected!"
                    print msg
            elif event.key == pygame.K_s and pygame.key.get_mods() & (pygame.KMOD_RCTRL | pygame.KMOD_LCTRL):
                fh = open(args.annotationFile, 'w')
                pickle.dump(rects, fh)
                fh.close()

                msg = "Output written!"
                print msg
            elif event.key == pygame.K_t and pygame.key.get_mods() & (pygame.KMOD_RCTRL | pygame.KMOD_LCTRL):

                msg = "Training network..."
                print msg

                classes = {}

                Xs = []
                Ys = []

                for rect in rects:
                    if rect.label not in classes:
                        classes[rect.label] = len(classes)

                    for f_ in rect.fs:
                        im = vid.get_data(f_)
                        
                        feats = sess.run(target, feed_dict = { tens : im.reshape(1, im.shape[0], im.shape[1], im.shape[2]) })[0]

                        (x, y), (w, h), keyframe = rect.sample(f_)

                        if keyframe:
                            i = int(y + h / 2) / 16
                            j = int(x + w / 2) / 16

                            Xs.append(feats[i, j])
                            Ys.append(classes[rect.label])

                        #for i in range(H / 16):
                        #    for j in range(W / 16):
                        #        if rect.contains(f_, (j * 16 + 8, i * 16 + 8)):
                        #            Xs.append(feats[i, j])
                        #            Ys.append(classes[rect.label])

                lgr = sklearn.linear_model.LogisticRegression()

                lgr.fit(Xs, Ys)

                msg = "Network trained!"
                print msg

    clock.tick(50)

    screen.fill((0, 0, 0))

    frame = vid.get_data(f)

    surf = pygame.surfarray.make_surface(numpy.rollaxis(frame, 1, 0))

    if lgr and selected and selected.label in classes:
        hist = sess.run(target, feed_dict = { tens : frame.reshape(1, frame.shape[0], frame.shape[1], frame.shape[2]) })[0]#numpy.linalg.norm(, axis = 2)

        hist = lgr.predict_log_proba(hist.reshape((-1, 1024))).reshape((H / 16, W / 16, -1))

        hist = numpy.argmax(hist, axis = 2).astype('float')#hist[:, :, classes[selected.label]]

        hist -= hist.min()
        hist /= hist.max()
        hist = plt.cm.jet(hist)[:, :, :3]
        hist = (hist * 255).astype('uint8')
        
        hist = numpy.kron(hist, numpy.ones((16, 16, 1)))
        
        nn = pygame.surfarray.make_surface(numpy.rollaxis(hist, 1, 0))
        nn.set_alpha(63)
        
        surf.blit(nn, (0, 0))

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

        if rect.label != None:
            label = font.render(rect.label, 1, (255, 255, 255))
        else:
            label = font.render("no label", 1, (255, 0, 255))

        pygame.draw.rect(surf, color, ((x, y), (w, h)), 4)
        surf.blit(label, (x, y - 15))

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

    lines = []
    lines.append("Frame jump: {0}".format(s))
    lines.append("Frames: {0} / {1}".format(f, F))
    lines.append("")

    if selected:
        lines.append("Keyframes: ")
        for f_ in selected.fs:
            lines.append("{0}".format(f_))

        lines.append("")
        lines.append("Type a-z to label")
        lines.append("Del deletes keyframe")
        lines.append("Click to move keyframe")
        lines.append("Escape to unselect")

    lines.append("")
    lines.append("Ctrl-s saves")
    lines.append("Arrows change frame")
    lines.append("+/- adjust frame step")
    lines.append("Ctrl-arrows fast jump")

    lines.append("")
    lines.append(msg)

    for i, line in enumerate(lines):
        label = font.render(line, 1, (255, 255, 255))
        screen.blit(label, (W, 15 * i))

    pygame.display.flip()
