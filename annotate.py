import pygame
from rect import Rect
import numpy
import re
import collections

def defaultGeom():
    return [1, 1]
    
def defaultLabel():
    return None

class Annotator(object):
    def __init__(self):
        self.selected = None
        self.msg = ""
        self.b = 16
        self.geoms = collections.defaultdict(defaultGeom)
        self.labels = collections.defaultdict(defaultLabel) #1D, keyed by (frame, (i / b, j / b)), value is label

    def handle(self, event, g):
        ctrl_pressed = pygame.key.get_mods() & (pygame.KMOD_RCTRL | pygame.KMOD_LCTRL)

        if event.type == pygame.MOUSEBUTTONUP:
            bx = event.pos[0] / self.b
            by = event.pos[1] / self.b

            key = (g.f, (bx, by))

            if key in self.labels:
                self.msg = "Selecting element"
                print self.msg

                self.selected = key
            else:
                if self.selected and self.selected[0] == g.f:
                    self.msg = "Moving element"
                    print self.msg

                    self.labels[key] = self.labels[self.selected]
                    del self.labels[self.selected]
                else:
                    self.msg = "Adding element"
                    print self.msg
                    
                    if self.selected:
                        self.labels[key] = self.labels[self.selected]
                    else:
                        self.labels[key] = None

                self.selected = key
            
        if event.type == pygame.KEYDOWN:
            if self.selected and not ctrl_pressed:
                if event.key == pygame.K_BACKSPACE:
                    if len(self.labels[self.selected]) > 0:
                        self.labels[self.selected] = self.labels[self.selected][:-1]

                    self.msg = "Modifying label (del)"
                elif re.match("[A-Za-z]", event.unicode):
                    if self.labels[self.selected] == None:
                        self.labels[self.selected] = str(event.unicode)
                    else:
                        self.labels[self.selected] += str(event.unicode)

                    self.msg = "Modifying label ({0})".format(event.unicode)
                elif event.key == pygame.K_RIGHTBRACKET:
                    self.geoms[self.labels[self.selected]][0] += 1
                elif event.key == pygame.K_LEFTBRACKET:
                    self.geoms[self.labels[self.selected]][0] = max(1, self.geoms[self.labels[self.selected]][0] - 1)
                elif event.key == pygame.K_QUOTE:
                    self.geoms[self.labels[self.selected]][1] += 1
                elif event.key == pygame.K_SEMICOLON:
                    self.geoms[self.labels[self.selected]][1] = max(1, self.geoms[self.labels[self.selected]][1] - 1)
                
            if event.key in [pygame.K_ESCAPE, pygame.K_RETURN]:
                self.selected = None
            elif event.key == pygame.K_DELETE:
                if self.selected:
                    del self.labels[self.selected]
                    self.selected = None
                    self.msg = "Removing label"
                    print "Removing label"
                else:
                    self.msg = "No marker selected!"
                    print self.msg

    def draw(self, g):
        frame = g.vid.get_data(g.f)

        surf = pygame.surfarray.make_surface(numpy.rollaxis(frame, 1, 0))

        for (f, loc), label in self.labels.iteritems():
            if f != g.f:
                continue

            if label != None:
                lsize = g.font.size(label)
                rlabel = g.font.render(label, 1, (255, 255, 255))
            else:
                lsize = g.font.size("no label")
                rlabel = g.font.render("no label", 1, (255, 0, 255))

            lx, ly = loc

            lxo = (self.geoms[label][0] - 1) / 2
            lyo = (self.geoms[label][1] - 1) / 2

            li, lj = ly - lyo, lx - lxo

            ri = li + self.geoms[label][1]
            rj = lj + self.geoms[label][0]

            if (f, loc) == self.selected:
                color = [0, 255, 255]
            else:
                color = [255, 255, 255]

            for xx in [lj * self.b, rj * self.b]:#range(lj * self.b, rj * self.b + 1, self.b):
                pygame.draw.line(surf, color, (xx, li * self.b), (xx, ri * self.b), 1)

            for yy in [li * self.b, ri * self.b]:#range(li * self.b, ri * self.b + 1, self.b):
                pygame.draw.line(surf, color, (lj * self.b, yy), (rj * self.b, yy), 1)

            pygame.draw.rect(surf, color, ((lx * self.b, ly * self.b), (self.b, self.b)), 2)
            surf.blit(rlabel, (lx * self.b - lsize[0] / 2 + self.b / 2, li * self.b - lsize[1]))

        g.screen.blit(surf.convert(), (0, 0))

        lines = []
        lines.append("Frame jump: {0}".format(g.s))
        lines.append("Frames: {0} / {1}".format(g.f, g.F))
        lines.append("")

        lines.append("Labels: ")
        count = collections.Counter()
        for label in self.labels.values():
            count[label] += 1

        for label in count:
            lines.append("{0} : {1}".format(label, count[label]))
            
        if self.selected:
            lines.append("")
            lines.append("Type a-z to label")
            lines.append("Del deletes keyframe")
            lines.append("Click to move keyframe")
            lines.append("Escape to unselect")

        lines.append("")
        lines.append("Ctrl-s saves")
        lines.append("Arrows change frame")
        lines.append("[, ] shrink/grow x-geom")
        lines.append(";,' shrink/grow y-geom")
        lines.append("+, - adjust frame step")
        lines.append("Ctrl-arrows fast jump")

        lines.append("")
        lines.append(self.msg)

        for i, line in enumerate(lines):
            label = g.font.render(line, 1, (255, 255, 255))
            g.screen.blit(label, (g.W, 15 * i))
