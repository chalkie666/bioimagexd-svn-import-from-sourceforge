#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: DynamicThreshold.py
 Project: BioImageXD
 Created: 10.12.2007, LP
 Description:

 A module that contains dynamic threshold filter for the processing task.
 
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
__author__ = "BioImageXD Project <http://www.bioimagexd.net/>"
__version__ = "$Revision$"
__date__ = "$Date$"

import lib.ProcessingFilter
#import itkBXD
import scripting
import types
import GUIBuilder
import itk

MEAN = 0
MEDIAN = 1

class DynamicThresholdFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Created: 10.12.2007, LP
	Description: A dynamic threshold filter. Uses
	itkBXD.DynamicThresholdImageFilter.
	"""
	name = "Dynamic threshold"
	category = lib.FilterTypes.SEGMENTATION
	level = scripting.COLOR_INTERMEDIATE

	def __init__(self, inputs = (1,1)):
		"""
		Created: 10.12.2007, LP
		Description: Initialization
		"""
		self.statisticsType = MEAN
		self.neighborhood = (5,5)
		self.insideValue = 255
		self.outsideValue = 0
		
		lib.ProcessingFilter.ProcessingFilter.__init__(self,(1,1))
		self.itkFlag = 1
		self.descs = {"X": "X:", "Y": "Y:", "StatisticsType": "Statistics type:"}
		self.filter = None
		self.pc = itk.PyCommand.New()
		self.pc.SetCommandCallable(self.updateProgress)

	def updateProgress(self):
		lib.ProcessingFilter.ProcessingFilter.updateProgress(self,self.filter,"ProgressEvent")

	def getParameters(self):
		"""
		Created: 10.12.2007, LP
		Description: Returns the parameters for GUI.
		"""
		return [["",("StatisticsType",)],["Neighborhood (only odd values)",("X","Y")]]

	def getType(self, param):
		"""
		Created: 10.12.2007, LP
		Description: Returns the types of parameters for GUI.
		"""
		if param == "StatisticsType":
			return GUIBuilder.CHOICE
		return types.IntType

	def getDefaultValue(self, param):
		"""
		Created:
		Description:
		"""
		if param == "StatisticsType":
			return self.statisticsType
		elif param == "X":
			return self.neighborhood[0]
		elif param == "Y":
			return self.neighborhood[1]

	def getParameterLevel(self, param):
		"""
		Created:
		Description:
		"""
		if param in ["X","Y","StatisticsType"]:
			return scripting.COLOR_INTERMEDIATE
		return scripting.COLOR_BEGINNER

	def getRange(self, param):
		"""
		Created:
		Description:
		"""
		if param == "StatisticsType":
			return ("Mean","Median")
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Created: 10.12.2007, LP
		Description: Execute filter in input image and return output image
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self,inputs):
			return None

		self.eventDesc = "Dynamic thresholding image"
		inputImage = self.getInput(1)
		inputImage = self.convertVTKtoITK(inputImage)

		# Import itkBXD now because otherwise it would really slow down the
		# application's starting procedure (about 5 seconds)
		import itkBXD
		dynamicThresholdFilter = itkBXD.DynamicThresholdImageFilter[inputImage,inputImage].New()
		self.filter = dynamicThresholdFilter
		dynamicThresholdFilter.AddObserver(itk.ProgressEvent(),self.pc.GetPointer())
		dynamicThresholdFilter.SetNeighborhood(self.parameters["X"],self.parameters["Y"])
		if self.parameters["StatisticsType"] == MEAN:
			dynamicThresholdFilter.SetStatisticsTypeMean()
		else:
			dynamicThresholdFilter.SetStatisticsTypeMedian()
		dynamicThresholdFilter.SetInput(inputImage)

		outputImage = dynamicThresholdFilter.GetOutput()
		if update:
			outputImage.Update()

		return outputImage