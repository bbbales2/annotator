#%%
import sys
import os
os.chdir('/home/bbales2/annotater')
import googlenet

import tensorflow as tf
import pickle
import imageio

import numpy

im2 = numpy.zeros((1, 480, 640, 3))
#%%

reload(googlenet)

tf.reset_default_graph()

sess = tf.Session()

tens = tf.placeholder(tf.float32, shape = [1, im2.shape[1], im2.shape[2], 3])

# Create an instance, passing in the input data
with tf.variable_scope("image_filters", reuse = False):
    net = googlenet.GoogleNet({'data' : tens})

with tf.variable_scope("image_filters", reuse = True):
    net.load('googlenet.tf', sess, ignore_missing = True)
#%%
target = [net.layers[name] for name in net.layers if name == 'pool5_7x7_s1'][0]

#%%
import time

tmp = time.time()
hist = sess.run(target, feed_dict = { tens : im2 })[0]
print time.time() - tmp

print hist.shape
#%%
with open('test5') as f:
    ann = pickle.load(f)

vid = imageio.get_reader('monsters.mp4', 'ffmpeg')
W, H = vid.get_meta_data()['size']
vids = []
for f in range(len(vid)):
    print f
    vids.append(vid.get_data(f))

vid = numpy.array(vids)
#%%
labels = set(ann.labels.values())
l2i = dict((l, i) for i, l in enumerate(labels))
i2l = dict((i, l) for l, i in l2i.iteritems())
#%%
import sklearn.linear_model
import matplotlib.pyplot as plt
import matplotlib.patches
import time
import collections

Xs = collections.defaultdict(list)
#Ys = collections.defaultdict(list)

Xns = collections.defaultdict(list)
#Yns = collections.defaultdict(list)

for label in labels:
    for (f, (x, y)), label_ in ann.labels.iteritems():
        if label_ != label:
            continue

        im = vid[f]

        tmp = time.time()
        print time.time() - tmp

        tmp = time.time()
        feats = sess.run(target, feed_dict = { tens : im.reshape(1, im.shape[0], im.shape[1], im.shape[2]) })[0]
        print time.time() - tmp

        Xs[label].append(feats[y, x])
        #Ys[label].append(1)

        geomx, geomy = ann.geoms[label]

        li = y - (geomy - 1) / 2
        lj = x - (geomx - 1) / 2

        #plt.imshow(im)
        #ax = plt.gca()

        #ax.add_patch(matplotlib.patches.Rectangle((lj * 16, li * 16), geomx * 16, geomy * 16, fill=False, color = 'white'))
        #plt.imshow(im[li * 16 : (li + geomy) * 16, lj * 16 : (lj + geomx) * 16])

        n = 0
        nxs = []
        nys = []
        while n < 100:
            i = numpy.random.randint(0, feats.shape[0])
            j = numpy.random.randint(0, feats.shape[1])

            if (li > i or li + geomy < i) and (lj > j or lj + geomx < j):
                Xns[label].append(feats[i, j])
                #Yns[label].append(0)
                n += 1

                nys.append(i * 16)
                nxs.append(j * 16)

                #plt.imshow(im[li * 16 : (li + geomy) * 16, lj * 16 : (lj + geomx) * 16])
                #plt.show()

        #plt.plot(nxs, nys, 'ow')
        #plt.show()
                            #for i in range(H / 16):
                            #    for j in range(W / 16):
                            #        if rect.contains(f_, (j * 16 + 8, i * 16 + 8)):
                            #            Xs.append(feats[i, j])
                            #            Ys.append(classes[rect.label])

#lgr = sklearn.linear_model.LogisticRegression()
#%%
for l0 in labels:
    for l1 in labels:
        if l0 != l1:
            Xns[l0].extend(Xs[l1])
            #Yns[l0].extend([0] * len(Xs[l1]))
#%%
clss = {}
for label in labels:
    Xt = []
    Yt = []

    Xt.extend(Xs[label])
    Yt.extend([1] * len(Xs[label]))
    Xt.extend(Xns[label])
    Yt.extend([0] * len(Xns[label]))

    lvc = sklearn.linear_model.LogisticRegression(class_weight = 'balanced')#sklearn.svm.SVC(class_weight = 'balanced')
    lvc.fit(Xt, Yt)
    clss[label] = lvc
#%%
for label in labels:
    for (f, (x, y)), label_ in ann.labels.iteritems():
        if label_ != label:
            continue

        im = vid[f]

        hist = sess.run(target, feed_dict = { tens : im.reshape(1, im.shape[0], im.shape[1], im.shape[2]) })[0]

        hist = clss[label].predict(hist.reshape((-1, 1024))).reshape((H / 16, W / 16))

        1/0

    #hist = numpy.argmax(hist, axis = 2).astype('float')#hist[:, :, classes[selected.label]]

    #hist -= hist.min()
    #hist /= hist.max()
    #hist = plt.cm.jet(hist)[:, :, :3]
    #            hist = (hist * 255).astype('uint8')

        hist = numpy.kron(hist, numpy.ones((16, 16)))

        plt.imshow(im, interpolation = 'NONE')
        plt.imshow(hist, alpha = 0.3, interpolation = 'NONE')
        plt.title(label)
        plt.show()
#%%
import mahotas
ls, c = mahotas.label(hist)

sums = mahotas.labeled_sum(hist, ls)[1:]
coords = mahotas.center_of_mass(hist, ls)[1:]
#%%
with open('classifiers', 'w') as f:
    pickle.dump(clss, f)
#%%
for label in labels:
    try:
        writer = imageio.get_writer('movie_{0}.mp4'.format(label), fps = 24.0)

        cmap = plt.cm.jet

        for f in range(len(vid)):
            im = vid[f]

            tmp = time.time()
            hist = sess.run(target, feed_dict = { tens : im.reshape(1, im.shape[0], im.shape[1], im.shape[2]) })[0]
            print time.time() - tmp

            tmp = time.time()
            hist = clss[label].predict(hist.reshape((-1, 1024))).reshape((H / 16, W / 16, -1))
            print time.time() - tmp

            hist = hist.reshape((hist.shape[0], hist.shape[1]))

            hist = numpy.kron(hist, numpy.ones((16, 16)))

            #plt.imshow(im, interpolation = 'NONE')
            #plt.imshow(hist, alpha = 0.3, interpolation = 'NONE')
            #plt.title(label)
            #plt.show()

            towrite = im * 0.75 / 255.0 + cmap(hist)[:, :, :3] * 0.25
            #plt.imshow(towrite)
            #plt.show()
            writer.append_data(towrite)
            print "movie_{0}.mp4 -- {1} / {2} frames rendered".format(label, f, len(vid))
    finally:
        writer.close()
#%%
frame = g.vid.get_data(g.f)
#%%
names = []
for name in net.layers:
    names.append(name)

for name in sorted(names):
    print name

#%%

import skimage.io

im2 = skimage.io.imread('/home/bbales2/lineage_process/dec9/121.png').astype('float')

shift = numpy.array([104., 117., 124.])

im2 = im2 - shift

im2 = im2.reshape((1, im2.shape[0], im2.shape[1], im2.shape[2]))
