import numpy
import matplotlib.pyplot as plt
import pygame
from rect import Rect
import sklearn.linear_model

class Network(object):
    def __init__(self, sess, target, placeholder):
        self.sess = sess
        self.target = target
        self.placeholder = placeholder
        self.lgr = None

        self.classes = {}
        self.negatives = {}

    def handle(self, event, g):
        ctrl_pressed = pygame.key.get_mods() & (pygame.KMOD_RCTRL | pygame.KMOD_LCTRL)

        if event.type == pygame.MOUSEBUTTONUP:
            if g.ann.selected:
                sel = g.ann.selected
                if sel.label:
                    if event.button == 1:
                        # create negative sample
                        if sel.label not in self.negatives:
                            self.negatives[sel.label] = []

                        self.negatives[sel.label].append((g.f, event.pos))
                        
                        print "Negative added"
                    elif event.button == 3:
                        if sel.label in self.negatives and len(self.negatives[self.label]) > 0:
                            idxs = []
                            ds = []
                            for idx, (f, (x, y)) in enumerate(self.negatives[self.label]):
                                if f == self.f:
                                    idxs.append(idx)
                                    ds.append(numpy.sqrt((x - event.pos[0])**2 + (y - event.pos[1])**2))

                            if len(ds) > 0:
                                self.negatives.pop(idxs[numpy.argmin(ds)])
                                
                                print "Negative deleted"
                            else:
                                print "No negative deleted"
                            
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_t:# and ctrl_pressed:
                msg = "Training network..."
                print msg

                self.classes = {}

                Xs = []
                Ys = []

                print len(g.ann.rects)
                for rect in g.ann.rects:
                    print rect.label
                    if rect.label not in self.classes:
                        self.classes[rect.label] = len(self.classes)

                    for f_ in rect.fs:
                        im = g.vid.get_data(f_)
                        
                        feats = self.sess.run(self.target, feed_dict = { self.placeholder : im.reshape(1, im.shape[0], im.shape[1], im.shape[2]) })[0]

                        (x, y), (w, h), ftype = rect.sample(f_)

                        if ftype == Rect.KEYFRAME:
                            
                            i = int(y + h / 2) / 16
                            j = int(x + w / 2) / 16

                            Xs.append(feats[i, j])
                            Ys.append(self.classes[rect.label])

                        print Ys

                        #for i in range(H / 16):
                        #    for j in range(W / 16):
                        #        if rect.contains(f_, (j * 16 + 8, i * 16 + 8)):
                        #            Xs.append(feats[i, j])
                        #            Ys.append(classes[rect.label])

                self.lgr = sklearn.linear_model.LogisticRegression()

                self.lgr.fit(Xs, Ys)

                msg = "Network trained!"
                print msg

    def draw(self, g):
        g.ann.draw(g)

        surf = pygame.Surface((g.H, g.W))

        for name in self.negatives:
            label = g.font.render("-{0}".format(name), 1, (255, 255, 255))
            for f, (x, y) in self.negatives[name]:
                pygame.draw.circle(g.screen, (255, 255, 255), (x, y), 20, 1)
                g.screen.blit(label, (x - label.get_width() / 2, y - 25 - label.get_height() / 2))

        #g.screen.blit(surf, (0, 0))

        if self.lgr and g.ann.selected and g.ann.selected.label in self.classes:
            frame = g.vid.get_data(g.f)

            hist = self.sess.run(self.target, feed_dict = { self.placeholder : frame.reshape(1, frame.shape[0], frame.shape[1], frame.shape[2]) })[0]

            hist = self.lgr.predict_log_proba(hist.reshape((-1, 1024))).reshape((g.H / 16, g.W / 16, -1))

            hist = numpy.argmax(hist, axis = 2).astype('float')#hist[:, :, classes[selected.label]]

            hist -= hist.min()
            hist /= hist.max()
            hist = plt.cm.jet(hist)[:, :, :3]
            hist = (hist * 255).astype('uint8')
            
            hist = numpy.kron(hist, numpy.ones((16, 16, 1)))
        
            nn = pygame.surfarray.make_surface(numpy.rollaxis(hist, 1, 0))
            nn.set_alpha(63)
        
            g.screen.blit(nn, (0, 0))
