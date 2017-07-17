from marching_cubes import march
import code
import tifffile
import numpy as np
import glob
from numpy import load

from multiprocessing.dummy import Pool as ThreadPool
import subprocess
import threading
import os
import sys
import pickle
import platform

SCALEX = 1.0
SCALEY = 1.0
SCALEZ = 1.0

def findBBDimensions(listOfPixels):
	xs = listOfPixels[0]
	ys = listOfPixels[1]
	zs = listOfPixels[2]

	minxs = min(xs)
	maxxs = max(xs)

	minys = min(ys)
	maxys = max(ys)

	minzs = min(zs)
	maxzs = max(zs)

	dx = maxxs - minxs
	dy = maxys - minys
	dz = maxzs - minzs

	return [minxs, maxxs+1, minys, maxys+1, minzs, maxzs+1], [dx, dy, dz]

def calcMesh(stackname, labelStack, location, simplify):

	indices = np.where(labelStack>0)
	box, dimensions = findBBDimensions(indices)


	window = labelStack[box[0]:box[1], box[2]:box[3], box[4]:box[5]]
	localIndices = np.where(window > 0)

	paddedWindowSizeList = list(window.shape)
	paddedWindowSize = tuple([i+2 for i in paddedWindowSizeList])

	blankImg = np.zeros(paddedWindowSize, dtype=bool)

	blankImg[tuple(([i+1 for i in localIndices[0]], [i+1 for i in localIndices[1]], [i+1 for i in localIndices[2]]))] = 1
	print("Building mesh...")
	vertices, normals, faces = march(blankImg.transpose(), 3)  # zero smoothing rounds
	with open(location + os.path.basename(stackname) +".obj", 'w') as f:
		f.write("# OBJ file\n")

		for v in vertices:
			f.write("v %.2f %.2f %.2f \n" % ((box[0] * SCALEX) + (v[0] * SCALEX), (box[2] * SCALEY) + (v[1] * SCALEY), (box[4] * SCALEZ) + v[2]))
		#for n in normals:
		#	f.write("vn %.2f %.2f %.2f \n" % (n[2], n[1], n[0]))
		for face in faces:
			f.write("f %d %d %d \n" % (face[2]+1, face[1]+1, face[0]+1))
	print("Decimating Mesh...")
	if os.name == 'nt':
		s = './binWindows/simplify ./' + location + os.path.basename(stackname) +".obj ./" + location + os.path.basename(stackname) +".smooth.obj " + str(simplify)
	else:
		if platform.system() == "Darwin":
			s = './binOSX/simplify ./' + location + os.path.basename(stackname) +".obj ./" + location + os.path.basename(stackname) +".smooth.obj " + str(simplify)
		else:
			s = './binLinux/simplify ./' + location + os.path.basename(stackname) +".obj ./" + location + os.path.basename(stackname) +".smooth.obj " + str(simplify)
	print(s)
	subprocess.call(s, shell=True)

def main():
	meshes = sys.argv[2]
	simplify = sys.argv[3]
	alreadyDone = glob.glob(meshes + "*.obj")
	alreadyDone = [os.path.basename(i)[:-4] for i in alreadyDone]

	labelsFolderPath = sys.argv[1]

	labelsPaths = sorted(glob.glob(labelsFolderPath +'*'))
	#code.interact(local=locals())
	for ii,stack in enumerate(labelsPaths):
		if os.path.basename(stack) in alreadyDone:
			print("Detected already processed file. Skipping.")
			print("[Delete file in output folder to reprocess.]")
			continue
		labelStack = tifffile.imread(stack)
		#labelStack = np.dstack(labelStack)
		print("Loaded data stack " + str(ii) + "/" + str(len(labelsPaths)))
		print("Thresholding...")

		calcMesh(stack, labelStack, meshes, simplify)


if __name__ == "__main__":
	main()
