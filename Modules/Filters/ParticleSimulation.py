	# -*- coding: iso-8859-1 -*-
"""
 Copyright (C) 2005  BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import lib.ProcessingFilter
import vtkbxd
import GUI.GUIBuilder
import lib.FilterTypes
import scripting
import types
import random
import math
import vtk
import os
import codecs
import Logging
import csv
import lib.ParticleReader
import lib.Particle
import lib.ParticleWriter
import lib.Math
import lib.Progress

DIST_UNIFORM = 0
DIST_NORM = 1
DIST_POSNORM = 2
DIST_NEGNORM = 3

class ParticleSimulationFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for generating Particle simulation data
	"""		
	name = "4D particle simulation"
	category = lib.FilterTypes.SIMULATION
	level = scripting.COLOR_EXPERIENCED

	def __init__(self):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.objects = []
		self.readObjects = []
		self.polydata = None
		self.objPolydata = []
		self.timeStamps = []
		self.imageCache = {}
		self.spacing = (1.0, 1.0, 1.0)
		self.voxelSize = (1.0, 1.0, 1.0)
		self.cellCOM = None
		self.modified = 1
		self.progressObj = lib.Progress.Progress()
		self.descs = {"X":"X:", "Y":"Y:", "Z":"Z:","Time":"Number of timepoints",
		"Coloc":"Create colocalization between channels", 
		"ColocAmountStart":"Coloc. amnt (at start)",
		"ColocAmountEnd":"Coloc. amnt (at end)",
		#"Shift":"Create shift in the data",
		#"ShiftStart":"Min. shift (in x,y px size):",
		#"ShiftEnd":"Max. shift (in x,y px size)",
		"ShotNoiseAmount":"% of shot noise",
		"ShotNoiseMin":"Min. intensity of shot noise",
		"ShotNoiseMax":"Max. intensity of shot noise",
		"ShotNoiseDistribution":"Shot noise distribution",
		#"BackgroundNoiseAmount":"% of background noise",
		"BackgroundNoiseMin":"Min. intensity of bg noise",
		"BackgroundNoiseMax":"Max. intensity of bg noise",
		"NumberOfObjectsStart":"# objects (at least)",
		"NumberOfObjectsEnd":"# of objects (at most)",
		"ObjSizeStart":"Min. size of object (in px)",
		"ObjSizeEnd":"Max. size of object (in px)",
		"ObjSizeDistribution":"Size distribution",
		#"ObjectFluctuationStart":"Min. change in object #",
		#"ObjectFluctuationEnd":"Max. change in object #",
		"ObjMinInt":"Min. intensity of objects at the first time point",
		"ObjMaxInt":"Max. intensity of objects at the first time point",
		"IntChange":"Max. intensity change (in %)",
		"RandomMovement":"Move randomly",
		"MoveTowardsPoint":"Move towards a point",
		"MovePercentage":"% of objects move towards point",
		"TargetPoints":"# of target points",
		"Clustering":"Objects should cluster",
		"SpeedStart":"Obj. min speed (in x,y px size)",
		"SpeedEnd":"Obj. max speed (in x,y px size)",
		"SizeChange":"Max. size change (in %)",
		"ClusterPercentage":"% of objects cluster",
		"ClusterDistance":"Max. distance for clustering (in x,y px size)",
		"Cache":"Cache timepoints",
		"CacheAmount":"# of timepoints cached",
		"CreateAll":"Create all timepoints at once",
		"CreateNoise":"Create noise",
		"ReadObjects":"Read sizes and number from",
		"ObjectsCreateSource":"Create objects close to surface from source",
		"SigmaDistSurface":"Sigma of Gaussian distance to surface (in x,y px size)",
		"TimeDifference":"Time difference between time points",
		"TargetPointsInside":"Target points inside radius (in x,y px size)"}

		self.filterDesc = "Generate 4D particle simulation data. In addition to image data, produces also ground truth object and track statistics.\nInput: None (optional cell surface)\nOutput: Grayscale image"
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [ ["Caching",("Cache","CacheAmount","CreateAll")],["Dimensions",("X","Y","Z","Time","TimeDifference")],#["Shift", ("Shift","ShiftStart","ShiftEnd")],
			["Noise",("CreateNoise","ShotNoiseAmount","ShotNoiseMin","ShotNoiseMax","ShotNoiseDistribution","BackgroundNoiseMin","BackgroundNoiseMax")],
			["Objects",(("ReadObjects", "Select object statistics file", "*.csv"),"NumberOfObjectsStart","NumberOfObjectsEnd","ObjSizeStart","ObjSizeEnd","ObjSizeDistribution","SizeChange","ObjMinInt","ObjMaxInt","IntChange","ObjectsCreateSource", "SigmaDistSurface")],#"ObjectFluctuationStart","ObjectFluctuationEnd",
			#["Colocalization",("Coloc","ColocAmountStart","ColocAmountEnd")],
			["Movement strategy",("RandomMovement","MoveTowardsPoint","TargetPoints","TargetPointsInside","MovePercentage","SpeedStart","SpeedEnd")],
			["Clustering",("Clustering","ClusterPercentage","ClusterDistance")],
		]
		
	def setParameter(self, parameter, value):
		"""
		An overriden method for setting the parameter value, used to catch and set the number
		of timepoints
		"""
		if self.parameters.get(parameter)!=value:
			self.modified = 1
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)
		if parameter in ["Time", "X", "Y", "Z"]:
			if self.dataUnit:
				self.dataUnit.setNumberOfTimepoints(self.parameters["Time"])
				self.dataUnit.setModifiedDimensions((self.parameters["X"], self.parameters["Y"], self.parameters["Z"]))
				lib.messenger.send(None, "update_dataset_info")
				
	def onRemove(self):
		"""
		A callback for stuff to do when this filter is being removed.
		"""
		if self.dataUnit:
			self.dataUnit.setModifiedDimensions(None)
				
	def getLongDesc(self, parameter):
		"""
		Return a long description of the parameter
		""" 
		return ""
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["ShotNoiseAmount","ClusteringPercentage","SigmaDistSurface","TimeDifference"]:
			return types.FloatType
		if parameter in ["X","Y","Z","ShiftStart","ShiftEnd","ObjMinInt","ObjMaxInt"]:
			return types.IntType
		if parameter in ["CreateNoise","Coloc","Shift","RandomMovement","MoveTowardsPoint","Clustering","Cache","CreateAll","ObjectsCreateSource"]:
			return types.BooleanType
		if parameter == "ReadObjects":
			return GUI.GUIBuilder.FILENAME
		if parameter in ["ShotNoiseDistribution","ObjSizeDistribution"]:
			return GUI.GUIBuilder.CHOICE
			
		return types.IntType
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""		
		if parameter in ["X","Y"]: return 512
		if parameter == "Cache": return True
		if parameter == "CacheAmount": return 15
		if parameter == "CreateAll": return True
		if parameter == "Z": return 25
		if parameter == "TargetPoints": return 1
		if parameter == "Time": return 15
		if parameter == "Clustering": return True
		if parameter == "ColocAmountStart": return 1
		if parameter == "ClusterPercentage": return 20
		if parameter == "ClusterDistance":return 30
		if parameter == "ColocAmountEnd": return 50
		if parameter == "MoveTowardsPoint":return True
		if parameter == "MovePercentage": return 30
		if parameter == "ShotNoiseAmount": return 0.1
		if parameter == "ShotNoiseMin": return 128
		if parameter == "ShotNoiseMax": return 255
		if parameter == "ShotNoiseDistribution": return 0
		if parameter == "SizeChange": return 5
		if parameter == "SpeedStart": return 2
		if parameter == "SpeedEnd": return 10
		#if parameter == "BackgroundNoiseAmount": return 5
		if parameter == "BackgroundNoiseMin": return 1
		if parameter == "BackgroundNoiseMax": return 30
		if parameter == "NumberOfObjectsStart":return 20
		if parameter == "NumberOfObjectsEnd": return 200
		if parameter == "ObjectFluctuationStart": return 0
		if parameter == "ObjectFluctuationEnd": return 0
		if parameter == "ObjSizeStart": return 5
		if parameter == "ObjSizeEnd": return 50
		if parameter == "ObjSizeDistribution": return 0
		if parameter == "ObjMinInt": return 200
		if parameter == "ObjMaxInt": return 255
		if parameter == "IntChange": return 5
		if parameter == "ReadObjects": return "statistics.csv"
		if parameter == "ObjectsCreateSource": return False
		if parameter == "SigmaDistSurface": return 5.0
		if parameter == "TimeDifference": return 300.0
		if parameter == "TargetPointsInside": return 0
		
		# Shift of 1-5% per timepoint
		if parameter == "ShiftStart": return 1
		if parameter == "ShiftEnd": return 15
		return 0

	def getRange(self, param):
		"""
		Return range of list parameter
		"""
		if param in ["ShotNoiseDistribution","ObjSizeDistribution"]:
			return ("Uniform distribution", "Normal distribution","Positive normal distribution","Negative normal distribution")
		
	def createTimeSeries(self):
		"""
		Create a time series of configurations that correspond to the current parameters
		"""
		self.modified = 0
		x,y,z = self.parameters["X"],self.parameters["Y"], self.parameters["Z"]
		self.majorAxis = random.randint(int(0.55*y), int(0.85*y))
		
		for image in self.imageCache.values():
			image.ReleaseData()
		
		self.imageCache = {}
		self.jitters = []
		self.shifts = []
		self.objects = []
		
		shiftDir=[0,0,0]
		shiftAmnt = 0
		for tp in range(0, self.parameters["Time"]):
			#if self.parameters["Shift"]:
			#	print "Creating shift amounts for timepoint %d"%tp
				# If shifting is requested, then in half the cases, create some jitter
				# meaning shift of 1-5 pixels in X and Y and 0-1 pixels in Z
			#	if random.random() < 0.5:
			#		jitterx = random.randint(1,5)
			#		jittery = random.randint(1,5)
			#		jitterz = random.randint(0,1)
			#		self.jitters.append((jitterx, jittery, jitterz))
				
				# If we're in the middle of a shift, then continue to that direction
			#	if shiftAmnt > 0:
			#		shiftx = shiftDir[0]*random.randint(self.parameters["ShiftStart"], self.parameters["ShiftEnd"])
			#		shifty = shiftDir[1]*random.randint(self.parameters["ShiftStart"], self.parameters["ShiftEnd"])
			#		shiftz = shiftDir[2]*random.randint(self.parameters["ShiftStart"], self.parameters["ShiftEnd"])
			#		self.shifts.append((shiftx, shifty, shiftz))
			#		shiftAmnt -= 1
				# If no shift is going on, then create a shift in some direction
			#	else:
			#		shiftAmnt = random.randint(2, 4)
					# There's a 50% chance that there's no shift, and 2x25% chance of the shift being
					# in either direction
			#		shiftDir[0] = random.choice([-1,0,0,1])
			#		shiftDir[1] = random.choice([-1,0,0,1])
					# there's 60% chance of having shift in z dir
			#		shiftDir[2] = random.choice([-1,-1,-1,0,0,0,0,1,1,1])
					
				
				# in 5% of cases, create a jolt of 2 to 5 px in z direction 
			#	if random.random() < 0.05:
			#		direction = random.choice([-1,1])
			#		x,y,z = self.shifts[-1]
			#		z += random.randint(2,5)*direction
			#		if len(shifts) == 1:
			#			pass
			#		else:
			#			self.shifts[-1] = (x,y,z)
			#else:
			#	self.shifts.append((0,0,0))
				
			print "Creating objects for timepoint %d"%tp
			objs = self.createObjectsForTimepoint(tp)

			#if self.parameters["ObjectFluctuationEnd"]:
			#	print "Adding fluctuations to object numbers"
			#	objs = self.createFluctuations(objs)
			self.objects.append(objs)

		clusteredObjects = []
		if self.parameters["Clustering"]:
			print "Introducing clustering"
			clusteredObjects = self.clusterObjects(self.objects)
		
		# Sort objects
		for tpObjs in self.objects:
			tpObjs.sort()
		
		self.tracks = []
		for tp, objs in enumerate(self.objects):
			for i, (objN, (x,y,z), size, objInt) in enumerate(objs):
				if len(self.tracks) < objN:
					self.tracks.append([])
				p = lib.Particle.Particle((x,y,z), (x,y,z), tp, size, objInt, objN)
				p.setVoxelSize(self.voxelSize)
				self.tracks[objN-1].append(p)
			# Set same particle in track of clustered particles
			for ctp,objN,clusObj in clusteredObjects:
				if tp == ctp:
					p = lib.Particle.Particle(clusObj[1], clusObj[1], ctp, clusObj[2], clusObj[3], clusObj[0])
					p.setVoxelSize(self.voxelSize)
					self.tracks[objN-1].append(p)


		if self.parameters["ObjectsCreateSource"]:
			for tp, objs in enumerate(self.objects):
				self.objPolydata.append([])
	
	def clusterObjects(self, objects):
		"""
		Create clustering of objects
		"""
		combine = []
		clustered = {}
		#clusteredObjN = {}
		removedByTP = []
		for remtp in range(len(self.objects)):
			removedByTP.append(0)
		
		for tp,objs in enumerate(objects):
			if tp == 0: continue
			toremove = []
			toadd = {}
			#combine = []
			for i, (objN1, (x1,y1,z1), size1, objInt1) in enumerate(objs):
				for j, (objN2, (x2,y2,z2), size2, objInt2) in enumerate(objs):
					if objN1 == objN2: continue
					#if objN in clusteredObjN: continue
					#if objN2 in clusteredObjN: continue
					if (tp,objN1) in clustered or (tp,objN2) in clustered: continue
					d = math.sqrt(((x2-x1) * self.spacing[0])**2 + ((y2-y1) * self.spacing[1])**2 + ((z2-z1) * self.spacing[2])**2)
					if d < self.parameters["ClusterDistance"]:
						if random.random()*100 < self.parameters["ClusterPercentage"]:
							# Mark as combined in this and coming time points
							#for combTP in range(tp,len(objects)):
							#	combine.append((combTP,objN,i,objN2,j))
							#combine.append((objN,i,objN2,j))
							#clustered[(tp,objN2)] = 1
							#clustered[(tp,objN)] = 1
							#clusteredObjN[objN]=1
							#clusteredObjN[objN2]=1
							size3 = int((size1+size2)*0.7)
							x3 = (x1+x2)/2
							y3 = (y1+y2)/2
							z3 = (z1+z2)/2
							int3 = int((objInt1+objInt2) * 0.7)
							#toadd.append((objN1, (x3,y3,z3), size3, int3))
							if size1 >= size2:
								toadd[objN1] = (objN1,(x3-x1,y3-y1,z3-z1), size3, int3)
								combine.append((tp,objN2,(objN1, (x3,y3,z3), size3, int3)))
							else:
								toadd[objN2] = (objN2,(x3-x2,y3-y2,z3-z2), size3, int3)
								combine.append((tp,objN1,(objN2, (x3,y3,z3), size3, int3)))
							toremove.append(objN1)
							toremove.append(objN2)
							clustered[(tp,objN1)] = 1
							clustered[(tp,objN2)] = 1

			for remTP in range(tp, len(objects)):
				for remObj in objects[remTP]:
					if remObj[0] in toremove:
						objects[remTP].remove(remObj)
						removedByTP[remTP] += 1
						if toadd.get(remObj[0],False):
							addObj = toadd.get(remObj[0])
							loc = list(addObj[1])
							for dim in range(3):
								loc[dim] += remObj[1][dim]
							addObj = (addObj[0], tuple(loc), addObj[2], addObj[3])
							objects[remTP].append(addObj)
							removedByTP[remTP] -=1

			#for addObj in toadd:
			#	objects[tp].append(addObj)
			#	removedByTP[tp] -= 1

			#for objN,i,objN2,j in combine:
			#	ob1 = objects[tp][i]
			#	ob2 = objects[tp][j]
			#	toremove.append((ob1,ob2))
			#	objN,(x1,y1,z1),s1,int1 = ob1
			#	objN2,(x2,y2,z2),s2,int2 = ob2
			#	s3 = int((s1+s2)*0.7)
			#	x3 = (x1+x2)/2
			#	y3 = (y1+y2)/2
			#	z3 = (z1+z2)/2
			#	int3 = int((int1+int2) * 0.7)
			#	objects[tp].append((objN,(x3,y3,z3), s3, int3))
			
			#for ob1,ob2 in toremove:
			#	objects[tp].remove(ob1)
			#	objects[tp].remove(ob2)
			#	removedByTP[tp] += 1

		#toremove=[]
		#for tp,objN,i,objN2,j in combine:
		#	ob1 = objects[tp][i]
		#	ob2 = objects[tp][j]
			#if len(self.tracks[objN-1]) > tp and len(self.tracks[objN2-1]) > tp:
			#	self.tracks[objN-1].remove(self.tracks[objN-1][tp])
			#	self.tracks[objN2-1].remove(self.tracks[objN2-1][tp])
		#	toremove.append((tp,ob1,ob2))
		#	objN,(x1,y1,z1),s1,int1 = ob1
		#	objN2,(x2,y2,z2),s2,int2 = ob2
		#	s3 = int((s1+s2)*0.7)
		#	x3 = (x1+x2)/2
		#	y3 = (y1+y2)/2
		#	z3 = (z1+z2)/2
		#	int3 = int((int1+int2) * 0.7)
		#	objects[tp].append((objN,(x3,y3,z3), s3, int3))
			#self.tracks[objN-1].insert(tp, lib.Particle.Particle((x3,y3,z3), (x3,y3,z3), tp, size, int3, objN))

		#for tp,ob1,ob2 in toremove:
		#	objects[tp].remove(ob1)
		#	objects[tp].remove(ob2)
		#	removedByTP[tp] += 1

		for remtp in range(len(self.objects)):
			print "Removed from timepoint %d: %d"%(remtp,removedByTP[remtp])
		return combine
	
	def createFluctuations(self, objects):
		"""
		Create fluctuations in the number of objects
		"""
		removeN = random.randint(self.parameters["ObjectFluctuationStart"],self.parameters["ObjectFluctuationEnd"])
		addN = random.randint(self.parameters["ObjectFluctuationStart"],self.parameters["ObjectFluctuationEnd"])
		
		for i in range(0, removeN):
			obj = random.choice(objects)
			objects.remove(obj)
		print "Removed",removeN,"objects"
		for i in range(0, addN):
			objects.append(self.createObject())
		print "Added",addN,"objects"
		
	def createObjectsForTimepoint(self, tp):
		"""
		Create objects for given timepoint
		"""
		objs = []
		x,y,z = self.parameters["X"], self.parameters["Y"], self.parameters["Z"]
		coeff = z/float(x)
		if tp == 0:
			if self.parameters["MoveTowardsPoint"]:
				self.towardsPoints = []
				for c in range(0, self.parameters["TargetPoints"]):
					print "Getting point toward which to move"
					rx, ry, rz = self.getPointInsideCell()
					if self.parameters["TargetPointsInside"] > 0 and len(self.towardsPoints) > 0:
						firstX,firstY,firstZ = self.towardsPoints[0]
						while math.sqrt((rx-firstX)**2 + (ry-firstY)**2 + ((rz-firstZ)*self.spacing[2])**2) > self.parameters["TargetPointsInside"]:
							rx, ry, rz = self.getPointInsideCell()
					print "it's",rx,ry,rz
					self.towardsPoints.append((rx,ry,rz))

			if self.readObjects:
				self.numberOfObjects = len(self.readObjects)
			else:
				self.numberOfObjects = random.randint(self.parameters["NumberOfObjectsStart"],self.parameters["NumberOfObjectsEnd"])
			
			for obj in range(1, self.numberOfObjects+1):
				self.createObject(obj,objs)
		else:
			for objN, objCom, size, objInt in self.objects[tp-1]:
				rx,ry,rz = objCom
				if self.parameters["MoveTowardsPoint"] and random.random() < self.parameters["MovePercentage"] / 100.0:
					nearest = None
					smallest = 2**31
					for (x,y,z) in self.towardsPoints:
						d = math.sqrt(((x-rx) * self.spacing[0])**2 + ((y-ry) * self.spacing[1])**2 + ((z-rz) * self.spacing[2])**2)
						if d < smallest:
							smallest = d
							nearest = (x,y,z)

					direction = [nearest[i] - objCom[i] for i in range(3)]
					length = 0.0
					for i in range(3):
						length += direction[i]*direction[i]
					length = math.sqrt(length)
					direction = [i / length for i in direction]
					speed = random.randint(self.parameters["SpeedStart"], self.parameters["SpeedEnd"])
					speedx = direction[0] * speed
					speedy = direction[1] * speed
					speedz = direction[2] * speed * coeff
					
					#speedx = random.randint(self.parameters["SpeedStart"], self.parameters["SpeedEnd"])
					#speedy = random.randint(self.parameters["SpeedStart"], self.parameters["SpeedEnd"])
					#speedz = coeff*random.randint(self.parameters["SpeedStart"], self.parameters["SpeedEnd"])
					#if rx > nearest[0]:
					#	speedx *= -1
					#if ry > nearest[1]:
					#	speedy *= -1
					#if rz > nearest[2]:
					#	speedz *= -1
				elif self.parameters["RandomMovement"] or self.parameters["MoveTowardsPoint"]:
					#speedx = random.choice([-1,1])*random.randint(self.parameters["SpeedStart"], self.parameters["SpeedEnd"])
					#speedy = random.choice([-1,1])*random.randint(self.parameters["SpeedStart"], self.parameters["SpeedEnd"])
					#speedz = random.choice([-1,1])*coeff*random.randint(self.parameters["SpeedStart"], self.parameters["SpeedEnd"])
					direction = []
					direction.append(random.choice([-1,1]) * random.random())
					direction.append(random.choice([-1,1]) * random.random())
					direction.append(random.choice([-1,1]) * coeff * random.random())
					length = 0.0
					for i in range(3):
						length += direction[i]*direction[i]
					length = math.sqrt(length)
					direction = [i / length for i in direction]
					speed = random.randint(self.parameters["SpeedStart"], self.parameters["SpeedEnd"])
					speedx = direction[0] * speed
					speedy = direction[1] * speed
					speedz = direction[2] * speed
				
				rx += speedx
				ry += speedy
				rz += speedz
				if rx < 0: rx = 0
				if ry < 0: ry = 0
				if rz < 0: rz = 0
				if rx > self.parameters["X"] - 1: rx = self.parameters["X"] - 1
				if ry > self.parameters["Y"] - 1: rx = self.parameters["Y"] - 1
				if rz > self.parameters["Z"] - 1: rx = self.parameters["Z"] - 1
				
				if self.parameters["SizeChange"]:
					negative = 1.0
					maxchange = int(round(size*(self.parameters["SizeChange"]/100.0)))

					if maxchange < 0:
						negative = -1
					change = random.randint(0, maxchange)
					change *= negative
					size += change

				if self.parameters["IntChange"]:
					negative = 1.0
					maxchange = int(round(objInt*(self.parameters["IntChange"]/100.0)))
					if maxchange < 0:
						negative = -1
					change = random.randint(0, maxchange)
					change *= negative
					objInt += change

				objs.append((objN, (rx,ry,rz), size, objInt))
		return objs
		
	def createObject(self, objNum, objs):
		print "Creating object %d"%objNum
		if self.readObjects:
			size = self.readObjects[objNum-1][0][0]
		else:
			sizeStart = self.parameters["ObjSizeStart"]
			sizeEnd = self.parameters["ObjSizeEnd"]
			sizeDistr = self.parameters["ObjSizeDistribution"]
			size = self.generateDistributionValue(sizeDistr, sizeStart, sizeEnd)

		if self.parameters["ObjectsCreateSource"]:
			rx, ry, rz = self.getPointCloseToSurface()
		else:
			rx, ry, rz = self.getPointInsideCell()

		# Select intensity for object, voxel intensity will be -5% to +5%
		objInt = random.randint(self.parameters["ObjMinInt"],self.parameters["ObjMaxInt"])
		objs.append((objNum, (rx,ry,rz), size, objInt))
		
	def getPointInsideCell(self):
		x,y,z = self.parameters["X"],self.parameters["Y"], self.parameters["Z"]
		while 1:
			# Set couple pixel buffer
			rx,ry,rz = random.randint(6,x-7), random.randint(6,y-7), random.randint(6,z-7)
			if self.pointInsideEllipse((rx,ry,rz), self.majorAxis):
				break
		return rx,ry,rz
		
	def createData(self, currentTimepoint):
		"""
		Create a test dataset within the parameters defined
		"""
		x,y,z = self.parameters["X"], self.parameters["Y"], self.parameters["Z"]
		if self.modified:
			print "Creating the time series data"
			self.createTimeSeries()
			if self.parameters["CreateAll"]:
				n = min(self.parameters["CacheAmount"], self.parameters["Time"])
				for i in range(0, n):
					if i == currentTimepoint: 
						print "Won't create timepoint %d, it'll be last"%i
						continue
					self.createData(i)

		print "\n\nGenerating timepoint %d"%currentTimepoint
		
		if currentTimepoint in self.imageCache:
			print "Returning cached image"
			return self.imageCache[currentTimepoint]

		print "Allocating image"

		if self.parameters["CreateNoise"]:
			print "Creating background noise"
			noiseSource = vtk.vtkImageNoiseSource()
			noiseSource.SetWholeExtent(0,x-1,0,y-1,0,z-1)
			noiseSource.SetMinimum(self.parameters["BackgroundNoiseMin"])
			noiseSource.SetMaximum(self.parameters["BackgroundNoiseMax"])
			castFilter = vtk.vtkImageCast()
			castFilter.SetOutputScalarTypeToUnsignedChar()
			castFilter.SetInputConnection(noiseSource.GetOutputPort())
			information = vtk.vtkImageChangeInformation()
			information.SetInputConnection(castFilter.GetOutputPort())
			information.SetOutputSpacing(self.spacing)
			image = information.GetOutput()
			image.Update()
		else:
			image = vtk.vtkImageData()
			image.SetScalarTypeToUnsignedChar()
			x,y,z = self.parameters["X"], self.parameters["Y"], self.parameters["Z"]
			image.SetDimensions((x,y,z))
			image.AllocateScalars()
			image.SetSpacing(self.spacing)
			
			print "Initializing image"
			for iz in range(0,z):
				for iy in range(0,y):
					for ix in range(0,x):
						image.SetScalarComponentFromDouble(ix,iy,iz,0,0)

		if self.parameters["CreateNoise"]:
			noisePercentage = self.parameters["ShotNoiseAmount"]
			noiseAmount = (noisePercentage/100.0) * (x*y*z)
			print "Creating shot noise"
		else:
			noiseAmount = 0

		shotNoiseMin = self.parameters["ShotNoiseMin"]
		shotNoiseMax = self.parameters["ShotNoiseMax"]
		shotNoiseDistr = self.parameters["ShotNoiseDistribution"]

		while noiseAmount > 0:
			rx,ry,rz = random.randint(0,x-1), random.randint(0,y-1), random.randint(0,z-1)
			shotInt = self.generateDistributionValue(shotNoiseDistr, shotNoiseMin, shotNoiseMax)				
			image.SetScalarComponentFromDouble(rx,ry,rz,0,shotInt)
			noiseAmount -= 1

		#shiftx, shifty, shiftz = self.shifts[currentTimepoint]
		
		print "Creating objects",currentTimepoint
		for oIter, (objN, (rx,ry,rz), size, objInt) in enumerate(self.objects[currentTimepoint]):
			#rx += shiftx
			#ry += shifty
			#rz += shiftz

			(rx,ry,rz), realSize, intList, voxelList = self.createObjectAt(image, rx,ry,rz, size, objInt)
			objMean, objStd, objStdErr = lib.Math.meanstdeverr(intList)
			# Change possible new size and com to object
			self.objects[currentTimepoint][oIter] = (objN, (rx,ry,rz), realSize, (objMean, objStdErr), voxelList)

		if self.parameters["ObjectsCreateSource"]:
			locator = vtk.vtkOBBTree()
			locator.SetDataSet(self.polydata)
			locator.BuildLocator()
			pointLocator = vtk.vtkPointLocator()
			pointLocator.SetDataSet(self.polydata)
			pointLocator.BuildLocator()
			objPolyTP = []
			for objN, (cx, cy, cz), size, meanInt, voxelList in self.objects[currentTimepoint]:
				cxs = cx * self.spacing[0]
				cys = cy * self.spacing[1]
				czs = cz * self.spacing[2]
				locatorInside = locator.InsideOrOutside((cxs,cys,czs))
				if locatorInside == -1:
					inside = 1
				else:
					inside = 0
				
				percVoxelsInside = 0.0
				numIn = 0
				for (vx,vy,vz) in voxelList:
					vxs = vx * self.spacing[0]
					vys = vy * self.spacing[1]
					vzs = vz * self.spacing[2]
					locatorInside = locator.InsideOrOutside((vxs,vys,vzs))
					if locatorInside == -1:
						numIn += 1
				percVoxelsInside = float(numIn) / len(voxelList)

				objid = pointLocator.FindClosestPoint((cxs, cys, czs))
				x2,y2,z2 = self.polydata.GetPoint(objid)
				x2 /= self.spacing[0]
				y2 /= self.spacing[1]
				z2 /= self.spacing[2]

				distToSurf = self.distance((cx,cy,cz), (x2,y2,z2), self.voxelSize)
				distToCom = self.distance((cx,cy,cz), self.cellCOM, self.voxelSize)
				objPolyTP.append((objN, (cx,cy,cz), distToSurf, distToCom, inside, percVoxelsInside))
			self.objPolydata[currentTimepoint] = objPolyTP
		
		n = len(self.imageCache.items())
		if n > self.parameters["CacheAmount"]:
			items = self.imageCache.keys()
			items.sort()
			print "Removing ", items[0], "from cache"
			self.imageCache[items[0]].ReleaseData()
			del self.imageCache[items[0]]
		self.imageCache[currentTimepoint] = image

		self.progressObj.setProgress(currentTimepoint/self.parameters["Time"])
		self.updateProgress(None, "ProgressEvent")

		return image
		
	def pointInsideEllipse(self, pt, majorAxis, f1 = None, f2 = None):
		"""
		@param pt Point to be tested
		@param majorAxis Length of the major axis of ellipse
		@param f1, f2 optional focal points of the ellipse
		@return true if given point is inside the ellipse
		"""
		rx,ry,rz = pt
		x,y,z = self.parameters["X"], self.parameters["Y"], self.parameters["Z"]
		dx = (y-majorAxis)/2
		#print "Testing",rx,ry,rz,"major axis=",self.majorAxis
		if not f1:
			f1y = 2*dx
			f1x = x/2
		else:
			f1x,f1y = f1
		if not f2:
			f2y = y-(2*dx)
			f2x = x/2
		else:
			f2x,f2y = f2
			
		p1 = (f1x-rx,f1y-ry)
		p2 = (f2x-rx,f2y-ry)
		d1 = math.sqrt(p1[0]*p1[0]+p1[1]*p1[1])+math.sqrt(p2[0]*p2[0]+p2[1]*p2[1])
		return d1 < majorAxis
		
	def createObjectAt(self, imageData, x0, y0, z0, size, objInt):
		"""
		Create an object in the image at the give position
		@param imageData the image to modify
		@param x0, y0, z0 the coordinates of the object
		@param size the size of the object in pixels
		"""
		origr = math.pow(size*0.23561944901923448, 0.333333)
		#r = int(1+math.sqrt(size/math.pi))
		#r = int(round(origr))
		#if r < 1:
		#	r = 1
		maxx,maxy,maxz = imageData.GetDimensions()
		minx,miny,minz = [0 for i in range(3)]
		maxx -= 1
		maxy -= 1
		maxz -= 1

		xs = x0-origr
		ys = y0-origr
		zs = z0-origr
		xe = x0+origr
		ye = y0+origr
		ze = z0+origr
		xsInt = int(math.ceil(xs))
		ysInt = int(math.ceil(ys))
		zsInt = int(math.ceil(zs))
		xeInt = int(math.floor(xe))
		yeInt = int(math.floor(ye))
		zeInt = int(math.floor(ze))

		# Be sure that whole object is inside image range
		if xsInt < minx:
			xeInt += (minx - xsInt)
			xsInt = 0
			x0 = (xeInt + xsInt) / 2.0
		if ysInt < miny:
			yeInt += (miny - ysInt)
			ysInt = 0
			y0 = (yeInt + ysInt) / 2.0
		if zsInt < minz:
			zeInt += (minz - zsInt)
			zsInt = 0
			z0 = (zeInt + zsInt) / 2.0
		if xeInt > maxx:
			xsInt -= (xeInt - maxx)
			xeInt = maxx
			x0 = (xeInt + xsInt) / 2.0
		if yeInt > maxy:
			ysInt -= (yeInt - maxy)
			yeInt = maxy
			y0 = (yeInt + ysInt) / 2.0
		if zeInt > maxz:
			zsInt -= (zeInt - maxz)
			zeInt = maxz
			z0 = (zeInt + zsInt) / 2.0

		# Create only core and randomize other voxels
		coreSize = (xeInt-xsInt)*(yeInt-ysInt)*(zeInt-zsInt)
		if coreSize > size:
			xeInt -= 1
			xsInt += 1
			yeInt -= 1
			ysInt += 1
			zeInt -= 1
			zsInt += 1

		# Calculate approximation of area of object to be created
		#a = ((xe-xs)/2.0) * self.voxelSize[0] * 1000000 # convert to um
		#b = ((ye-ys)/2.0) * self.voxelSize[1] * 1000000 # convert to um
		#c = ((ze-zs)/2.0) * self.voxelSize[2] * 1000000 # convert to um
		#ap = a**1.6
		#bp = b**1.6
		#cp = c**1.6
		#area = 4*math.pi*((ap*bp + ap*cp + bp*cp)/3)**(1/1.6)
		
		count = 0
		intList = []
		totalInt = 0.0
		coms = [0.0, 0.0, 0.0]
		# Select intensity for object, voxel intensity will be -5% to +5%
		minInt = int(round(0.95 * objInt))
		if minInt < 0: minInt = 0
		if minInt > 255: minInt = 255
		maxInt = int(round(1.05 * objInt))
		if maxInt < 0: maxInt = 20
		if maxInt > 255: maxInt = 255

		voxelList = []
		for x in range(xsInt,xeInt+1):
			for y in range(ysInt,yeInt+1):
				for z in range(zsInt,zeInt+1):
					# Do not use spacing to get real looking objects
					d = math.sqrt((x0-x)**2 + (y0-y)**2 + (z0-z)**2)
					if d <= origr:
						voxelInt = random.randint(minInt,maxInt)
						imageData.SetScalarComponentFromDouble(x,y,z,0,voxelInt)
						count += 1
						intList.append(voxelInt)
						totalInt += voxelInt
						coms[0] += voxelInt * x
						coms[1] += voxelInt * y
						coms[2] += voxelInt * z
						voxelList.append((x,y,z))

		if count < size: # Mark some random pixels
			maxTry = 100
			while count < size and maxTry > 0:
				maxTry -= 1
				xRand = random.choice(range(xsInt-1,xeInt+2))
				yRand = random.choice(range(ysInt-1,yeInt+2))
				zRand = random.choice(range(zsInt-1,zsInt+2))
				if (xRand,yRand,zRand) not in voxelList and xRand >= 0 and xRand <= maxx and yRand >= 0 and yRand <= maxy and zRand >= 0 and zRand <= maxz and ((xRand-1,yRand,zRand) in voxelList or (xRand+1,yRand,zRand) in voxelList or (xRand,yRand-1,zRand) in voxelList or (xRand,yRand+1,zRand) in voxelList or (xRand,yRand,zRand-1) in voxelList or (xRand,yRand,zRand+1) in voxelList):
					voxelInt = random.randint(minInt,maxInt)
					imageData.SetScalarComponentFromDouble(xRand,yRand,zRand,0,voxelInt)
					count += 1
					intList.append(voxelInt)
					totalInt += voxelInt
					coms[0] += voxelInt * xRand
					coms[1] += voxelInt * yRand
					coms[2] += voxelInt * zRand
					voxelList.append((xRand,yRand,zRand))

		x0, y0, z0 = [coms[i] / (totalInt) for i in range(3)]
		return (x0,y0,z0), count, intList, voxelList

	def getPointCloseToSurface(self):
		"""
		Select random point close to surface provided by user as parameter
		"""
		numOfPolys = self.polydata.GetNumberOfPolys()
		randPolyID = random.randint(0, numOfPolys-1)
		pdata = self.polydata.GetPolys().GetData()
		pointIDs = [int(pdata.GetTuple1(i)) for i in range(4*randPolyID+1,4*randPolyID+4)]
		points = [self.polydata.GetPoint(i) for i in pointIDs]
		# Calculate center of random polygon
		center = [0.0, 0.0, 0.0]
		for point in points:
			for i in range(3):
				center[i] += point[i] / self.spacing[i]

		for i in range(3):
			center[i] = center[i] / 3

		sigma = self.parameters["SigmaDistSurface"]
		randomCOM = [random.gauss(center[i], sigma / self.spacing[i]) for i in range(3)]
		dims = (self.parameters["X"], self.parameters["Y"], self.parameters["Z"])

		for i in range(3):
			if randomCOM[i] < 0:
				randomCOM[i] = 0
			elif randomCOM[i] > dims[i] - 1:
				randomCOM[i] = dims[i] - 1

		return tuple(randomCOM)
		

	def writeOutput(self, dataUnit, timepoint):
		"""
		Optionally write the output of this module during the processing
		"""
		fileroot = self.dataUnit.getName()
		bxddir = dataUnit.getOutputDirectory()
		fileroot = os.path.join(bxddir, fileroot)
		filename = "%s.csv" % fileroot
		self.writeToFile(filename, dataUnit, timepoint)
		
	def writeToFile(self, filename, dataUnit, timepoint):
		"""
		write the objects from a given timepoint to file
		"""
		settings = dataUnit.getSettings()
		settings.set("StatisticsFile", filename)

		objnums = []
		volumes = []
		volumeums = []
		coms = []
		comums = []
		avgint = []
		avgintstderr = []
		avgdist = []
		avgdiststderr = []
		areaum = []
		voxelVolume = 1.0
		for i in range(3):
			voxelVolume *= self.voxelSize[i]
			voxelVolume *= 1000000 # convert to um

		# Sort objects
		for tpObjs in self.objects:
			tpObjs.sort()
		
		
		for i, obj in enumerate(self.objects[timepoint]):
			objN, com, volume, meanInt = obj[0:4]
			volumes.append(volume)
			coms.append(com)
			com = list(com)
			for cIter in range(len(com)):
				com[cIter] *= self.voxelSize[cIter]
				com[cIter] *= 1000000 # convert to um

			distList = []
			for j, obj2 in enumerate(self.objects[timepoint]):
				if i == j: continue
				objN2, com2 = obj2[0:2]
				com2 = list(com2)
				for cIter in range(3):
					com2[cIter] *= self.voxelSize[cIter]
					com2[cIter] *= 1000000 # convert to um
				dx = com[0] - com2[0]
				dy = com[1] - com2[1]
				dz = com[2] - com2[2]
				dist = math.sqrt(dx*dx + dy*dy + dz*dz)
				distList.append(dist)
			avgDist, avgDistStd, avgDistStdErr = lib.Math.meanstdeverr(distList)
			
			objnums.append(objN)
			com = tuple(com)
			comums.append(com)
			volumeums.append(volume * voxelVolume)
			avgint.append(meanInt[0])
			avgintstderr.append(meanInt[1])
			avgdist.append(avgDist)
			avgdiststderr.append(avgDistStdErr)
			areaum.append(0.0)

		writer = lib.ParticleWriter.ParticleWriter()
		writer.setObjectValue('objnum', objnums)
		writer.setObjectValue('volume', volumes)
		writer.setObjectValue('volumeum', volumeums)
		writer.setObjectValue('centerofmass', coms)
		writer.setObjectValue('umcenterofmass', comums)
		writer.setObjectValue('avgint', avgint)
		writer.setObjectValue('avgintstderr', avgintstderr)
		writer.setObjectValue('avgdist', avgdist)
		writer.setObjectValue('avgdiststderr', avgdiststderr)
		writer.setObjectValue('areaum', areaum)
		writer.writeObjects(filename, timepoint)

		if self.parameters["ObjectsCreateSource"]:
			# Sort objects
			for tpObjs in self.objPolydata:
				tpObjs.sort()
			# Write analyse polydata results
			filepoly = filename
			tail,sep,head = filepoly.rpartition('.csv')
			filepoly = ''.join((tail,'_poly',sep))
			# Move this to somewhere else
			f = codecs.open(filepoly, "ab", "latin1")
			Logging.info("Saving polydata statistics to file %s"%filepoly, kw="processing")
			w = csv.writer(f, dialect = "excel", delimiter = ";")
			if timepoint >= 0:
				w.writerow(["Timepoint %d" % timepoint])
			w.writerow(["Obj#","COM X", "COM Y", "COM Z", "Dist.(COM-surface)","Dist.(Obj COM-Cell COM)","COM inside surface","% of voxels inside"])
			for i, (objN,(comx,comy,comz),dist,comdist,inside,insidePerc) in enumerate(self.objPolydata[timepoint]):
				dist *= 1000000 # convert to um
				comdist *= 1000000 # convert to um
				w.writerow([i+1, int(round(comx)), int(round(comy)), int(round(comz)), dist, comdist, inside, insidePerc])
			f.close()
		
		if timepoint == self.parameters["Time"]-1:
			tail,sep,head = filename.rpartition('.csv')
			filename = ''.join((tail,'_track',sep))
			trackWriter = lib.ParticleWriter.ParticleWriter()
			trackWriter.writeTracks(filename, self.tracks, 3, self.timeStamps)
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		self.progressObj.setProgress(0.0)
		self.updateProgress(None, "ProgressEvent")

		currentTimepoint = self.getCurrentTimepoint()
		inputImage = self.getInput(1)
		
		try:
			self.voxelSize = self.dataUnit.getVoxelSize()
		except:
			self.voxelSize = (1.0, 1.0, 1.0)
		self.spacing = list(inputImage.GetSpacing())
		for i in range(3):
			self.spacing[i] /= self.spacing[0]
		self.spacing = tuple(self.spacing)

		# Create timestamps
		self.timeStamps = []
		curStamp = 0.0
		for i in range(self.parameters["Time"]):
			self.timeStamps.append(curStamp)
			curStamp += self.parameters["TimeDifference"]
		self.dataUnit.getSettings().set("TimeStamps", self.timeStamps)

		if os.path.exists(self.parameters["ReadObjects"]) and self.modified:
			reader = lib.ParticleReader.ParticleReader(self.parameters["ReadObjects"], 0)
			objects = reader.read()
			volumes = reader.getVolumes()
			intensities = reader.getAverageIntensities()
			objCount = min(len(volumes),len(intensities[0]))
			self.readObjects = []
			for i in range(objCount):
				self.readObjects.append((volumes[i], intensities[0][i]))

		if self.parameters["ObjectsCreateSource"] and self.modified:
			# Update first dims of result data
			wholeExtent = inputImage.GetWholeExtent()
			inputDataUnit = self.getInputDataUnit(1)
			x = wholeExtent[1] - wholeExtent[0] + 1
			y = wholeExtent[3] - wholeExtent[2] + 1
			z = wholeExtent[5] - wholeExtent[4] + 1
			if self.dataUnit:
				self.parameters["X"] = x
				self.parameters["Y"] = y
				self.parameters["Z"] = z
				self.dataUnit.setModifiedDimensions((x, y, z))
				lib.messenger.send(None, "update_dataset_info")

			# Read com of the largest object from input data
			particleFile = inputDataUnit.getSettings().get("StatisticsFile")
			if particleFile is None or not os.path.exists(particleFile):
				pass
				#path = inputDataUnit.getDataSource().path
				#for fileName in os.listdir(path):
				#	if ".csv" in fileName:
				#		particleFile = os.path.join(path,fileName)
			
			if not particleFile is None and os.path.exists(particleFile):
				reader = lib.ParticleReader.ParticleReader(particleFile, 0)
				comObjs = reader.read()
				self.cellCOM = comObjs[0][0].getCenterOfMass()
			else:
				self.cellCOM = (self.parameters["X"] / 2, self.parameters["Y"] / 2, self.parameters["Z"] / 2)

			polydata = self.getPolyDataInput(1)
			if polydata:
				self.polydata = polydata
			else:
				Logging.error("No polydata in source", "Cannot create objects close to surface of input as there is no polydata in input.")
				return inputImage
		
		return self.createData(currentTimepoint)
	
	def distance(self, com1, com2, voxelSize):
		"""
		Help method to calculate distance of two points
		"""
		distanceX = (com1[0] - com2[0]) * voxelSize[0]
		distanceY = (com1[1] - com2[1]) * voxelSize[1]
		distanceZ = (com1[2] - com2[2]) * voxelSize[2]

		return math.sqrt(distanceX * distanceX + distanceY * distanceY + distanceZ * distanceZ)
	
	def generateDistributionValue(self, distr, minValue, maxValue):
		"""
		Generate value for specified distribution inside specified range
		"""
		mu = (maxValue + minValue) / 2.0
		sigma = (maxValue - mu) / 3.0
		if distr == DIST_UNIFORM:
			value = random.randint(minValue,maxValue)
		else:
			if distr == DIST_NORM:
				value = random.gauss(mu,sigma)
			elif distr == DIST_POSNORM:
				value = random.gauss(0.0, 2*sigma)
				value = int(round(abs(value) + minValue))
			elif distr == DIST_NEGNORM:
				value = random.gauss(0.0, 2*sigma)
				if value > 0:
					value *= -1.0
				value = int(round(value + maxValue))

			if value < minValue:
				value = minValue
			elif value > maxValue:
				value = maxValue

		return value
	
