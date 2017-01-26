import pygame
from rect import Rect
import numpy
import re
import collections
import os
import matplotlib.pyplot as plt
import itertools

def defaultGeom():
    return [1, 1]
    
def defaultLabel():
    return None

tfont = pygame.font.SysFont("monospace", 15)
lfont = pygame.font.Font(pygame.font.match_font('monospace', bold = True), 15)

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

class Annotator(object):
    def __init__(self):
        self.selected = None
        self.msg = ""
        self.markers = []
        self.resize = False
        self.mode = 'circle'

    def handle(self, event, g):
        ctrl_pressed = pygame.key.get_mods() & (pygame.KMOD_RCTRL | pygame.KMOD_LCTRL)

        if event.type == pygame.MOUSEMOTION:
            if self.resize == True and type(self.selected) == Rect:
                if self.selected and self.selected.f == g.f:
                    self.selected.setSecondCorner(event.pos)
                else:
                    self.resize = False

                    self.msg = "Done resizing"
                    print self.msg

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 or event.button == 3:
                x = event.pos[0]
                y = event.pos[1]

                did_selection = False
                if event.button == 1:
                    for obj in self.markers:
                        if (type(obj) == Circle and self.mode == "circle") or (type(obj) == Rect and self.mode == "rectangle"):
                            if obj.contains(g.f, (x, y)):
                                did_selection = True
                                
                                self.selected = obj
                                
                                self.msg = "Selecting marker"
                                print self.msg
                                
                                break

                if not did_selection:
                    if self.selected and self.selected.f == g.f and event.button == 1:
                        self.msg = "Moving element"

                        self.selected.move((x, y))

                        if type(self.selected) == Rect:
                            self.msg = "Resizing rect"

                            self.resize = True

                        print self.msg
                    else:
                        self.msg = "Adding element"
                        print self.msg

                        # copy from selected marker
                        if self.mode == 'circle':
                            if self.selected:
                                label = self.selected.label
                            else:
                                label = None
                                
                            if self.selected and type(self.selected) == Circle:
                                r = self.selected.r
                            else:
                                r = 20
                                
                            self.selected = Circle(g.f, (x, y), r, label)

                            self.markers.append(self.selected)
                        else:
                            if self.selected:
                                label = self.selected.label
                            else:
                                label = None

                            w = 1
                            h = 1
                    
                            self.selected = Rect(g.f, (x, y), (w, h), label)

                            self.markers.append(self.selected)
                    
                            self.resize = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.resize == True:
                self.resize = False

                self.msg = "Done resizing"

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                if self.selected and type(self.selected) == Circle:
                    self.selected.r = min(200, self.selected.r + 2)
                    self.msg = "Grow marker"
                    print self.msg
            elif event.button == 5:
                if self.selected and type(self.selected) == Circle:
                    self.selected.r = max(10, self.selected.r - 2)
                    self.msg = "Shrink marker"
                    print self.msg

        if event.type == pygame.KEYUP:
            if ctrl_pressed:
                if event.key == pygame.K_1:
                    self.mode = "circle"

                    self.msg = "Switched to circles"
                    print self.msg
                elif event.key == pygame.K_2:
                    self.mode = "rectangle"

                    self.msg = "Switched to rectangles"
                    print self.msg

                self.selected = None
                
        if event.type == pygame.KEYDOWN:
            if self.selected and not ctrl_pressed:
                if event.key == pygame.K_BACKSPACE:
                    if len(self.selected.label) > 0:
                        self.selected.label = self.selected.label[:-1]

                    self.msg = "Modifying label (del)"
                elif re.match("[A-Za-z]", event.unicode):
                    if self.selected.label == None:
                        self.selected.label = str(event.unicode)
                    else:
                        self.selected.label += str(event.unicode)

                    self.msg = "Modifying label ({0})".format(event.unicode)
                
            if event.key in [pygame.K_ESCAPE, pygame.K_RETURN]:
                self.selected = None
            elif event.key == pygame.K_DELETE:
                if self.selected:
                    self.markers.remove(self.selected)

                    self.selected = None

                    self.msg = "Removing label"
                    print "Removing label"
                else:
                    self.msg = "No marker selected!"
                    print self.msg

    def draw(self, g):
        fname = g.files[g.f].path
        frame = (255 * plt.cm.Greys(g.files[g.f].im)[:, :, :3]).astype('uint8')

        surf = pygame.surfarray.make_surface(numpy.rollaxis(frame, 1, 0)).convert_alpha()

        pygame.display.set_caption("{0} add mode, {1}".format(self.mode, fname))

        for marker in self.markers:
            if marker.f != g.f:
                continue

            if marker.label != None:
                lsize = lfont.size(marker.label)
                rlabel = lfont.render(marker.label, 1, (255, 0, 100))
            else:
                lsize = lfont.size("no label")
                rlabel = lfont.render("no label", 1, (255, 0, 255))

            if marker == self.selected:
                color = [255, 0, 0]
            else:
                color = [200, 100, 0]

            if type(marker) == Circle:
                pygame.draw.circle(surf, color, (marker.x, marker.y), marker.r, 3)

                lx = marker.x - lsize[0] / 2
                ly = marker.y - marker.r - lsize[1]
            else:
                pygame.draw.rect(surf, color, ((marker.x, marker.y), (marker.w, marker.h)), 3)

                lx = marker.x + marker.w / 2 - lsize[0] / 2
                ly = marker.y - lsize[1]

            tbackground = pygame.Surface((lsize[0] + 4, lsize[1]))
            tbackground.set_alpha(128)
            tbackground.fill((0, 0, 0))

            #g.screen.blit(tbackground, (lx, ly))

            surf.blit(tbackground, (lx - 2, ly))
            surf.blit(rlabel, (lx, ly))

        g.screen.blit(surf.convert(), (0, 0))

        lines = []
        lines.append("Frame jump: {0}".format(g.s))
        lines.append("Frames: {0} / {1}".format(g.f, g.F))
        lines.append("")

        lines.append("Labels: ")
        count = collections.Counter()
        for marker in self.markers:
            count[marker.label] += 1

        for label in count:
            lines.append("{0} : {1}".format(label, count[label]))
            
        if self.selected:
            lines.append("")
            lines.append("Type a-z to label")
            lines.append("Del deletes marker")
            lines.append("Click to move marker")
            lines.append("Right-Click to add marker")
            lines.append("Scroll mouse to resize marker")
            lines.append("Escape to unselect")

        lines.append("")
        lines.append("Ctrl-s saves")
        lines.append("Arrows change frame")
        lines.append("+, - adjust frame step")
        lines.append("Ctrl-arrows fast jump")
        lines.append("Ctrl-1 switches to circles")
        lines.append("Ctrl-2 switches to rectangles")

        lines.append("")
        lines.append(self.msg)

        for i, line in enumerate(lines):
            label = tfont.render(line, 1, (255, 255, 255))
            g.screen.blit(label, (g.W, 15 * i))

