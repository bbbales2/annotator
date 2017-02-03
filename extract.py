#%%
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
os.chdir('/home/bbales2/annotator')

import googlenet
import matplotlib.pyplot as plt

pygame.init()

import annotate
import traceback
import skimage.io
import tensorflow as tf

import argparse

#parser = argparse.ArgumentParser(description='Check how the classifier worked')
#parser.add_argument('file', default = 'monsters.mp4', help = 'Path to video file with frames to annotate')
#parser.add_argument('annotationFile', default = 'labels.pkl', help = 'File that holds the project annotations')
#parser.add_argument('classifiersFile', default = 'classifiers.pkl', help = 'File that holds the project classifiers')
#parser.add_argument('--fileList', action = 'store_true', help = 'Treat file argument as a text file with newline separated paths to images to be annotated instead of video file')

#args = parser.parse_args()

class File(object):
    def __init__(self, path = None, im = None):
        self.path = path
        self.im = im

files = []

#if args.fileList:
#    # TODO: Need to allow any resolution
#    W, H = 1024, 1024
#
#    with open(args.file) as f:
#        for line in f:
#            line = line.strip()
#            
#            if len(line) > 0 and os.path.exists(line):
#                frame = skimage.io.imread(line)
#
#                frame = numpy.pad(frame, ((0, max(0, 1024 - frame.shape[0])), (0, max(0, 1024 - frame.shape[1]))), mode = 'edge')
#
#                frame = frame[:H, :W]
#
#                files.append(File(line, frame))
#else:
if True:
    vid = imageio.get_reader('monsters.mp4', 'ffmpeg')

    W, H = vid.get_meta_data()['size']

    F = vid.get_length()
    for i, frame in enumerate(vid):
        #if i > 100:
        #    break

        files.append(File('{0}, frame = {1}'.format('monsters.mp4', i), frame))

        print "Reading frame {0} / {1}".format(i, F)

# Load up the neural network
#%%
print "Loading GoogleNet neural network"

sess = tf.Session()

tens = tf.placeholder(tf.float32, shape = [1, H, W, 3])

net = googlenet.GoogleNet({'data' : tens})

net.load('googlenet.tf', sess, ignore_missing = True)

target = [net.layers[name] for name in net.layers if name == 'pool5_7x7_s1'][0]

test = sess.run(target, feed_dict = { tens : numpy.zeros((1, H, W, 3)) })[0]

print "Neural network loaded"
#%%

with open('classifiers.pkl') as f:
    classifiers = pickle.load(f)

with open('labels.pkl') as fh:
    ann = pickle.load(fh)
#%%
msg = ""

labels = classifiers.keys()

for i, f in enumerate(files):
    plt.imshow(f.im)
    plt.title(i)
    plt.show()
    
    if i > 50:
        break
#%%
frame = files[10].im
hist = sess.run(target, feed_dict = { tens : frame.reshape(1, frame.shape[0], frame.shape[1], frame.shape[2]) })[0]
hist = classifiers['fallen'].predict_proba(hist.reshape((-1, 1024)))[:, 1].reshape((H / 16, W / 16))
#%%
plt.imshow(hist[:, :], interpolation = 'NONE')
plt.colorbar()
plt.show()
#%%
import bisect
import time

L = 5

l = hist.sum()
m = numpy.random.poisson(l)
sums = numpy.cumsum(hist.flatten())
xs = []
for i in range(m):
    idx = bisect.bisect_left(sums, numpy.random.random() * l)
    xs.append(numpy.unravel_index(idx, hist.shape))
    
xs = numpy.array(xs)

plt.imshow(hist, interpolation = 'NONE')
plt.colorbar()
plt.plot(xs[:, 1], xs[:, 0], 'w+')
plt.show()
#%%
tmp1 = time.time()
u = numpy.random.random((L, 2)) * hist.shape
sig = 1.5
I = numpy.random.random(L)

def norm(x, u, sig):
    return numpy.exp(-0.5 * (x - u).dot(x - u) / (sig**2)) / (2 * numpy.pi * sig)

print u, I

for r in range(10):
    T = []
    for j in range(m):
        total = 0.0
        
        for l in range(L):
            total += norm(xs[j], u[l], sig)
            
        T.append(total)
        
    un = numpy.zeros(u.shape)
    for l in range(L):
        total = 0.0
        
        unum = 0.0
        signum = 0.0
        
        denom = 0.0
        
        for j in range(m):
            tmp = norm(xs[j], u[l], sig) / T[j]
            
            total += tmp
            unum += xs[j] * tmp
            signum += sum((xs[j] - u[l]) * (xs[j] - u[l])) * tmp
           
        un[l] = unum / total
        I[l] = total
        
#    total = 0.0
#    denom = 0.0
#        
#    for j in range(m):
#        tmp = norm(xs[j], u[l], sig) / T[j]
#            
#        total += tmp
#        signum += sum((xs[j] - un[l]) * (xs[j] - un[l])) * tmp
#        
#    sig = numpy.sqrt(signum / total)
        
    u = un
        
    #print "Means: ", u
    #print "Intensities: ", I
    #print "sig: ", sig
    #print "---"
print "Time: ", time.time() - tmp1
    
plt.imshow(hist, interpolation = 'NONE')
plt.colorbar()
idxs = numpy.where(I > 0.1)
plt.plot(u[idxs, 1], u[idxs, 0], 'wo')
plt.show()
