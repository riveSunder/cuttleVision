""" learn to interpret grayscale defocused chromatic aberration as color. This is the fully convolutional version """

#import sys
#sys.path.append('/home/radlr/anaconda3/envs/lVGPU2/lib/python3.6/site-packages')
#hint from https://stackoverflow.com/questions/19876079/opencv-cannot-find-module-cv2
# need the above path append for jupyter notebook implementation


# math etc.
from scipy import misc
import numpy as np

#plotting
import matplotlib as mpl
from matplotlib import pyplot as plt

#image functions, esp. resizing
import cv2
#directory functions
import os

import tensorflow as tf

from tensorflow.contrib import learn
import time

# user-definable flags
FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_integer('maxSteps', 10,
                            """Number of batches to run.""")
tf.app.flags.DEFINE_float('dropout', 0.5,
                            """proportion of weights to drop out.""")
tf.app.flags.DEFINE_float('learningRate', 1e-5,
                            """Learning Rate.""")

tf.app.flags.DEFINE_float('decayRate',.99,"""Save figure at every multiple of this factor""")
tf.app.flags.DEFINE_integer('batchSize', 64,
                            """Minibatch size""")
tf.app.flags.DEFINE_integer('mySeed',1337,"""pseudorandom number gen. seed""")
tf.app.flags.DEFINE_integer('dispIt',2,"""display progress at every multiple of this factor""")
tf.app.flags.DEFINE_integer('saveIt',20,"""Save figure at every multiple of this factor""")

tf.app.flags.DEFINE_integer('convDepth',4,"""Save figure at every multiple of this factor""")



# Set up hyperparameters
convDepth = FLAGS.convDepth
lR = FLAGS.learningRate
dORate = FLAGS.dropout
#epochs = FLAGS.maxSteps
bSize = FLAGS.batchSize
mySeed = FLAGS.mySeed
batchSize = FLAGS.batchSize
maxSteps = FLAGS.maxSteps
dispIt = FLAGS.dispIt
saveIt = FLAGS.saveIt
decayRate = FLAGS.decayRate
#
imgHeight = 512
imgWidth = imgHeight
pool1Size = 2   
pool2Size = 2
kern1Size = 8
kern2Size = 4
kern3Size = 2
kern4Size = 1 


data = tf.placeholder("float",[None, imgHeight,imgWidth,3], name='X')

targets = tf.placeholder("float",[None, imgHeight,imgWidth,3], name='Y')
mode = tf.placeholder("bool",name="myMode")

def cephovision(data,targets,mode):
	# mode = false apply dropout
	# mode = true don't apply dropout, i.e. for evaluation/test
	#input layer is 3 defocused chromatically aberrated images
	inputLayer = tf.reshape(data,[-1,imgHeight,imgWidth,3])
	### Input stack	
	conv1 = tf.layers.conv2d(
        	inputs = inputLayer,
	        filters = convDepth,
        	kernel_size = [kern1Size,kern1Size],
	        padding = "same",
        	activation = tf.nn.tanh,
		name = "conv1")
	dropout1 = tf.layers.dropout(
		inputs = conv1,
		rate = dORate,
		training = mode,
		name = "dropout1")
	
	conv2 = tf.layers.conv2d(
		inputs = dropout1,
		filters = convDepth*2,
		kernel_size = [kern2Size,kern2Size],
		padding = "same",
		activation = tf.nn.tanh,
		name = "conv2")
	dropout2 = tf.layers.dropout(
		inputs = conv2,
		rate = dORate,
		training = mode,
		name = "dropout2")
	conv3 = tf.layers.conv2d(
		inputs = dropout2,
		filters = convDepth*4,
		kernel_size = [kern3Size,kern3Size],
		padding = "same",
		activation = tf.nn.tanh,
		name = "conv3")
	dropout3 = tf.layers.dropout(
		inputs = conv3,
		rate = dORate,
		training = mode,
		name = "dropout3")

	###Synthesis stack
	conv4_ = tf.layers.conv2d_transpose(
		inputs = dropout2,
		filters = convDepth*4, 
		kernel_size = [kern4Size,kern4Size], 
		strides = (1, 1), 
		padding = 'same',
		activation = tf.nn.tanh,
		name = "conv4_")
	dropout4 = tf.layers.dropout(
		inputs = conv4_,
		rate = dORate,
		training = mode,
		name = "dropout4")
	conv5_ = tf.layers.conv2d_transpose(
		inputs = dropout4,
		filters = convDepth*2, 
		kernel_size = [kern3Size,kern3Size], 
		strides = (1, 1), 
		padding = 'same',
		activation = tf.nn.tanh,	
		name = "conv5_")
	dropout5 = tf.layers.dropout(
		inputs = conv5_,
		rate = dORate,
		training = mode,
		name = "dropout5")
	conv6_ = tf.layers.conv2d_transpose(
		inputs = dropout5,
		filters = convDepth, 
		kernel_size = [kern2Size,kern2Size], 
		strides = (1, 1), 
		padding = 'same',
		activation = tf.nn.tanh,
		name = "conv6_")
	dropout6 = tf.layers.dropout(
		inputs = conv6_,
		rate = dORate,
		training = mode,	
		name = "dropout6")
	conv7_ = tf.layers.conv2d_transpose(
		inputs = dropout6,
		filters = 3, 
		kernel_size = [kern1Size,kern1Size], 
		strides = (1, 1), 
		padding = 'same',
		#activation = tf.nn.tanh,
		name = "conv7_")
	myOut = conv7_

	# placeholders
	loss = None
	#trainOp = tf.train.MomentumOptimizer(lR,mom).minimize(loss)
	trainOp = None
	loss = tf.reduce_mean(tf.pow(targets - myOut, 2))
	if mode == True:
				
		trainOp = tf.train.AdamOptimizer(
			learning_rate=lR,beta1=0.9,
			beta2 = 0.999,
			epsilon=1e-08,
			use_locking=False,
			name='Adam').minimize(loss,global_step = tf.contrib.framework.get_global_step())
	
	return myOut #, model_fn_lib.ModelFnOps(mode=mode,loss=loss, train_op=trainOp)


#	tf.layers.dropout(inputs, rate=0.5, noise_shape=None, seed=None, training=False, name=None)

myOut = cephovision(data,targets,mode)
loss = tf.sqrt(tf.reduce_mean(tf.pow(targets - myOut, 2)))
#loss = tf.reduce_mean(targets - myOut)
trainOp = tf.train.AdamOptimizer(
	learning_rate=lR,beta1=0.9,
	beta2 = 0.999,
	epsilon=1e-08,
	use_locking=False,
	name='Adam').minimize(loss,global_step = tf.contrib.framework.get_global_step())

init = tf.global_variables_initializer()
def main(unused_argv):
	with tf.Session() as sess:
		tf.initialize_all_variables().run() # deprecated, but tf.global_variables_initializer doesn't work at all
		lR = FLAGS.learningRate
		# Load the training data
		#myImgs = np.load('./data/simCVTgts/simCVTgts.npy')
		myTgts = np.load('./data/simCVTgts/CVTgts.npy')
		myImgs = np.load('./data/simCVImgs/CVImgs.npy')
		myImgs = myImgs / np.max(myImgs)
		myTgts = myTgts / np.max(myTgts)
		#myTgts = myImgs
		#myImgs = myTgts
		
		# Shuffle data and targets		
		np.random.seed(mySeed)
		np.random.shuffle(myTgts)
		np.random.seed(mySeed)
		np.random.shuffle(myImgs)

		nSamples = np.shape(myTgts)[0]
        

		# Save 10% for the evaluations data set. 
		evalSamples = round(0.1*nSamples)
		testSamples = round(0.2*nSamples)

		# group and normalize the datasets
		trainData = np.array(myImgs[testSamples+1:nSamples,:],dtype="float32")
		trainTgts = np.array(myTgts[testSamples+1:nSamples,:],dtype="float32")
		trainData = (trainData - np.min(trainData) )/ np.max(trainData - np.min(trainData)) 


		evalData = np.array(myImgs[0:evalSamples,:],dtype="float32")
		evalTgts = np.array(myTgts[0:evalSamples,:],dtype="float32")				
		
		testData = np.array(myImgs[evalSamples+1:testSamples,:],dtype="float32")
		testTgts = np.array(myTgts[evalSamples+1:testSamples,:],dtype="float32")           
		testData = (testData - np.min(testData) )/ np.max(testData - np.min(testData)) 
		evalData = (evalData - np.min(evalData) )/ np.max(evalData - np.min(evalData)) 
		

		t = time.time()
		for i in range(maxSteps):

			if( (i) % dispIt == 0):
				start = 0
				end = batchSize
				trainData_ = trainData[start:end]
				trainTgts_ = trainTgts[start:end]
				print("Epoch %i with training cost %.4e and cross-validation cost %.4e " % (i,sess.run(loss, feed_dict={data: trainData_, targets: trainTgts_, mode: False}), sess.run(loss, feed_dict={data: evalData, targets: evalTgts, mode: False}) ))
				print("learning rate decayed to %e" %(lR))
				myElapsed = time.time()-t
				print("elapsed time ", myElapsed, " s")

			if( (i) % saveIt == 0):
				myRandIndex = int(20* np.random.random())
				testXS = evalData[myRandIndex:myRandIndex+2,:]
				testYS = evalTgts[myRandIndex:myRandIndex+2,:]
				#recon = sess.run(ae['y'], feed_dict={ae['x']: test_xs_norm})
				#mask_np = np.random.binomial(1,1, test_xs.shape)
				recon = sess.run(myOut,feed_dict = {data: testXS, targets: testYS, mode: False})
				print(np.shape(testXS))
				print(np.shape(recon))

				fig, axs = plt.subplots(3, 2, figsize=(10,7),dpi=80)
				print("Targets subset >")
				for example_i in range(1):
				#CA monochrome images at different focus (input)
					#axs[0][0+example_i].imshow(cv2.cvtColor(np.reshape(testXS[example_i,...], (imgWidth,imgHeight,3)),cv2.COLOR_BGR2RGB))
					axs[0][0+example_i].imshow(np.reshape(testXS[example_i,:,:,0], (imgWidth,imgHeight)),cmap="gray")
					axs[1][0+example_i].imshow(np.reshape(testXS[example_i,:,:,1], (imgWidth,imgHeight)),cmap="gray")
					axs[2][0+example_i].imshow(np.reshape(testXS[example_i,:,:,2], (imgWidth,imgHeight)),cmap="gray")
					axs[0][0+example_i].set_xticklabels([])
					axs[0][0+example_i].set_yticklabels([])
					axs[1][0+example_i].set_xticklabels([])
					axs[1][0+example_i].set_yticklabels([])
					axs[2][0+example_i].set_xticklabels([])
					axs[2][0+example_i].set_yticklabels([])

					axs[0][0].set_title("Cephalopod View")


					#Color interpretation (prediction)
					axs[0][example_i+1].imshow(cv2.cvtColor(np.reshape(recon[example_i, ...], (imgWidth,imgHeight,3)),cv2.COLOR_BGR2RGB))
					axs[0][example_i+1].set_xticklabels([])
					axs[0][example_i+1].set_yticklabels([])
					axs[0][example_i+1].set_title("Ceph. Color Perception")

					# delete empty subplot
					plt.delaxes(axs[1][example_i+1])

					#Color image (target)
					axs[2][example_i+1].imshow(cv2.cvtColor(np.reshape(testYS[example_i, ...], (imgWidth,imgHeight,3)), cv2.COLOR_BGR2RGB))
					axs[2][example_i+1].set_xticklabels([])
					axs[2][example_i+1].set_yticklabels([])
					
					axs[2][example_i+1].set_title("Trichromat Color")
				#plt.show()
				
				fig.savefig("./training2017Sept28/cephovisionStep%1.iTime%1.i.png" %(i,t))


			for start, end in zip(range(0, len(trainData), batchSize),range(batchSize, len(trainData), batchSize)):
				input_ = trainData[start:end]
				targets_ = trainTgts[start:end]
				#mask_np = np.random.binomial(1,1-corruption_level, input_.shape)
				sess.run(trainOp, feed_dict = {data: input_, targets: targets_, mode: True})
			lR = lR * decayRate
			
		

		
		if (0):
			MTClassifier = learn.Estimator(model_fn = cephovision,
				model_dir = "./model/",
				config=tf.contrib.learn.RunConfig(save_checkpoints_secs=60))

			validationMonitor = tf.contrib.learn.monitors.ValidationMonitor(
				evalData,
				evalTgts,
				every_n_steps=50,
				metrics=loss)

			MTClassifier.fit(x=trainData,
				y=trainTgts,
				batch_size = batchSize,
				steps = maxSteps,
				monitors = [validationMonitor])
		print("test?")

if __name__ == "__main__":
    tf.app.run()



