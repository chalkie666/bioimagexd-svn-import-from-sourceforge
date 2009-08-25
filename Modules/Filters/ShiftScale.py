#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ShiftScale
 Project: BioImageXD
 Created: 10.12.2007, LP
 Description:

 A module for shifting and scaling the intensities
 
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
import scripting
import types
import GUI.GUIBuilder
import lib.FilterTypes
import vtk

class ShiftScaleFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for shifting the values of dataset by constant and scaling by a constant
	"""		
	name = "Shift and Scale"
	category = lib.FilterTypes.MATH
	
	def __init__(self):
		"""
		Initialization
		"""		   
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.vtkfilter = vtk.vtkImageShiftScale()
		self.vtkfilter.AddObserver("ProgressEvent", lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, 'ProgressEvent', self.updateProgress)
		self.eventDesc = "Applying a shift and scale to image intensity"
		self.descs = {"Shift": "Shift:", "Scale": "Scale:", "AutoScale": "Scale to range 0-255", "NoOverflow":"Prevent over/underflow"}
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [["", ("Shift", "Scale", "AutoScale", "NoOverflow")]]
		
		
	def getLongDesc(self, parameter):
		"""
		Return a long description of the parameter
		""" 
		return ""
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["Shift", "Scale"]:
			return types.FloatType
		elif parameter in  ["AutoScale","NoOverflow"]:
			return types.BooleanType
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""		
		if parameter == "Shift":
			return 0
		if parameter == "Scale":
			return 1
		return 1
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""			   
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		image = self.getInput(1)
		image.UpdateInformation()
		image.SetUpdateExtent(image.GetWholeExtent())
		image.Update()
		print "Using ",image
		self.vtkfilter.SetInput(image)
		self.vtkfilter.SetClampOverflow(self.parameters["NoOverflow"])
		if self.parameters["AutoScale"]:
			x, y = image.GetScalarRange()
			print "image type=", image.GetScalarTypeAsString()
			print "Range of data=", x, y
			self.vtkfilter.SetOutputScalarTypeToUnsignedChar()
			if not y:
				lib.messenger.send(None, "show_error", "Bad scalar range", "Data has scalar range of %d -%d" % (x, y))
				return vtk.vtkImageData()
			scale = 255.0 / y
			print "Scale=", scale
			self.vtkfilter.SetShift(0)
			self.vtkfilter.SetScale(scale)
		else:
			self.vtkfilter.SetShift(self.parameters["Shift"])
			self.vtkfilter.SetScale(self.parameters["Scale"])
			
			print "Shift=",self.parameters["Shift"], "scale=",self.parameters["Scale"]
			self.vtkfilter.Update()
			print "New Scalar range=", self.vtkfilter.GetOutput().GetScalarRange()
		
#		if update:
#			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()	 
		
