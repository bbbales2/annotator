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
import matplotlib.pyplot as plt

pygame.init()

import annotate
import traceback
import skimage.io

import argparse

from rect import Rect

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('fileList', help = 'Path to text file with newline separated paths to images to be annotated')
parser.add_argument('annotationFile', help = 'File that will hold the project annotations')

args = parser.parse_args()

class File(object):
    def __init__(self, path = None, im = None):
        self.path = path
        self.im = im

files = []
with open(args.fileList) as f:
    for line in f:
        line = line.strip()

        if len(line) > 0 and os.path.exists(line):
            files.append(File(line, skimage.io.imread(line)))

W, H = 1024, 1024

screen = pygame.display.set_mode((W + 200, H))

clock = pygame.time.Clock()
pygame.key.set_repeat(200, 25)
font = pygame.font.SysFont("monospace", 15)

msg = ""

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
        try:
            self.selected.handle(event, self)
        except Exception as e:
            traceback.print_exc()

    def draw(self):
        #try:
            surf = self.selected.draw(self)

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
