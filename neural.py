            elif event.key == pygame.K_t and ctrl_pressed:

                msg = "Training network..."
                print msg

                classes = {}

                Xs = []
                Ys = []

                for rect in rects:
                    if rect.label not in classes:
                        classes[rect.label] = len(classes)

                    for f_ in rect.fs:
                        im = vid.get_data(f_)
                        
                        feats = sess.run(target, feed_dict = { tens : im.reshape(1, im.shape[0], im.shape[1], im.shape[2]) })[0]

                        (x, y), (w, h), keyframe = rect.sample(f_)

                        if keyframe:
                            i = int(y + h / 2) / 16
                            j = int(x + w / 2) / 16

                            Xs.append(feats[i, j])
                            Ys.append(classes[rect.label])

                        #for i in range(H / 16):
                        #    for j in range(W / 16):
                        #        if rect.contains(f_, (j * 16 + 8, i * 16 + 8)):
                        #            Xs.append(feats[i, j])
                        #            Ys.append(classes[rect.label])

                lgr = sklearn.linear_model.LogisticRegression()

                lgr.fit(Xs, Ys)

                msg = "Network trained!"
                print msg

    if lgr and selected and selected.label in classes:
        hist = sess.run(target, feed_dict = { tens : frame.reshape(1, frame.shape[0], frame.shape[1], frame.shape[2]) })[0]#numpy.linalg.norm(, axis = 2)

        hist = lgr.predict_log_proba(hist.reshape((-1, 1024))).reshape((H / 16, W / 16, -1))

        hist = numpy.argmax(hist, axis = 2).astype('float')#hist[:, :, classes[selected.label]]

        hist -= hist.min()
        hist /= hist.max()
        hist = plt.cm.jet(hist)[:, :, :3]
        hist = (hist * 255).astype('uint8')
        
        hist = numpy.kron(hist, numpy.ones((16, 16, 1)))
        
        nn = pygame.surfarray.make_surface(numpy.rollaxis(hist, 1, 0))
        nn.set_alpha(63)
        
        surf.blit(nn, (0, 0))
