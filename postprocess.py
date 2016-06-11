#%%

import numpy
import skimage.io
import skimage.transform
import matplotlib.pyplot as plt

import os
import json

os.chdir('/home/bbales2/annotater')

#%%

frames = []

for fname in sorted(os.listdir('images')):
    im = skimage.io.imread('images/{0}'.format(fname), as_grey = True)

    w, h = ((256.0 / max(im.shape)) * numpy.array(im.shape)).astype('int')

    frame = skimage.transform.resize(im, (w, h))

    frames.append(frame)

#%%
f = open('output.txt', 'r')
data = json.load(f)
f.close()
#%%
b = 10

Xs = range(-b, b)
Ys = range(-b, b)

Xs, Ys = numpy.meshgrid(Xs, Ys, indexing = 'xy')

R = numpy.sqrt(Xs * Xs + Ys * Ys)

sigma = 4.0
sampler = numpy.exp(-R**2 / (2 * sigma**2))
plt.imshow(sampler)
sampler /= sampler.sum()
#%%
#%%

samples = []

im2s = []

for i, im in enumerate(frames):
    #plt.imshow(im, interpolation = 'NONE', cmap = plt.cm.gray)
    sampleT = []

    tform = skimage.transform.estimate_transform('similarity', numpy.array(data[i])[:, ::-1], numpy.array(data[0])[:, ::-1]
)

    print tform(data[i]), data[0]

    im2s.append(skimage.transform.warp(im, inverse_map = tform.inverse))

    plt.imshow(im, cmap = plt.cm.gray, interpolation = 'NONE')
    for x, y in data[i]:
        sampleT.append((im[y - b : y + b, x - b : x + b] * sampler).sum())
        circle = plt.Circle((y, x), 5, color = 'r', fill = None)
        plt.gca().add_artist(circle)
    #plt.show()
    plt.savefig('images3/image{0:03d}.png'.format(i))
    plt.show()

    #skimage.io.imsave('images2/image{0:03d}.png'.format(i), im2s[-1])
    samples.append(sampleT)

samples = numpy.array(samples)

#%%
plt.plot(samples[:, 0])
plt.plot(samples[:, 1])
plt.ylabel('Image Intensity')
plt.xlabel('Frame Number')
plt.show()

data[50]