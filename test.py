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

pygame.init()

import annotate
import traceback
import skimage.io
import tensorflow as tf

import argparse

parser = argparse.ArgumentParser(description='Check how the classifier worked')
parser.add_argument('file', help = 'Path to video file with frames to annotate')
parser.add_argument('annotationFile', help = 'File that holds the project annotations')
parser.add_argument('classifiersFile', help = 'File that holds the project classifiers')
parser.add_argument('--fileList', action = 'store_true', help = 'Treat file argument as a text file with newline separated paths to images to be annotated instead of video file')

args = parser.parse_args()

class File(object):
    def __init__(self, path = None, im = None):
        self.path = path
        self.im = im

files = []

if args.fileList:
    # TODO: Need to allow any resolution
    W, H = 1024, 1024

    with open(args.file) as f:
        for line in f:
            line = line.strip()
            
            if len(line) > 0 and os.path.exists(line):
                frame = skimage.io.imread(line)

                frame = numpy.pad(frame, ((0, max(0, 1024 - frame.shape[0])), (0, max(0, 1024 - frame.shape[1]))), mode = 'edge')

                frame = frame[:H, :W]

                files.append(File(line, frame))
else:
    vid = imageio.get_reader(args.file, 'ffmpeg')

    W, H = vid.get_meta_data()['size']

    F = vid.get_length()
    for i, frame in enumerate(vid):
        #if i > 100:
        #    break

        files.append(File('{0}, frame = {1}'.format(args.file, i), frame))

        print "Reading frame {0} / {1}".format(i, F)

# Load up the neural network

print "Loading GoogleNet neural network"

sess = tf.Session()

tens = tf.placeholder(tf.float32, shape = [1, H, W, 3])

net = googlenet.GoogleNet({'data' : tens})

net.load('googlenet.tf', sess, ignore_missing = True)

target = [net.layers[name] for name in net.layers if name == 'pool5_7x7_s1'][0]

test = sess.run(target, feed_dict = { tens : numpy.zeros((1, H, W, 3)) })[0]

print "Neural network loaded"

with open(args.classifiersFile) as f:
    classifiers = pickle.load(f)

screen = pygame.display.set_mode((W + 200, H))

clock = pygame.time.Clock()
pygame.key.set_repeat(200, 25)
font = pygame.font.SysFont("monospace", 15)

msg = ""

labels = classifiers.keys()

class Global(object):
    def __init__(self, files, screen, W, H):
        self.f = 0
        self.s = 1
        self.step_sizes = [1, 5, 10, 15, 25, 50, 100]
        self.files = files
        self.screen = screen
        self.selected = None
        self.F = len(files)
        self.font = font
        self.W = W
        self.H = H
        self.current_label_idx = 0
        
        self.reload()

    def handle(self, event):
        ctrl_pressed = pygame.key.get_mods() & (pygame.KMOD_RCTRL | pygame.KMOD_LCTRL)

        if event.type == pygame.QUIT: sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                if ctrl_pressed:
                    fs = []
                    for marker in self.ann.markers:
                        fs.append(marker.f)

                    fs = sorted(fs)

                    i = bisect.bisect_right(fs, g.f)

                    if i < len(fs):
                        self.f = fs[i]
                    else:
                        self.f = self.F - 1
                else:
                    self.f = min(self.F - 1, (self.f + self.s))

                msg = "Nav right"
            elif event.key == pygame.K_LEFT:
                if ctrl_pressed:
                    fs = []
                    for marker in self.ann.markers:
                        fs.append(marker.f)

                    fs = sorted(fs)

                    i = bisect.bisect_left(fs, g.f) - 1

                    if i >= 0:
                        self.f = fs[i]
                    else:
                        self.f = 0
                else:
                    self.f = max(0, (self.f - self.s))

                msg = "Nav left"

            elif event.key == pygame.K_DOWN:
                self.current_label_idx = min(len(labels) - 1, self.current_label_idx + 1)
            elif event.key == pygame.K_UP:
                pass

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                i = bisect.bisect_right(self.step_sizes, self.s)

                if i < len(self.step_sizes):
                    self.s = self.step_sizes[i]

                msg = "Step size increased"
            elif event.key == pygame.K_MINUS:
                i = bisect.bisect_left(self.step_sizes, self.s) - 1

                if i >= 0:
                    self.s = self.step_sizes[i]
                else:
                    self.s = 1

                msg = "Step size decreased"
            elif event.key == pygame.K_s and ctrl_pressed:
                fh = open(args.annotationFile, 'w')
                pickle.dump(self.ann, fh)
                fh.close()

                msg = "Output written!"
                print msg
            elif event.key == pygame.K_r and ctrl_pressed:
                self.reload()

                msg = "Modules reloaded!"
                print msg
            elif event.key == pygame.K_F1:
                self.selected = self.ann
    
                msg = "Annotator selected!"
                print msg

    def draw(self):
        #try:
            surf = self.selected.draw(self)

            frame = self.files[self.f].im

            if len(frame.shape) == 2:
                frame = (255 * plt.cm.Greys(frame)[:, :, :3]).astype('uint8')

            hist = sess.run(target, feed_dict = { tens : frame.reshape(1, frame.shape[0], frame.shape[1], frame.shape[2]) })[0]

            hist = classifiers[labels[self.current_label_idx]].predict(hist.reshape((-1, 1024))).reshape((self.H / 16, self.W / 16))

            self.signal = hist.copy()

            hist = hist.astype('float')

            hist -= hist.min()
            hist /= hist.max()

            hist = plt.cm.jet(hist)[:, :, :3]
            hist = (hist * 255).astype('uint8')

            hist = numpy.kron(hist, numpy.ones((16, 16, 1)))
        
            nn = pygame.surfarray.make_surface(numpy.rollaxis(hist, 1, 0))
            nn.set_alpha(63)

            self.screen.blit(nn, (0, 0))
            #self.screen.blit(surf, (0, 0))
        #except Exception as e:
        #    traceback.print_exc()

    def reload(self):
        try:
            reload(annotate)

            if os.path.exists(args.annotationFile):
                with open(args.annotationFile) as fh:
                    try:
                        self.ann = pickle.load(fh)
                    except:
                        self.ann = annotate.Annotator()
            else:
                self.ann = annotate.Annotator()

            self.selected = self.ann
        except Exception as e:
            raise e
            #traceback.print_exc()
 
g = Global(files, screen, W, H)

while 1:
    for event in pygame.event.get():
        g.handle(event)

    clock.tick(20)

    screen.fill((0, 0, 0))

    g.draw()

    pygame.display.flip()
