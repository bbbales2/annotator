import pygame
from rect import Rect
import numpy
import re

class Annotator(object):
    def __init__(self, rects = None):
        if not rects:
            self.rects = []
        else:
            self.rects = rects

        self.resize = False
        self.selected = False
        self.msg = ""

    def handle(self, event, g):
        ctrl_pressed = pygame.key.get_mods() & (pygame.KMOD_RCTRL | pygame.KMOD_LCTRL)

        if event.type == pygame.MOUSEMOTION:

            if self.resize == True:
                if self.selected and self.selected.keyframe(g.f):
                    self.selected.setSecondCorner(g.f, event.pos)
                else:
                    self.resize = False

                    self.msg = "Done resizing"

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if not self.selected:
                for rect in self.rects:
                    if rect.contains(g.f, event.pos):
                        self.selected = rect

                        if self.selected.label:
                            self.msg = "{0} selected".format(self.selected.label)
                        else:
                            self.msg = "Selected keyframe"
                        break

                if not self.selected:
                    self.msg = "Adding keyframe"

                    print "Adding new keyframe"

                    self.selected = Rect(g.f, event.pos, (1, 1))

                    self.rects.append(self.selected)
                    
                    self.resize = True
            else:
                if not self.selected.keyframe(g.f):
                    self.msg = "Adding keyframe"

                    print "Adding keyframe to currently selected marker"

                    self.selected.add(g.f, event.pos, (1, 1))
                else:
                    self.msg = "Resizing keyframe"

                    print "Moving keyframe in currently selected marker"

                    self.selected.move(g.f, event.pos)

                self.resize = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.resize == True:
                self.resize = False

                self.msg = "Done resizing"
            
        if event.type == pygame.KEYDOWN:
            if self.selected and not ctrl_pressed:
                if event.key == pygame.K_BACKSPACE:
                    if self.selected.label > 0:
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
                    if self.selected.delete(g.f):
                        self.msg = "Removing keyframe"
                        print "Removing keyframe from selected marker"
                    else:
                        self.msg = "No keyframe in frame"
                        print "No keyframes at current frame! (only teal selections can be deleted -- not purple)"

                    if len(self.selected.fs) == 0:
                        self.rects.remove(self.selected)
                        self.selected = None

                        self.msg = "Removing marker"
                        print "No keyframes left in marker... Removing marker"
                else:
                    self.msg = "No marker selected!"
                    print self.msg

    def draw(self, g):
        frame = g.vid.get_data(g.f)

        surf = pygame.surfarray.make_surface(numpy.rollaxis(frame, 1, 0))

        for rect in self.rects:
            if rect.interpolated(g.f) or rect == self.selected:
                color = [255, 0, 0]
            else:
                continue

            (x, y), (w, h), rtype = rect.sample(g.f)
            
            x = int(x)
            y = int(y)
            w = int(w)
            h = int(h)
            
            if rtype == Rect.KEYFRAME:
                color = [0, 255, 0]

            if rtype == Rect.EXTRAPOLATE:
                color = [150, 150, 150]
                
            if rect == self.selected:
                color[2] = 255

            if rect.label != None:
                label = g.font.render(rect.label, 1, (255, 255, 255))
            else:
                label = g.font.render("no label", 1, (255, 0, 255))

            if rtype != Rect.EXTRAPOLATE or rect == self.selected:
                width = 1 if rtype == Rect.EXTRAPOLATE else 4

                li = y / 16
                lj = x / 16

                ri = (y + h) / 16
                rj = (x + w) / 16

                for xx in range(lj * 16, (rj + 1) * 16 + 1, 16):
                    pygame.draw.line(surf, (255, 255, 255), (xx, li * 16), (xx, (ri + 1) * 16), 1)

                for yy in range(li * 16, (ri + 1) * 16 + 1, 16):
                    pygame.draw.line(surf, (255, 255, 255), (lj * 16, yy), ((rj + 1) * 16, yy), 1)

                pygame.draw.rect(surf, color, ((x, y), (w, h)), width)
                surf.blit(label, (x, y - 15))

        g.screen.blit(surf.convert(), (0, 0))

        lines = []
        lines.append("Frame jump: {0}".format(g.s))
        lines.append("Frames: {0} / {1}".format(g.f, g.F))
        lines.append("")

        if self.selected:
            lines.append("Keyframes: ")
            for f_ in self.selected.fs:
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
        lines.append(self.msg)

        for i, line in enumerate(lines):
            label = g.font.render(line, 1, (255, 255, 255))
            g.screen.blit(label, (g.W, 15 * i))

