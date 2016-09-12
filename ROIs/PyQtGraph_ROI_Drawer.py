#!/usr/bin/env python
import h5py
import sys


def MASK_DRAWER_GUI(areaFile,restart=False):
    import numpy as np
    from pyqtgraph.Qt import QtGui, QtCore
    from pyqtgraph import Qt
    import pyqtgraph as pg
    import time
    import sys
    import os
    import copy as cp
    from skimage.filters import gaussian as gaussian_filter
    from skimage.morphology import disk
    from skimage.filters.rank import median as median_filter
    from scipy.ndimage.morphology import binary_fill_holes




    class Visualizator(QtGui.QMainWindow):

        def __init__(self, ROI_patches,ROI_masks,areaFile):
            QtGui.QMainWindow.__init__(self)
            self.Folder = os.path.dirname(areaFile.file.filename) + '/'
            self.idx = 0
            self.ROI_patches = []#ROI_patches
            self.masks = []#np.zeros(ROI_patches.shape)
            #print self.masks.shape, ROI_masks.shape
            #self.masks[:,:,:ROI_masks.shape[2]] = ROI_masks
            self.mean_image = np.mean(areaFile[:3000],axis=0).T
            self.ROI_attrs = {'centres':[],
                              'patches':[],
                              'masks':[],
                              'idxs':[],
                              'traces':[]}
            self.play_video = False
            self.rolling_average = 10
            self.ROI_centres = []#areaFile.attrs['ROI_centres']
            self.video = areaFile
            self.nFrames = self.video.shape[0]
            self.frame_idx = self.rolling_average
            self.smoothing = 1
            self.maskalpha = 0.6
            self.mask = np.zeros([areaFile.shape[1],
                                 areaFile.shape[2],
                                 4])

            self.temp_mask = np.zeros([areaFile.shape[1],
                                 areaFile.shape[2]])

            self.show_mean_image = True
            #self.masks = np.zeros(ROI_patches.shape)
            #initialise the main window
            w = QtGui.QWidget()
            layout = QtGui.QGridLayout()
            w.setLayout(layout)
            self.prevT = time.time()

            self.IFI=2
            self.vidTimer = QtCore.QTimer()
            self.vidTimer.timeout.connect(self.update_video)
            self.vidTimer.start(self.IFI)

            self.img = pg.ImageItem()
            self.mask_img = pg.ImageItem()
            print areaFile.shape
            self.img.setImage(areaFile[self.frame_idx,:,:].T)
            self.mask_img.setImage(self.mask)
            self.mask_img.setOpacity(self.maskalpha)

            self.frameTxt = pg.TextItem('Frame Nr: ' + str(self.frame_idx+1) + '/' + str(self.nFrames))
            
            """ This section contains the code to
                create and upgrade the histogram
                used to control the image """
            self.histLI = pg.HistogramLUTWidget(image=self.img,fillHistogram=False)
            self.histLI.autoHistogramRange=False
            
            self.roi_item = pg.EllipseROI([60, 10], [30, 20], pen=(3,9))
            self.vb = pg.ViewBox()
            self.vb.setAspectLocked(1)
            self.vb.addItem(self.img)
            self.vb.addItem(self.roi_item)
            self.vb.addItem(self.mask_img)
            #self.vb.addItem(self.img_ROI)      
            #self.vb.addItem(self.tx)
            self.vb.addItem(self.frameTxt)
            grV1 = pg.GraphicsView(useOpenGL=True)
            grV1.setCentralItem(self.vb)
            self.vb.scene().sigMouseMoved.connect(self.mouseMoved)
            #self.img.sigClicked.connect(self.test1)
            #self.sigClicked.connect(self.test1)
            self.vb.scene().sigMouseClicked.connect(self.onClick)          #THIS IS IT!

            self.Gplt = pg.PlotWidget(background='w')
            self.Gplt.setFixedHeight(200)
            self.Gplt.setXRange(0,self.nFrames)


            self.timeLine = pg.InfiniteLine(pos=self.frame_idx,angle=90,movable=True)
            self.Gplt.addItem(self.timeLine)
            self.timeLine.sigDragged.connect(self.update_timeline)

            ############## INIT ROI IMAGES #######################
            cols,rows = areaFile.shape[1:3]
            m = np.mgrid[:cols,:rows]
            self.possx = m[0,:,:]# make the x pos array
            self.possy = m[1,:,:]# make the y pos array


            ############## INIT BUTTONS #######################
            btn1 = QtGui.QPushButton("Next ROI", self)
            btn2 = QtGui.QPushButton("Previous ROI", self)
            btn3 = QtGui.QPushButton("Save Progress", self)
            btn4 = QtGui.QPushButton("Clear ROI", self)
            btn5 = QtGui.QPushButton("Play Video", self)
            btn6 = QtGui.QPushButton("Update ROI Trace",self)
            btn7 = QtGui.QPushButton("Increase Rolling Average", self)
            btn8 = QtGui.QPushButton("Decrease Rolling Average", self)
            btn9 = QtGui.QPushButton("Increase Spatial Smoothing", self)
            btn10 = QtGui.QPushButton("Decrease Spatial Smoothing", self)
            btn11 = QtGui.QPushButton("Show Mean Image", self)
            btn12 = QtGui.QPushButton("Hide Mask", self)
            btn1.clicked.connect(self.buttonClicked)            
            btn2.clicked.connect(self.buttonClicked)
            #btn3.clicked.connect(self.save_ROIS)
            btn4.clicked.connect(self.buttonClicked)
            btn5.clicked.connect(self.buttonClicked)
            btn6.clicked.connect(self.buttonClicked)
            btn7.clicked.connect(self.buttonClicked)
            btn8.clicked.connect(self.buttonClicked)
            btn9.clicked.connect(self.buttonClicked)
            btn10.clicked.connect(self.buttonClicked)
            btn11.clicked.connect(self.buttonClicked)
            btn12.clicked.connect(self.buttonClicked)

            layout.addWidget(grV1,0,0,7,8)
            layout.addWidget(btn1,9,1,1,1)
            layout.addWidget(btn2,9,0,1,1)
            layout.addWidget(btn3,10,2,1,1)
            layout.addWidget(btn4,10,3,1,1)
            layout.addWidget(btn5,9,2,1,1)
            layout.addWidget(btn6,9,3,1,1)
            layout.addWidget(btn7,9,5,1,1)
            layout.addWidget(btn8,9,6,1,1)
            layout.addWidget(btn9,10,5,1,1)
            layout.addWidget(btn10,10,6,1,1)
            layout.addWidget(btn11,10,1,1,1)
            layout.addWidget(btn12,10,0,1,1)
            layout.addWidget(self.Gplt,11,0,3,8)

            layout.addWidget(self.histLI,0,8,7,2)
            self.setCentralWidget(w)
            self.show()
            #self.connect(self, Qt.SIGNAL('triggered()'), self.closeEvent
        #def save_ROIS(self):
        #    arr = cp.deepcopy(np.array((self.masks)))
        #    areaFile.attrs['ROI_masks'] = arr
        #    #-------- Save ROIs to hdf5
        #    f_handle = h5py.File(self.Folder +'ROI_data.h5','w',libver='latest')
        #    f_handle.create_dataset('ROI_masks',data=cp.deepcopy(np.array((self.masks))),dtype='int16')
        #    f_handle.create_dataset('ROI_patches',data=areaFile.attrs['ROI_patches'],dtype='int16')
        #    f_handle.create_dataset('ROI_locs',data=np.array(areaFile.attrs['ROI_centres']),dtype='int16')
        #    f_handle.attrs['parent_file'] = areaFile.name
        #    f_handle.close()
        #    print 'ROI MASKS SAVED'


        #def closeEvent(self, event):
        #    print 'leaving now \n you have drawn %s ROIs' %self.masks.shape[2]
        #    event.accept() # let the window close
        #    #areaFile

        def onClick(self,ev):
            print self.vb.mapSceneToView(ev.pos())
            if ev.button()==1 and ev.double():
                self.proc_roi_region(add_region=True)
                self.mask_img.setImage(self.mask,autoLevels=False,levels=[0,2])
            elif ev.button()==2 and ev.double():
                self.proc_roi_region(add_region=False)
                self.mask_img.setImage(self.mask,autoLevels=False,levels=[0,2])

                pass


        def proc_roi_region(self,add_region=True):

            mpossx = self.roi_item.getArrayRegion(self.possx,self.img).astype(int)
            mpossx = mpossx[np.nonzero(mpossx)]#get the x pos from ROI
            mpossy = self.roi_item.getArrayRegion(self.possy,self.img).astype(int)
            mpossy = mpossy[np.nonzero(mpossy)]# get the y pos from ROI
            xLims = [np.min(mpossx)-10,np.max(mpossx)+10]
            yLims = [np.min(mpossy)-10,np.max(mpossy)+10]
            #xLims = [np.mean(mpossx)-20,np.mean(mpossx)+20]; yLims = [np.mean(mpossy)-20,np.mean(mpossy)+20]



            self.temp_mask[mpossx,mpossy] = 1
            self.temp_mask = binary_fill_holes(self.temp_mask).T


            if add_region:
                self.ROI_attrs['centres'].append([np.mean(mpossx),np.mean(mpossy)])
                self.ROI_attrs['patches'].append(np.mean(areaFile[:,yLims[0]:yLims[1],xLims[0]:xLims[1]],axis=0))

                self.ROI_attrs['traces'].append(np.mean(
                                                        areaFile[:,yLims[0]:yLims[1],xLims[0]:xLims[1]] *
                                                        self.temp_mask[yLims[0]:yLims[1],xLims[0]:xLims[1]],
                                                        axis=(1,2)))
                self.ROI_attrs['idxs'].append(1)
                self.ROI_attrs['masks'].append(self.temp_mask[yLims[0]:yLims[1],xLims[0]:xLims[1]])
                self.Gplt.clear()
                self.Gplt.addItem(self.timeLine)
                self.Gplt.plot(self.ROI_attrs['traces'][-1])
                """from matplotlib.pyplot import imshow,show,plot, figure

                figure()
                imshow(self.ROI_attrs['patches'][-1],cmap='binary_r')
                show()

                figure()
                imshow(self.ROI_attrs['masks'][0])
                show()

                figure()
                imshow(self.temp_mask,cmap='binary_r')
                show()

                figure()
                imshow(self.mean_image.T,cmap='binary_r')
                show()



                figure()
                plot(self.ROI_attrs['traces'][0])
                show()"""


                self.mask[:,:,0] += self.temp_mask.T
                self.mask[:,:,3] += self.temp_mask.T
            else:
                self.mask[mpossx,mpossy,0] = 0
                self.mask[mpossx,mpossy,3] = 0
                print 'here'
            self.temp_mask = np.zeros(self.temp_mask.shape) 
            #return self.mask



        def buttonClicked(self):
            sender = self.sender()
            if sender.text()=='Next ROI':
                if self.idx<nROIs-1:
                    self.idx += 1
                    self.frame_idx = self.rolling_average
                    self.Gplt.clear()
                    self.Gplt.addItem(self.timeLine)
            elif sender.text()=='Previous ROI':
                if self.idx>=1:
                    self.idx -= 1
                    self.frame_idx = self.rolling_average
                    self.Gplt.clear()
                    self.Gplt.addItem(self.timeLine)
            elif sender.text()=='Clear ROI':
                self.masks[:,:,self.idx] = 0
            elif sender.text()=='Hide Mask':
                if self.maskalpha==0:
                    self.maskalpha=0.2
                    self.img_ROI.setOpacity(self.maskalpha)

                else:
                    self.maskalpha=0
                    self.img_ROI.setOpacity(self.maskalpha)

            elif sender.text()=='Increase Rolling Average':
                self.rolling_average += 1
                print self.rolling_average
            elif sender.text()=='Show Mean Image':
                self.show_mean_image = not self.show_mean_image
            elif sender.text()=='Decrease Rolling Average':
                if self.rolling_average>=1:
                    self.rolling_average -= 1
                    print self.rolling_average
            elif sender.text()=='Increase Spatial Smoothing':
                self.smoothing += 0.1
            elif sender.text()=='Decrease Spatial Smoothing':
                if self.smoothing>0:
                    self.smoothing -= .1
            elif (sender.text()=='Play Video' or sender.text()=='Pause Video'):
                self.play_video = not self.play_video
                self.show_mean_image = False
                if not self.play_video:
                    sender.setText("Play Video")
                else:
                    sender.setText('Pause Video')
                


            elif sender.text()=="Update ROI Trace":
                print 'button regged'
                if ((self.masks.shape[1]<self.ROI_centres[self.idx][0]<512-self.masks.shape[1]) and
                    (self.masks.shape[1]<self.ROI_centres[self.idx][1]<512-self.masks.shape[1])):
                    print 'check completed %s' %self.ROI_centres[self.idx]
                    trace = np.mean(self.masks[:,:,self.idx]*self.video[:,int(self.ROI_centres[self.idx][1]-self.masks.shape[1]/2):int(self.ROI_centres[self.idx][1]+self.masks.shape[1]/2),
                                  int(self.ROI_centres[self.idx][0] - self.masks.shape[1]/2):int(self.ROI_centres[self.idx][0]+self.masks.shape[1]/2)],
                                          axis=(1,2))
                    print 'trace extracted'
                    self.Gplt.plot(trace)
                else:
                    print 'unable to plot outside of range'


            #self.tx.setText('ROI Nr: ' + str(self.idx+1) + '/' + str(nROIs))
            mask = np.zeros([self.masks.shape[0],self.masks.shape[1],3])
            #print self.masks.shape
            mask[np.where(self.masks[:,:,self.idx])] = (1,0,0)
            
            self.img_ROI.setImage(mask)
            self.img.setImage(self.ROI_patches[:,:,self.idx])




        #Play Video Play Function    
        def update_video(self):
            
            if self.play_video:
                video_image = np.mean(self.video[self.frame_idx-self.rolling_average:self.frame_idx+self.rolling_average+1],axis=0).T

                #video_image = median_filter(self.video,disk(2))
                video_image = gaussian_filter(video_image,self.smoothing)
                self.img.setImage(video_image,
                                  autoLevels=False)

                if self.frame_idx>=self.nFrames-1:
                    self.frame_idx=self.rolling_average
                
                self.frame_idx += 1
                self.frameTxt.setText('Frame Nr: ' + str(self.frame_idx+1) + '/' + str(self.nFrames))
                self.timeLine.setPos(self.frame_idx)
            if (self.show_mean_image and not self.play_video):
                self.img.setImage(self.mean_image)
            #if (not self.show_mean_image and not self.play_video):
            #
            #    video_image = np.mean(self.video[self.frame_idx-self.rolling_average:self.frame_idx+self.rolling_average+1,
            #                              int(self.ROI_centres[self.idx][1]-self.masks.shape[1]/2):int(self.ROI_centres[self.idx][1]+self.masks.shape[1]/2),
            #                              int(self.ROI_centres[self.idx][0] - self.masks.shape[1]/2):int(self.ROI_centres[self.idx][0]+self.masks.shape[1]/2)],
            #                              axis=0)
            #
            #    #video_image = median_filter(self.video,disk(2))
            #    video_image = gaussian_filter(video_image,self.smoothing)
            #    self.img.setImage(video_image,
            #                      autoLevels=False)



            #else:
            #    img.setImage(np.fliplr(np.mean(b[frame_idx-rolling_average:frame_idx+rolling_average+1,:,:],axis=0).T),
            #                 autoLevels=False)
            
                
        
        def update_timeline(self):

            while self.timeLine.isUnderMouse():
                self.play_video = False
                self.frame_idx = int(self.timeLine.getXPos())
                self.timeLine.setPos(self.frame_idx)
                #img.setImage(np.fliplr(np.mean(b[frame_idx-rolling_average:frame_idx+rolling_average+1,:,:],axis=0).T),autoLevels=False)
            self.play_video = True
        
        def add_ROI(self):
            print "I'm gonna add an ROI"



        def mouseMoved(self,e):

            if False:#(time.time() - self.prevT)>0.01:                 ###NEEEEEDS TO BE CHANGED BACK!!!
                a = self.img.mapFromScene(e)
                x_pos = a.x()
                y_pos = a.y()

                if  (y_pos<(self.masks.shape[1]-1) and  x_pos<(self.masks.shape[0]-1) and
                     y_pos>0                   and  x_pos>0):
                    
                    
                    
                    if y_pos>self.masks.shape[1]:
                        y_pos=self.masks.shape[1]
                    if x_pos>self.masks.shape[0]:
                        x_pos=self.masks.shape[0]

                    modifiers = QtGui.QApplication.keyboardModifiers()
                    if modifiers == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
                        self.masks[:,:,self.idx][int(np.floor(x_pos)),int(np.floor(y_pos))] = 1
                        self.masks[:,:,self.idx][int(np.ceil(x_pos)),int(np.ceil(y_pos))] = 1

                        mask = np.zeros([self.masks.shape[0],self.masks.shape[1],3])
                        mask[np.where(self.masks[:,:,self.idx])] = (1,0,0)


                        self.img_ROI.setImage(mask)

                    elif (modifiers == QtCore.Qt.ControlModifier and
                    not modifiers == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier)):
                        self.masks[:,:,self.idx][int(x_pos),int(y_pos)] = 1


                        mask = np.zeros([self.masks.shape[0],self.masks.shape[1],3])
                        mask[np.where(self.masks[:,:,self.idx])] = (1,0,0)
                        self.img_ROI.setImage(mask)

                    elif (modifiers == QtCore.Qt.AltModifier and
                    not modifiers == (QtCore.Qt.ShiftModifier | QtCore.Qt.AltModifier)):
                        self.masks[:,:,self.idx][int(x_pos),int(y_pos)] = 0

                        mask = np.zeros([self.masks.shape[0],self.masks.shape[1],3])
                        mask[np.where(self.masks[:,:,self.idx])] = (1,0,0)
                        self.img_ROI.setImage(mask)

                    elif modifiers == (QtCore.Qt.ShiftModifier | QtCore.Qt.AltModifier):
                        self.masks[:,:,self.idx][int(np.floor(x_pos)),int(np.floor(y_pos))] = 0
                        self.masks[:,:,self.idx][int(np.ceil(x_pos)),int(np.ceil(y_pos))] = 0

                        mask = np.zeros([self.masks.shape[0],self.masks.shape[1],3])
                        mask[np.where(self.masks[:,:,self.idx])] = (1,0,0)
                        self.img_ROI.setImage(mask)

                self.prevT = time.time()
                
    #nROIs = areaFile.attrs['ROI_patches'].shape[2]
    #if restart==True:
        #areaFile.attrs['ROI_masks'] = np.zeros(areaFile.attrs['ROI_patches'].shape)

    #if 'ROI_masks' not in (areaFile.attrs.iterkeys()):
    #    print 'no masks exist, creating empty ones'
    #    areaFile.attrs['ROI_masks'] = np.zeros(areaFile.attrs['ROI_patches'].shape)

    #roi_masks = cp.deepcopy(np.array(areaFile.attrs['ROI_masks'].astype('int')))
    app = QtGui.QApplication([])
    win = Visualizator(0,1,areaFile)
    #app.aboutToQuit.connect(app.deleteLater)
    #app.exec_()
    print sys.exit(app.exec_())

    return app






if __name__=="__main__":
	hdfPath = sys.argv[1]
	with h5py.File(hdfPath, 'a', libver='latest') as HDF_File:
		try:
			print HDF_File.filename
			print 'Sessions:'

			sessions = list((i for i in HDF_File.iterkeys()))
			for idx,f in enumerate(sessions):
				print idx, f 
			session = int(raw_input('Select Session Nr:'))

			sessions = list((i for i in HDF_File.iterkeys()))
			#print sessions

			dataType = 0
			if False:#'registered_data' in HDF_File[sessions[session]].iterkeys():
				print 'Using registered Data'
				dataType = 'registered_data'
			else:
				print 'Using Raw Data'
				dataType = 'raw_data'



			areas = list((i for i in HDF_File[sessions[int(session)]][dataType].iterkeys()))
			for idx,f in enumerate(areas):
				print idx, f 

			areaID = int(raw_input('Select Area Nr:'))
			areaFile = HDF_File[sessions[session]][dataType][areas[areaID]]
            #print '...into function'
			#areaFile.attrs['ROI_patches']
			app = MASK_DRAWER_GUI(areaFile,restart=False)
			#print sys.exit(app.exec_())
		except:
            #raise
            #print 'Something unexpected went wrong! :('
			raise

	print 'HDF_File Closed, PyQt Closed'
