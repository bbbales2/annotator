import sys
import os
import googlenet

import tensorflow as tf
import pickle
import imageio

import numpy

import sklearn.linear_model
import matplotlib.pyplot as plt
import matplotlib.patches
import time
import collections
import skimage.io

import argparse

parser = argparse.ArgumentParser(description='Train the last layer of a GoogleNet neural network')
parser.add_argument('file', help = 'Path to video file whos frames are labeled')
parser.add_argument('annotationFile', help = 'File that holds the labels')
parser.add_argument('classifiersFile', help = 'File that will holds the trained classifiers')
parser.add_argument('--fileList', help = 'Treat file argument as a text file with newline separated paths to images to be annotated instead of video file', action = 'store_true')
parser.add_argument('--negatives', type = int, default = 30, help = 'Number of negative examples to datamine for each positive example')

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

                if len(frame.shape) == 2:
                    frame = (255 * plt.cm.Greys(frame)[:, :, :3]).astype('uint8')

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

print "Loading GoogleNet neural network"

tf.reset_default_graph()

sess = tf.Session()

tens = tf.placeholder(tf.float32, shape = [1, H, W, 3])

# Create an instance, passing in the input data
with tf.variable_scope("image_filters", reuse = False):
    net = googlenet.GoogleNet({'data' : tens})

with tf.variable_scope("image_filters", reuse = True):
    net.load('googlenet.tf', sess, ignore_missing = True)

target = [net.layers[name] for name in net.layers if name == 'pool5_7x7_s1'][0]

test = sess.run(target, feed_dict = { tens : numpy.zeros((1, H, W, 3)) })[0]

print "Neural network loaded"

with open(args.annotationFile) as fh:
    ann = pickle.load(fh)
    
labels = set([marker.label for marker in ann.markers])
l2i = dict((l, i) for i, l in enumerate(labels))
i2l = dict((i, l) for l, i in l2i.iteritems())

# This will be a list, for each class, of positive example features
Xs = collections.defaultdict(list)

# This will be a list, for each class, of negative example features
Xns = collections.defaultdict(list)

# Sort markers by frame and label
mbf = {}
for marker in ann.markers:
    if marker.f not in mbf:
        mbf[marker.f] = {}

    if marker.label not in mbf[marker.f]:
        mbf[marker.f][marker.label] = []

    mbf[marker.f][marker.label].append(marker)

m = 0
for frame, mbl in mbf.iteritems():
    for label, markersTmp in mbl.iteritems():
        for marker in markersTmp:
            im = files[frame].im

            #tmp = time.time()
            feats = sess.run(target, feed_dict = { tens : im.reshape(1, im.shape[0], im.shape[1], im.shape[2]) })[0]
            #time.time() - tmp
            
            Xs[label].append(feats[marker.y / 16, marker.x / 16])
            #Ys[label].append(1)
            
            n = 0
            negatives = list()
            
            while n < args.negatives:
                i = numpy.random.randint(0, feats.shape[0])
                j = numpy.random.randint(0, feats.shape[1])
            
                if (i, j) not in negatives:
                    is_negative = True

                    # If the random proposal lands in this marker, or any similarly labeled marker on this frame discard it
                    for markerTmp in markersTmp:
                        if markerTmp.contains(frame, (j * 16 + 8, i * 16 + 8)):
                            is_negative = False
                            break
                            
                    if is_negative:
                        Xns[label].append(feats[i, j])
                        n += 1
            
                        negatives.append((i, j))

            m += 1
            print "Processed label {0} / {1}".format(m, len(ann.markers))

        #nys, nxs = zip(*negatives)

        #nys = numpy.array(nys) * 16 + 8
        #nxs = numpy.array(nxs) * 16 + 8

        #plt.imshow(im)
        #plt.gca().add_artist(plt.Circle((marker.x, marker.y), marker.r, color='r'))
        #plt.plot(nxs, nys, 'ow')
        #plt.show()

# Add the positive examples of each class to the negative examples of all the others
for l0 in labels:
    for l1 in labels:
        if l0 != l1:
            Xns[l0].extend(Xs[l1])

# Build a binary classifier for each class
classifiers = {}
for label in labels:
    Xt = []
    Yt = []

    Xt.extend(Xs[label])
    Yt.extend([1] * len(Xs[label]))
    Xt.extend(Xns[label])
    Yt.extend([0] * len(Xns[label]))

    lvc = sklearn.linear_model.LogisticRegression(class_weight = 'balanced')#sklearn.svm.SVC(class_weight = 'balanced')
    lvc.fit(Xt, Yt)
    classifiers[label] = lvc

with open(args.classifiersFile, 'w') as f:
    pickle.dump(classifiers, f)

print "Classifiers written!"

#shift = numpy.array([104., 117., 124.])

#im2 = im2 - shift

#im2 = im2.reshape((1, im2.shape[0], im2.shape[1], im2.shape[2]))
