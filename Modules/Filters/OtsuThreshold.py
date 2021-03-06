# -*- coding: iso-8859-1 -*-
"""
 Unit: OtsuThreshold.py
 Project: BioImageXD
 Description:

 A module containing the Otsu threshold filter for the processing task.
							
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

import lib
import GUI
import itk

class OtsuThresholdFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A class for thresholding the image using the Otsu thresholding
	"""		
	name = "Otsu threshold"
	category = lib.FilterTypes.THRESHOLDING
	
	def __init__(self, inputs = (1, 1)):
		"""
		Initialization
		"""		   
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		
		self.descs = {} #"Upper": "Upper threshold", "Lower": "Lower threshold"}
		self.itkFlag = 1
		self.itkfilter = None
		self.filterDesc = "Automatically finds a threshold that separates the image pixels/voxels into two classes, foreground and background, having maximum variance between them\nInput: Grayscale image\nOutput: Binary image";

#	def getDefaultValue(self, parameter):
#		"""
#		Return the default value of a parameter
#		"""
#		if parameter == 'Upper':
#			return 255
#		if parameter == 'Lower':
#			return 0
		
#	def getType(self, parameter):
#		"""
#		Return the type of the parameter
#		"""	   
#		if parameter in ["Lower", "Upper"]:
#			return GUI.GUIBuilder.THRESHOLD
				
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return [] #[["Threshold", (("Lower", "Upper"), )]]

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
			
		image = self.getInput(1)
		image = self.convertVTKtoITK(image)

		self.itkfilter = itk.OtsuThresholdImageFilter[image,image].New()
		self.itkfilter.SetInput(image)
		self.itkfilter.SetInsideValue(0)
		if self.getDataUnit().getSingleComponentBitDepth() == 12:
			self.itkfilter.SetOutsideValue(4095)
		else:
			self.itkfilter.SetOutsideValue(255)
		
		self.itkfilter.SetNumberOfHistogramBins(255)

		data = self.itkfilter.GetOutput()
		data.Update()
		print "Threshold=", self.itkfilter.GetThreshold()
		#self.setParameter("Lower",self.itkfilter.GetThreshold())

		return data 
