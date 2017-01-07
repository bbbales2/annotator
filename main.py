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
import annotate
import neural
import traceback

pygame.init()

import argparse

from rect import Rect

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('video', help = 'Path to video file (preferably .mp4) that contains frames to be annotated')
parser.add_argument('annotationFile', help = 'File that will hold the project annotations')

args = parser.parse_args()

vid = imageio.get_reader(args.video, 'ffmpeg')

#print "Reading in video file..."
#for f in range(F):
#    vid.get_data(f)
#print "Done!"

W, H = vid.get_meta_data()['size']

#print "Loading nn"
#tf.reset_default_graph()

#sess = tf.Session()

#tens = tf.placeholder(tf.float32, shape = [1, H, W, 3])

#net = googlenet.GoogleNet({'data' : tens})

#net.load('googlenet.tf', sess, ignore_missing = True)

#target = [net.layers[name] for name in net.layers if name == 'inception_5b_output'][0]

#print "nn loaded!"

screen = pygame.display.set_mode((W + 200, H))

clock = pygame.time.Clock()
pygame.key.set_repeat(200, 25)
font = pygame.font.SysFont("monospace", 15)

msg = ""

class Global(object):
    def __init__(self, vid = None, screen = None, W = None, H = None):
        if vid:
            self.f = 0
            self.s = 1
            self.step_sizes = [1, 5, 10, 15, 25, 50, 100]
            self.vid = vid
            self.screen = screen
            self.selected = None
            self.F = vid.get_length()
            self.font = font
            self.W = W
            self.H = H

            self.reload()

    def handle(self, event):
        ctrl_pressed = pygame.key.get_mods() & (pygame.KMOD_RCTRL | pygame.KMOD_LCTRL)

        if event.type == pygame.QUIT: sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                if ctrl_pressed:
                    if self.ann.selected:
                        i = bisect.bisect_right(self.ann.selected.fs, self.f)

                        if i != len(self.ann.selected.fs):
                            self.f = self.ann.selected.fs[i]
                        else:
                            self.f = self.F - 1
                    else:
                        self.f = self.F - 1
                else:
                    self.f = min(self.F - 1, (self.f + self.s))

                msg = "Nav right"
            elif event.key == pygame.K_LEFT:
                if ctrl_pressed:
                    if self.ann.selected:
                        i = bisect.bisect_left(self.ann.selected.fs, self.f) - 1

                        if i >= 0 and i < len(self.ann.selected.fs):
                            self.f = self.ann.selected.fs[i]
                        else:
                            self.f = 0
                    else:
                        self.f = 0
                else:
                    self.f = max(0, (self.f - self.s))

                msg = "Nav left"

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
                pickle.dump(self.ann.rects, fh)
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
            elif event.key == pygame.K_F2:
                self.selected = self.nn

                msg = "Neural network seleced!"
                print msg
        try:
            self.selected.handle(event, self)
        except Exception as e:
            traceback.print_exc()

    def draw(self):
        try:
            self.selected.draw(self)
        except Exception as e:
            traceback.print_exc()

    def reload(self):
        try:
            reload(annotate)
            reload(neural)

            if os.path.exists(args.annotationFile):
                with open(args.annotationFile) as fh:
                    rects = pickle.load(fh)
            else:
                rects = []

            self.ann = annotate.Annotator(rects)
            self.nn = neural.Network(sess, target)

            self.selected = self.ann
        except Exception as e:
            raise e
            #traceback.print_exc()
 
g = Global(vid, screen, W, H)

while 1:
    for event in pygame.event.get():
        g.handle(event)

    clock.tick(50)

    screen.fill((0, 0, 0))

    g.draw()

    pygame.display.flip()
