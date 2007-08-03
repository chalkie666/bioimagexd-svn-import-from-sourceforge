# -*- coding: iso-8859-1 -*-
"""
 Unit: ImageOperations
 Project: BioImageXD
 Created: 10.02.2005, KP
 Description:

 This is a module with functions for various kind of image operations, for example
 conversion from VTK image data to wxPython bitmap

 Copyright (C) 2005  BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and / or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111 - 1307  USA
"""

__author__ = "BioImageXD Project < http: //www.bioimagexd.org/>"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005 / 01 / 13 13: 42: 03 $"

import vtk
import vtkbxd
import wx
import random
import math
import struct
import Logging
import GUI.Dialogs 
import optimize

def paintLogarithmicScale(ctfbmp, ctf, vertical = 1):
	"""
	Created: 04.08.2006
	Description: Paint a logarithmic scale on a bitmap that represents the given ctf
	"""
	maxval = ctf.GetRange()[1]
	width, height = ctfbmp.GetWidth(), ctfbmp.GetHeight()
	
	bmp = wx.EmptyBitmap(width + 10, height)
	
	deviceContext = wx.MemoryDC()
	deviceContext.SelectObject(bmp)
	deviceContext.BeginDrawing()
	colour = wx.Colour(255, 255, 255)
	deviceContext.SetBackground(wx.Brush(colour))
	deviceContext.SetPen(wx.Pen(colour, 0))
	deviceContext.SetBrush(wx.Brush(colour))
	deviceContext.DrawRectangle(0, 0, width + 16, height)
   
	deviceContext.SetPen(wx.Pen(wx.Colour(0, 0, 0), 1))
	deviceContext.DrawBitmap(ctfbmp, 5, 0)
	
	size = max(width, height)
	maxval = max(ctf.originalRange)
	logMaxVal = math.log(maxval)
	scale = size / float(maxval)
	for i in range(3 * int(logMaxVal) + 1, 1, -1):
		i /= 3.0	
		xCoordinate = int(math.exp(i) * scale)
		if not vertical:
			deviceContext.DrawLine(xCoordinate, 0, xCoordinate, 8)
			
		else:
			deviceContext.DrawLine(0, xCoordinate, 4, xCoordinate)
			deviceContext.DrawLine(width + 6, xCoordinate, width + 10, xCoordinate)
		
	deviceContext.EndDrawing()
	deviceContext.SelectObject(wx.NullBitmap)
	deviceContext = None	 
	return bmp	  
	
def paintCTFValues(ctf, width = 256, height = 32, paintScale = 0, paintScalars = 0):
	"""
	Description: Paint a bar representing a CTF
	
	@author: Kalle Pahajoki
	@since: 18.04.2005
	@param ctf: The ColorTransferFunction to draw
	
	@keyword width: The width of the bitmap
	@keyword height: The height of the bitmap
	@type width: Positive number
	@type height: Positive number
	
	@keyword paintScale: True if a logarithmic scale should be painted on the bitmap
	@type paintScale: Boolean (0,1)

	@keyword paintScalars: True if the max/min values of the range should be painted on the bitmap
	@type paintScalars: Boolean (0,1)
	"""    
	vertical = 0
	if height > width:
		vertical = 1
	bmp = wx.EmptyBitmap(width, height, -1)
	deviceContext = wx.MemoryDC()
	deviceContext.SelectObject(bmp)
	deviceContext.BeginDrawing()
		
	size = width
	if vertical: 
		size = height
	
	maxval = ctf.GetRange()[1]
	colorsPerWidth = float(maxval) / size
	for xCoordinate in range(0, size):
		val = [0, 0, 0]
		ctf.GetColor(xCoordinate * colorsPerWidth, val)
		red, green, blue = val
		red *= 255
		green *= 255
		blue *= 255
		red = int(red)
		green = int(green)
		blue = int(blue)
		
		deviceContext.SetPen(wx.Pen((red, green, blue)))
		if not vertical:
			deviceContext.DrawLine(xCoordinate, 0, xCoordinate, height)
		else:
			deviceContext.DrawLine(0, height - xCoordinate, width, height - xCoordinate)
			
		ctfLowerBound, ctfUpperBound = ctf.GetRange()
	if paintScalars:
		paintBoundaryValues(deviceContext, ctfLowerBound, ctfUpperBound, vertical, height, width)				
	deviceContext.EndDrawing()
	deviceContext.SelectObject(wx.NullBitmap)
	deviceContext = None	 
	if paintScale:
		bmp = paintLogarithmicScale(bmp, ctf)
	return bmp

def paintBoundaryValues(deviceContext, ctfLowerBound, ctfUpperBound, vertical, height, width): 
	"""
	Paints the boundary values of a ColorTransferFunction on a device context

	@author: Kalle Pahajoki
	@since: 18.04.2005

	@param deviceContext: The device context on which to draw
	@param deviceContext: A object of type deviceContext

	@param ctfLowerBound: The lower bound of the range of the CTF
	@type ctfLowerBound: Positive float
	
	@param ctfUpperBound: The upper bound of the range of the CTF
	@type ctfUpperBound: Positive float
	
	@param vertical: True if the values are to be drawn on a vertical line
	@type vertical: Boolean (0,1)
	"""
	#TODO: The 'magic numbers' could be replaced by clearly named constants
	
	deviceContext.SetTextForeground(wx.Colour(255, 255, 255))
	deviceContext.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL))
	if vertical:
		deviceContext.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL))
		deviceContext.DrawText("%d"%ctfLowerBound, 8, height - 20)
		deviceContext.SetFont(wx.Font(6, wx.SWISS, wx.NORMAL, wx.NORMAL))
		deviceContext.SetTextForeground(wx.Colour(0, 0, 0))
		deviceContext.DrawText("%d"%ctfUpperBound, 1, 10)
	else:
		deviceContext.DrawText("%d"%ctfLowerBound, 5, 6)
		deviceContext.SetTextForeground(wx.Colour(0, 0, 0))
		deviceContext.DrawText("%d"%ctfUpperBound, width - 35, 6)

def scaleImage(data, factor = 1.0, zDimension = -1, interpolation = 1, xfactor = 0.0, yfactor = 0.0):
	"""
	Created: 01.08.2005, KP
	Description: Scale an image with cubic interpolation
	"""    
	if zDimension != -1:
		data = getSlice(data, zDimension)
	
	data.SetSpacing(1, 1, 1)
	xDimension, yDimension, zDimension = data.GetDimensions()
	print "dims=",xDimension / 2.0, yDimension / 2.0, 0
	data.SetOrigin(xDimension / 2.0, yDimension / 2.0, 0)
	transform = vtk.vtkTransform()
	xExtent0, xExtent1, yExtent0, yExtent1, zExtent0, zExtent1 = data.GetExtent()
	print "extent=", xExtent0, xExtent1, yExtent0, yExtent1, zExtent0, zExtent1
	if xfactor or yfactor:
		xfactor *= factor
		yfactor *= factor
		
	if not (xfactor or yfactor):
		transform.Scale(1 / factor, 1 / factor, 1)
	else:
		transform.Scale(1 / xfactor, 1 / yfactor, 1)
	
	reslice = vtk.vtkImageReslice()
	reslice.SetOutputOrigin(0, 0, 0)
	reslice.SetInputConnection(data.GetProducerPort())
	
	if not (xfactor or yfactor):
		reslice.SetOutputExtent(int(xExtent0 * factor), int(xExtent1 * factor), 
			int(yExtent0 * factor), int(yExtent1 * factor), zExtent0, zExtent1)
	else:
		reslice.SetOutputExtent(int(xExtent0 * xfactor), int(xExtent1 * xfactor), 
			int(yExtent0 * yfactor), int(yExtent1 * yfactor), zExtent0, zExtent1)	
	reslice.SetResliceTransform(transform)
	
	if interpolation == 1:
		reslice.SetInterpolationModeToLinear()
	else:
		reslice.SetInterpolationModeToCubic()
	# XXX: modified, try to get errors out
	
	data = reslice.GetOutput()
	data.Update()
	
	return data
	
def loadNIHLut(data):
	"""
	Created: 17.04.2005, KP
	Description: Load an NIH Image LUT and return it as CTF
	"""    
	if not len(data):
		raise "loadNIHLut got no data"
	#n=256
	dataLength = len(data) - 32
	#n = d
	infoString = "4s2s2s2s2s8s8si%ds" % dataLength
	Logging.info("Unpacking ", infoString, "d = ", dataLength, "len(data) = ", len(data))#, kw = "imageop")
	#header, version, ncolors, start, end, fill1, fill2, filler, lut = struct.unpack(infoString, data)
	header, dummy, ncolors, start, end, dummy, dummy, dummy, lut = struct.unpack(infoString, data)

	if header != "ICOL":
		raise "Did not get NIH header!"
	ncolors = ord(ncolors[0]) * (2**8) + ord(ncolors[1])
	start = ord(start[0]) * (2**8) + ord(start[1])
	end = ord(end[0]) * (2**8) + ord(end[1])
	
	reds = lut[: ncolors]
	greens = lut[ncolors: (2 * ncolors)]
	blues = lut[(2 * ncolors): (3 * ncolors)]
	return reds, greens, blues
	
def loadLUT(filename, ctf = None, ctfrange = (0, 256)):
	"""
	Method: loadLUT(filename)
	Created: 17.04.2005, KP
	Description: Load an ImageJ binary LUT and return it as CTF. If a ctf
				 is passed as parameter, it is modified in place
	"""    
	if ctf:
		ctf.RemoveAllPoints()
	else:
		ctf = vtk.vtkColorTransferFunction()	  
	fileName = open(filename, "rb")
	lut = fileName.read()
	fileName.close()
	loadLUTFromString(lut, ctf, ctfrange)
	return ctf
	
def loadBXDLutFromString(lut, ctf):
	"""
	Created: 20.11.2006, KP
	Description: Load a BXD format lut from a given string
	"""
	lut = lut[6: ]
	start, end = struct.unpack("ff", lut[0: 8])
	lut = lut[8: ]
	Logging.info("The palette is in range %d-%d" % (start, end), kw = "ctf")
	j = 0
	start = int(start)
	end = int(end)
	k = ( len(lut) / 3 ) - 1
	reds = lut[0: k + 1]
	greens = lut[k + 1: 2 * k + 2]
	blues = lut[(2 * k) + 2: 3 * k + 3]
			
	j = 0
	for i in range(start, end + 1):
		#print "j=",j,"n=",len(reds),len(greens),len(blues)
		red = ord(reds[j])
		green = ord(greens[j])
		blue = ord(blues[j])
	  
		red /= 255.0
		green /= 255.0
		blue /= 255.0		
		ctf.AddRGBPoint(i, red, green, blue)
		j += 1
	return 
			
def loadLUTFromString(lut, ctf, ctfrange = (0, 256)):
	"""
	Created: 18.04.2005, KP
	Description: Load an ImageJ binary LUT from string
	Parameters:
		lut		 A binary string representing the lookup table
		ctf		 The CTF to modify
		ctfrange The range to which construct the CTF
	"""		   
	if lut[0: 6] == "BXDLUT":
		
		return loadBXDLutFromString(lut, ctf)
	failed = 1
	if len(lut) != 768:
		try:
			reds, greens, blues = loadNIHLut(lut)
			failed = 0
		except "loadNIHLut got no data":
			failed = 1
	
	if failed:
		k = ( len(lut) / 3 ) - 1
		reds = lut[0: k + 1]
		greens = lut[k + 1: 2 * k + 2]
		blues = lut[(2 * k) + 2: 3 * k + 3]
		
	step = int(math.ceil(ctfrange[1] / k))
	if step == 0:
		return vtk.vtkColorTransferFunction()
	j = 0
	#Logging.info("Ctf range = ",ctfrange[0]," - ",ctfrange[1],"step=",step)
	for i in range(int(ctfrange[0]), int(ctfrange[1]), int(step)):
		red = ord(reds[j])
		green = ord(greens[j])
		blue = ord(blues[j])
		red /= 255.0
		green /= 255.0
		blue /= 255.0		
		ctf.AddRGBPoint(i, red, green, blue)
		j += 1
	
def saveLUT(ctf, filename):
	"""
	Created: 17.04.2005, KP
	Description: Save a CTF as ImageJ binary LUT
	"""    
	ext = filename.split(".")[-1]
	ltype = "ImageJ"
	if ext.lower() == "bxdlut":
		ltype = "BioImageXD"
	fileName = open(filename, "wb")
	stringOfLUT = lutToString(ctf, luttype = ltype)
	fileName.write(stringOfLUT)
	fileName.close()
	
def lutToString(ctf, luttype = "ImageJ"):
	"""
	Created: 18.04.2005, KP
	Description: Write a lut to a string
	"""    
	stringOfLUT = ""
	minval, maxval = ctf.GetRange()
	if luttype == "ImageJ":
		perColor = maxval / 255
	else:
		perColor = 1
	if luttype == "BioImageXD":
		stringOfLUT = "BXDLUT"
		Logging.info("Adding to BXDLUT structure the minval=%d, maxval=%d" % (minval, maxval), kw = "ctf")
		
		stringOfLUT += struct.pack("f", minval)
		
		stringOfLUT += struct.pack("f", maxval)
	for col in range(0, 3):
		for i in range(0, int(maxval) + 1, int(perColor)):
			val = [0, 0, 0]
			
			ctf.GetColor(i, val)
			red, green, blue = val
			red *= 255
			green *= 255
			blue *= 255
			red = int(red)
			green = int(green)
			blue = int(blue)
			if red < 0: 
				red = 0
			if blue < 0: 
				blue = 0
			if green < 0: 
				green = 0
			if red >= 255: 
				red = 255
			if green >= 255: 
				green = 255
			if blue >= 255: 
				blue = 255
			color = [red, green, blue]
			stringOfLUT += chr(color[col])
	return stringOfLUT
		
def getAsParameterList(iTF):
	"""
	Created: Unknown, KP
	Description: Returns a list of iTF parameters
	"""
	lst = [	iTF.GetBrightness(),
			iTF.GetContrast(),
			iTF.GetGamma(),
			iTF.GetMinimumThreshold(),
			iTF.GetMinimumValue(),
			iTF.GetMaximumThreshold(),
			iTF.GetMaximumValue(),
			iTF.GetProcessingThreshold(),
			iTF.GetRangeMax()]
	return lst
	
def setFromParameterList(iTF, listOfValuesToSet):
	"""
	Created: Unknown, KP
	Description: Set the parameters from the input list
	"""
	brightness, contrast, gamma, minimumThreshold, minimumValue, maximumThreshold, \
	maximumValue, processingThreshold, rangemax = listOfValuesToSet
	iTF.SetRangeMax(rangemax)
	iTF.SetContrast(float(contrast))
	iTF.SetGamma(float(gamma))
	iTF.SetMinimumThreshold(int(minimumThreshold))
	iTF.SetMinimumValue(int(minimumValue))
	iTF.SetMaximumThreshold(int(maximumThreshold))
	iTF.SetMaximumValue(int(maximumValue))
	iTF.SetProcessingThreshold(int(processingThreshold))
	iTF.SetBrightness(int(brightness))

def vtkImageDataToWxImage(data, sliceNumber = -1, startpos = None, endpos = None):
	"""
	Created: Unknown, KP
	Description: Converts vtk-ImageData to a WxImage
	"""
	if sliceNumber >= 0:	
		#Logging.info("Getting sliceNumber %d"%sliceNumber,kw="imageop")
		data = getSlice(data, sliceNumber, startpos, endpos)
	exporter = vtk.vtkImageExport()
#	 Logging.info("Setting update extent to ",data.GetWholeExtent(),kw="imageop")
	data.SetUpdateExtent(data.GetWholeExtent())
	data.Update()
	exporter.SetInputConnection(data.GetProducerPort())
	dataMemorySize = exporter.GetDataMemorySize()
	formatString = "%ds" % dataMemorySize
	structString = struct.pack(formatString, "")
	exporter.SetExportVoidPointer(structString)
	exporter.Export()
	width, height = data.GetDimensions()[0:2]
	image = wx.EmptyImage(width, height)
	image.SetData(structString)
	return image
	
def vtkImageDataToPngString(data, sliceNumber = -1, startpos = None, endpos = None):
	"""
	Created: 26.07.2005, KP
	Description: A function that returns a vtkImageData object as png
				 data in a string
	"""    
	if sliceNumber >= 0:
		#Logging.info("Getting sliceNumber %d"%sliceNumber,kw="imageop")
		data = getSlice(data, sliceNumber, startpos, endpos)
		
	pngwriter = vtk.vtkPNGWriter()
	pngwriter.WriteToMemoryOn()
	pngwriter.SetInputConnection(data.GetProducerPort())
	#pngwriter.Update()
	pngwriter.Write()
	result = pngwriter.GetResult()
	data = ""
	for i in range(result.GetNumberOfTuples()):
		data += chr(result.GetValue(i))
	return data
	
def getMIP(imageData, color):
	"""
	Created: 1.9.2005, KP
	Description: A function that will take a volume and do a simple
				 maximum intensity projection that will be converted to a
				 wxBitmap
	"""   
	#getslice = vtk.vtkExtractVOI()
	#getslice.SetInput(imageData)
	#width, height, depth = imageData.GetDimensions()
	#getslice.SetVOI(0,width-1,0,height-1,depth/2,depth/2)
	
	#mip = getslice
	#minval, maxval = imageData.GetScalarRange()
	maxval = imageData.GetScalarRange()[1]
	imageData.SetUpdateExtent(imageData.GetWholeExtent())		 

	if maxval > 255:
		shiftscale = vtk.vtkImageShiftScale()
		shiftscale.SetInputConnection(imageData.GetProducerPort())
		shiftscale.SetScale(256.0 / maxval)
		shiftscale.SetOutputScalarTypeToUnsignedChar()	  
		imageData = shiftscale.GetOutput()
	#width, height, depth = imageData.GetDimensions()
	#cast = vtk.vtkImageCast()
	#cast.SetInput(mip.GetOutput())
	#cast.SetOutputScalarTypeToUnsignedChar()
	
	mip = vtkbxd.vtkImageSimpleMIP()
	mip.SetInputConnection(imageData.GetProducerPort())
	
	if color == None:
		output = optimize.execute_limited(mip)
		#mip.Update()

		#output = mip.GetOutput()
		#output.Update()
		return output

	if mip.GetOutput().GetNumberOfScalarComponents() == 1:
		ctf = getColorTransferFunction(color)
	
		maptocolor = vtk.vtkImageMapToColors()
		maptocolor.SetInputConnection(mip.GetOutputPort())
		maptocolor.SetLookupTable(ctf)
		maptocolor.SetOutputFormatToRGB()
		#maptocolor.Update()
		#imagedata=maptocolor.GetOutput()
		imagedata = optimize.execute_limited(maptocolor)
		
	else:
		imagedata = output = optimize.execute_limited(mip)
	#imagedata.Update()		   
	return imagedata

def getColorTransferFunction(color):
	"""
	Created: 06.11.2006, KP
	Description: Convert a color to a ctf and pass a ctf through
	"""
	if isinstance(color, vtk.vtkColorTransferFunction):
		return color
	ctf = vtk.vtkColorTransferFunction()
	red, green, blue = (0, 0, 0)
	ctf.AddRGBPoint(0.0, red, green, blue)
	
	red, green, blue = color
	red /= 255
	green /= 255
	blue /= 255
	ctf.AddRGBPoint(255.0, red, green, blue)	
	return ctf
	
def vtkImageDataToPreviewBitmap(dataunit, timepoint, color, width = 0, height = 0, getvtkImage = 0):
	#gcolor = (0, 0, 0), 
	"""
	Created: KP
	Description: A function that will take a volume and do a simple
				 Maximum Intensity Projection that will be converted to a
				 wxBitmap
	"""   
	imagedata = dataunit.getMIP(timepoint, None, small = 1, noColor = 1)
	vtkImg = imagedata

#	 imagedata.Update()
	if not color:
		color = dataunit.getColorTransferFunction()
	
	ctf = getColorTransferFunction(color)
	
	maxval = ctf.GetRange()[1]
	#imin, imax = imagedata.GetScalarRange()
	imax = imagedata.GetScalarRange()[1]
	if maxval > imax:
		step = float(maxval / imax)
		ctf2 = vtk.vtkColorTransferFunction()
		for i in range(0, maxval, int(step)):
			red, green, blue = ctf.GetColor(i)
			ctf2.AddRGBPoint(i / step, red, green, blue)
		ctf = ctf2
	maptocolor = vtk.vtkImageMapToColors()
	maptocolor.SetInputConnection(imagedata.GetProducerPort())
	maptocolor.SetLookupTable(ctf)
	maptocolor.SetOutputFormatToRGB()
	maptocolor.Update()
	imagedata = maptocolor.GetOutput()
	
	#imagedata.Update()
	#imagedata=getMIP(imageData,color)
	image = vtkImageDataToWxImage(imagedata)
	#image.SaveMimeFile("mippi2.png","image/png")
	xSize, ySize = image.GetWidth(), image.GetHeight()
	if not width and height:
		aspect = float(xSize) / ySize
		width = aspect * height
	if not height and width:
		aspect = float(ySize) / xSize
		height = aspect * width
	if not width and not height:
		width = height = 64
	#Logging.info("Scaling to %dx%d"%(width,height),kw="imageop")
	image.Rescale(width, height)
	
	bitmap = image.ConvertToBitmap()
	ret = [bitmap]
	if getvtkImage:
		ret.append(vtkImg)
		return ret
	return bitmap
	
def getPlane(data, plane, xCoordinate, yCoordinate, zCoordinate, applyZScaling = 0):
	"""
	Created: 06.06.2005, KP
	Description: Get a plane from given the volume
	"""   
	xAxis, yAxis, zAxis = 0, 1, 2
	print "getPlane", plane, xCoordinate, yCoordinate, zCoordinate
	permute = vtk.vtkImagePermute()
	dataWidth, dataHeight, dataDepth = data.GetDimensions()
	voi = vtk.vtkExtractVOI()
	#voi.SetInput(permute.GetOutput())
	permute.SetInputConnection(data.GetProducerPort())
	spacing = data.GetSpacing()
	data.SetSpacing(1,1,1)
	data.SetOrigin(0,0,0)
	xscale = 1
	yscale = 1
	if plane == "zy":
		print "Getting plane",xCoordinate, xCoordinate, 0, dataHeight - 1, 0, dataDepth - 1
		data.SetUpdateExtent(xCoordinate, xCoordinate, 0, dataHeight - 1, 0, dataDepth - 1)
		permute.SetFilteredAxes(zAxis, yAxis, xAxis)
#		voi.SetVOI(xCoordinate, xCoordinate, 0, dataHeight - 1, 0, dataDepth - 1)
		permute.Update()
		data = permute.GetOutput()		
		#data.SetOrigin(0,0,0)
		print "permute gave",data
		voi.SetInput(data)

		voi.SetVOI(0, dataDepth-1, 0, dataHeight-1, xCoordinate, xCoordinate)

		data.SetUpdateExtent(0, dataDepth-1, 0, dataHeight-1, 0,0)
		data.SetWholeExtent(0, dataDepth-1, 0, dataHeight-1, 0,0)
		#data.SetSpacing(1,1,1)
		xdim = dataDepth
		ydim = dataHeight
		
		if applyZScaling: 
			xdim *= spacing[2]
			xscale = spacing[2]
		
	elif plane == "xz":
		data.SetUpdateExtent(0, dataWidth - 1, yCoordinate, yCoordinate, 0, dataDepth - 1)
		permute.SetFilteredAxes(xAxis, zAxis, yAxis)
		permute.Update()
		data = permute.GetOutput()
		data.SetUpdateExtent(0, dataWidth-1, 0, dataDepth-1, 0,0)
		data.SetWholeExtent(0, dataWidth-1, 0, dataDepth-1, 0,0)
		#data.SetOrigin(0,0,0)
		#data.SetSpacing(1,1,1)

		voi.SetInput(data)
		#voi.SetVOI(0, dataWidth - 1, yCoordinate, yCoordinate, 0, dataDepth - 1)
		voi.SetVOI(0, dataWidth - 1, 0, dataDepth - 1, yCoordinate, yCoordinate)


		xdim = dataWidth
		ydim = dataDepth
		if applyZScaling: 
			ydim *= spacing[2]
			yscale = 1
		
	#vtkfilter = permute
	if applyZScaling:
		permute.Update()
		print "scaling ", voi.GetOutput()
		return scaleImage(voi.GetOutput(), interpolation = 2, xfactor = xscale, yfactor = yscale)
		
	
	voi.Update()
	print "got from voi=",voi.GetOutput()
#	permute.Update()
#	return permute.GetOutput()
	return voi.GetOutput()
	
def getPlaneOLD(data, plane, xCoordinate, yCoordinate, zCoordinate, applyZScaling = 0):
	"""
	Created: 06.06.2005, KP
	Description: Get a plane from given the volume
	"""   
	xAxis, yAxis, zAxis = 0, 1, 2
	print "getPlane", plane, xCoordinate, yCoordinate, zCoordinate
	permute = vtk.vtkImagePermute()
	dataWidth, dataHeight, dataDepth = data.GetDimensions()
	voi = vtk.vtkExtractVOI()
	#voi.SetInput(permute.GetOutput())
	voi.SetInputConnection(data.GetProducerPort())
	permute.SetInputConnection(voi.GetOutputPort())
	spacing = data.GetSpacing()
	xscale = 1
	yscale = 1
	if plane == "zy":
		print "Getting plane",xCoordinate, xCoordinate, 0, dataHeight - 1, 0, dataDepth - 1
		data.SetUpdateExtent(xCoordinate, xCoordinate, 0, dataHeight - 1, 0, dataDepth - 1)
		voi.SetVOI(xCoordinate, xCoordinate, 0, dataHeight - 1, 0, dataDepth - 1)
		voi.Update()
		print voi.GetOutput()
		permute.SetFilteredAxes(zAxis, yAxis, xAxis)
		xdim = dataDepth
		ydim = dataHeight
		
		if applyZScaling: 
			xdim *= spacing[2]
			xscale = spacing[2]
		
	elif plane == "xz":
		data.SetUpdateExtent(0, dataWidth - 1, yCoordinate, yCoordinate, 0, dataDepth - 1)
		#voi.SetVOI(0,dataWidth-1,0,dataDepth-1,yCoordinate,yCoordinate)
		voi.SetVOI(0, dataWidth - 1, yCoordinate, yCoordinate, 0, dataDepth - 1)
		permute.SetFilteredAxes(xAxis, zAxis, yAxis)
		xdim = dataWidth
		ydim = dataDepth
		if applyZScaling: 
			ydim *= spacing[2]
			yscale = 1
		
	#vtkfilter = permute
	if applyZScaling:
		permute.Update()
		return scaleImage(permute.GetOutput(), interpolation = 2, xfactor = xscale, yfactor = yscale)
		
	permute.Update()
	return permute.GetOutput()
	
def watershedPalette(ctfLowerBound, ctfUpperBound):	
	"""
	Created: Unknown, KP
	Description: Returns a randomly created CTF.
	"""
	ctf = vtk.vtkColorTransferFunction()
#	 ctf.AddRGBPoint(0,1,1,1)
#	 ctf.AddRGBPoint(1,0,0,0)
	ctf.AddRGBPoint(0, 0, 0, 0)
	ctf.AddRGBPoint(1, 0, 0, 0)
	
	if ctfLowerBound <= 1: 
		ctfLowerBound = 2
	for i in range(int(ctfLowerBound), int(ctfUpperBound)):		
		red = 0
		green = 0
		blue = 0    
		while red + green + blue < 1.5:
			red = random.random()
			green = random.random()
			blue = random.random()
		
		ctf.AddRGBPoint(float(i), float(red), float(green), float(blue))
		
	return ctf

def fire(ctfLowerBound, ctfUpperBound):
	"""
	Created: 
	Description: 
	"""
	reds = [
		  0,   0,   1,  25,  49,  73,  98, 122, 
		146, 162, 173, 184, 195, 207, 217, 229, 
		240, 252, 255, 255, 255, 255, 255, 255, 
		255, 255, 255, 255, 255, 255, 255, 255
	]
	greens = [	
		  0,   0,   0,   0,   0,   0,   0,   0, 
		  0,   0,   0,   0,   0,  14,  35,  57, 
		 79, 101, 117, 133, 147, 161, 175, 190, 
		205, 219, 234, 248, 255, 255, 255, 255
	]
	blues = [
		 31,  61,  96, 130, 165, 192, 220, 227, 
		210, 181, 151, 122,  93,  64,  35,   5, 
		  0,   0,   0,   0,   0,   0,   0,   0, 
		  0,   0,   0,  35,  98, 160, 223, 255
	]
	maxColorIndex = min(len(reds), len(greens), len(blues))
	div = ctfUpperBound / float(maxColorIndex)
	
	ctf = vtk.vtkColorTransferFunction()
	ctf.AddRGBPoint(0, 0, 0, 0)
	for colorIndex in range(ctfLowerBound, maxColorIndex):
		red = reds[colorIndex] / 255.0
		green = greens[colorIndex] / 255.0
		blue = blues[colorIndex] / 255.0
		ctf.AddRGBPoint(colorIndex * div, red, green, blue)
	return ctf

def getOverlay(width, height, color, alpha):
	"""
	Method: getOverlay(width, height, color, alpha)
	Created: 11.07.2005, KP
	Description: Create an overlay of given color with given alpha
	"""		  
	#print "\n\nGetting overlay",width,height
	size = width * height * 3
	formatString = "%ds" % size
	red, green, blue = color
	structStr = chr(red) + chr(green) + chr(blue)
	structStr = (width * height) * structStr
	structString = struct.pack(formatString, structStr)
	img = wx.EmptyImage(width, height)
	img.SetData(structString)
	size = width * height
	structStr = chr(alpha)
	formatString = "%ds" % size
	structStr = size * structStr
	structString = struct.pack(formatString, structStr)
	img.SetAlphaData(structString)
	return img
	
def getOverlayBorders(width, height, color, alpha, lineWidth = 1):
	"""
	Created: 12.04.2005, KP
	Description: Create borders for an overlay that are only very little transparent
	"""		  
	size = width * height * 3
	formatString = "%ds" % size	
	red, green, blue = color
	structStr = chr(red) + chr(green) + chr(blue)
	structStr = (width * height) * structStr
	structString = struct.pack(formatString, structStr)
	img = wx.EmptyImage(width, height)
	img.SetData(structString)
	size = width * height
	structStr = chr(0)
	formatString = "%ds" % size	
	structStr = size * structStr
	structString = struct.pack(formatString, structStr)
	structString = chr(alpha) * (2 * width) + structString[2 * width: ]
	lengthOfStructStr = len(structString)
	structString = structString[: lengthOfStructStr  - (2 * width)] + chr(alpha) * 2 * width
	twochar = chr(alpha) + chr(alpha)
	for i in range(0, width * height, width):
		if i:
			structString = structString[: i - 2] + 2 * twochar + structString[i + 2: ]
		else:
			structString = structString[: i] + twochar + structString[i + 2: ]
	img.SetAlphaData(structString)
	return img	  
	
def get_histogram(image):
	"""
	Created: 06.08.2006, KP
	Description: Return the histogrm of the image as a list of floats
	"""
	accu = vtk.vtkImageAccumulate()
	accu.SetInputConnection(image.GetProducerPort())
	x0, x1 = image.GetScalarRange()
	accu.SetComponentExtent(0, x1, 0, 0, 0, 0)
	accu.Update() 
	data = accu.GetOutput()
	
	values = []
	x0, x1, y0, y1, z0, z1 = data.GetWholeExtent()

	for i in range(0, int(x1) + 1):
		c = data.GetScalarComponentAsDouble(i, 0, 0, 0)
		values.append(c)
	return values
	
def histogram(imagedata, colorTransferFunction = None, bg = (200, 200, 200), logarithmic = 1, ignore_border = 0, 
	lower = 0, upper = 0, percent_only = 0, maxval = 255):
	"""
	Created: 11.07.2005, KP
	Description: Draw a histogram of a volume
	"""		  
	values = get_histogram(imagedata)
	sum = 0
	xoffset = 10
	sumth = 0
	percent = 0
	Logging.info("lower = ", lower, "upper = ", upper, kw = "imageop")
	for i, c in enumerate(values):
		sum += c
		if (lower or upper):
			if i >= lower and i <= upper:
				sumth += c
	retvals = values[: ]
	if sumth:
		percent = (float(sumth) / sum)
		#Logging.info("percent=",percent,kw="imageop")
	if ignore_border:
		ma = max(values[5:])
		mi = min(values[:-5])
		n = len(values)
		for i in range(0, 5):
			values[i] = ma
		for i in range(n - 5, n):
			values[i] = mi
			
	for i, value in enumerate(values):
		if value == 0: values[i] = 1
	if logarithmic:
		values = map(math.log, values)
	m = max(values)
	scale = 150.0 / m
	values = [x * scale for x in values]
	w = 256
	x1 = max(values)
	w += xoffset + 5
	
	diff = 0
	if colorTransferFunction:
		diff = 40
	if percent:
		diff += 30
	Logging.info("Creating a %dx%d bitmap for histogram" % (int(w), int(x1) + diff), kw = "imageop")
		
	# Add an offset of 15 for the percentage text
	bmp = wx.EmptyBitmap(int(w), int(x1) + diff + 15)
	dc = wx.MemoryDC()
	dc.SelectObject(bmp)
	dc.BeginDrawing()
	
	blackpen = wx.Pen((0, 0, 0), 1)
	graypen = wx.Pen((100, 100, 100), 1)
	whitepen = wx.Pen((255, 255, 255), 1)
	
	dc.SetBackground(wx.Brush(bg))

	dc.Clear()
	dc.SetBrush(wx.Brush(wx.Colour(200, 200, 200)))
	dc.DrawRectangle(0, 0, w, 150)
	
	if not logarithmic:
		points = range(1, 150, 150 / 8)
	else:
		points = [4, 8, 16, 28, 44, 64, 88, 116, 148]
		points = [p + 2 for p in points]
		points.reverse()
		
	for i in points:
		y = i
		dc.SetPen(blackpen)
		dc.DrawLine(0, y, 5, y)
		dc.SetPen(whitepen)
		dc.DrawLine(0, y - 1, 5, y - 1)
	
	d = (len(values) - 1) / 255.0
	for i in range(0, 255):
		c = values[int(i * d)]
		#print "i=",i,"d=",d,"i*d=",i*d,"i*d+d=",int((i*d)+d)
		c2 = values[int((i * d) + d)]
		dc.SetPen(graypen)
		dc.DrawLine(xoffset + i, x1, xoffset + i, x1 - c)
		dc.SetPen(blackpen)
		dc.DrawLine(xoffset + i, x1 - c, xoffset + i + 1, x1 - c2)
			
	if colorTransferFunction:
		for i in range(0, 256):
			val = [0, 0, 0]
			colorTransferFunction.GetColor(i * d, val)
			r, g, b = val
			r = int(r * 255)
			b = int(b * 255)
			g = int(g * 255)
			dc.SetPen(wx.Pen(wx.Colour(r, g, b), 1))
			dc.DrawLine(xoffset + i, x1 + 8, xoffset + i, x1 + 30)
		dc.SetPen(whitepen)
		dc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))
		dc.DrawText(str(int(maxval)), 230, x1 + 10)
	else:
		Logging.info("Got no ctf for histogram", kw = "imageop")
	
	dc.EndDrawing()
	dc.SelectObject(wx.NullBitmap)
	dc = None	 
	return bmp, percent, retvals, xoffset

def getMaskFromROIs(rois, mx, my, mz):
	"""
	Created: 06.08.2006, KP
	Description: Create a mask that contains all given Regions of Interest
	"""
	insideMap = {}
	for shape in rois:
		insideMap.update(shape.getCoveredPoints())
	insMap = {}
	coveredPointAmount = len(insideMap.keys())
	for x, y in insideMap.keys():
		insMap[(x, y)] = 1    
	return coveredPointAmount, getMaskFromPoints(insMap, mx, my, mz)
	
def getMaskFromPoints(points, mx, my, mz):
	"""
	Created: KP
	Description: Create a mask where all given points are set to 255
	"""
	size = mx * my
	pointStructString = "%dB" % size
	#pointData=[255*((i % mx,i / my) in points) for i in range(0,mx*my)]
	#pointData = [255*((x,y) in points) for x in range(0,mx) for y in range(0,my)]
	pointData = []
	for y in range(0, my):
		for x in range(0, mx):
			pointData.append(255 * points.get((x, y), 0))
	packedPointString = struct.pack(pointStructString, *pointData)
	
	importer = vtk.vtkImageImport()
	importer.CopyImportVoidPointer(packedPointString, mx * my)
# Why is this done dynamically?
	format = "UnsignedChar"
	eval("importer.SetDataScalarTypeTo%s()" % format)
	importer.SetNumberOfScalarComponents(1)
	importer.SetDataExtent(0, mx - 1, 0, my - 1, 0, 0)
	importer.SetWholeExtent(0, mx - 1, 0, my - 1, 0, 0)

	importer.Update()
	#writer = vtk.vtkPNGWriter()
	#writer.SetFileName("foo.png")
	#writer.SetInput(image)
	#writer.Write()
	
	append = vtk.vtkImageAppend()
	append.SetAppendAxis(2)
	for z in range(0, mz):
		append.SetInput(z, importer.GetOutput())
	append.Update()
	image2 = append.GetOutput()
	#print "Image2=",image2
	return image2
	
def equalize(imagedata, ctf):
	"""
	Created: Unknown, KP
	Description: Creates a set of lookup values from a histogram from the imagedata parameter.
	Then creates a color transfer function from these values and returns it.
	"""
	histogram = get_histogram(imagedata)
	maxval = len(histogram)
	
	def weightedValue(x):
		if x < 2:
			return x
		return math.sqrt(x)
	
	intsum = weightedValue(histogram[0])
	for i in range(1, maxval):
		intsum += 2 * weightedValue(histogram[i])
	intsum += weightedValue(histogram[-1])
	
	scale = maxval / float(intsum)
	lut = [0] * (maxval + 1)
	intsum = weightedValue(histogram[0])
	for i in range(1, maxval):
		delta = weightedValue(histogram[i])
		intsum += delta
		ceilValue = math.ceil(intsum * scale)
		floorValue = math.floor(intsum * scale)
# Changed the name of a to colorLookup, maybe not the clearest name yet though
		colorLookup = floorValue
		if abs(ceilValue - intsum * scale) < abs(floorValue - intsum * scale):
			colorLookup = ceilValue
		lut[i] = colorLookup
		intsum += delta
	lut[-1] = maxval
	
	ctf2 = vtk.vtkColorTransferFunction()
	for i, value in enumerate(lut):
		val = [0, 0, 0]
		ctf.GetColor(value, val)
		ctf2.AddRGBPoint(i, *val)
	return ctf2
	
def scatterPlot(imagedata1, imagedata2, z, countVoxels, wholeVolume = 1, logarithmic = 1, 
	dataunits = [], timepoint = 0):
	"""
	Created: 25.03.2005, KP
	Description: Create scatterplot
	"""		  
	imagedata1.SetUpdateExtent(imagedata1.GetWholeExtent())
	imagedata2.SetUpdateExtent(imagedata1.GetWholeExtent())
		
	imagedata1.Update()
	imagedata2.Update()
	x0, x1 = imagedata1.GetScalarRange()
	d = 255.0 / x1
	#shiftscale=vtk.vtkImageShiftScale()
	#shiftscale.SetOutputScalarTypeToUnsignedChar()
	#shiftscale.SetScale(d)
	#shiftscale.SetInput(imagedata1)
	#imagedata1 = shiftscale.GetOutput()

	x0, x1 = imagedata2.GetScalarRange()
	d = 255.0 / x1
	#shiftscale=vtk.vtkImageShiftScale()
	#shiftscale.SetOutputScalarTypeToUnsignedChar()
	#shiftscale.SetScale(d)
	#shiftscale.SetInput(imagedata2)
	#imagedata2 = shiftscale.GetOutput()
	
	app = vtk.vtkImageAppendComponents()
	app.AddInput(imagedata1)
	app.AddInput(imagedata2)
	#app.Update()
	
	shiftscale = vtk.vtkImageShiftScale()
	shiftscale.SetOutputScalarTypeToUnsignedChar()
	shiftscale.SetScale(d)
	shiftscale.SetInputConnection(app.GetOutputPort())
	
	acc = vtk.vtkImageAccumulate()
	
	#n = max(imagedata1.GetScalarRange())
	#n2 = max(max(imagedata2.GetScalarRange()),n)
	#print "n=",n
	n = 255
	acc.SetComponentExtent(0, n, 0, n, 0, 0)
	acc.SetInputConnection(shiftscale.GetOutputPort())
	acc.Update()
	
	data = acc.GetOutput()
	
	originalRange = data.GetScalarRange()
	
	if logarithmic:
		Logging.info("Scaling scatterplot logarithmically", kw = "imageop")
		logscale = vtk.vtkImageLogarithmicScale()
		logscale.SetInputConnection(acc.GetOutputPort())
		logscale.Update()
		data = logscale.GetOutput()
		
	x0, x1 = data.GetScalarRange()
	#print "Scalar range of logarithmic scatterplot=",x0,x1
	
	if countVoxels:
		x0, x1 = data.GetScalarRange()
		Logging.info("Scalar range of scatterplot = ", x0, x1, kw = "imageop")
		ctf = fire(x0, x1)
		ctf = equalize(data, ctf)
		#n = scatter.GetNumberOfPairs()
		#Logging.info("Number of pairs=%d"%n,kw="imageop")
		maptocolor = vtk.vtkImageMapToColors()
		maptocolor.SetInputConnection(data.GetProducerPort())
		maptocolor.SetLookupTable(ctf)
		maptocolor.SetOutputFormatToRGB()
		maptocolor.Update()
		data = maptocolor.GetOutput()
		ctf.originalRange = originalRange
	Logging.info("Scatterplot has dimensions: ", data.GetDimensions(), data.GetExtent(), kw = "imageop")						  
	data.SetWholeExtent(data.GetExtent())
	#if dataunits:
	#	 dataunits[0].storeToCache(data,timepoint,"scpt_%s"%dataunits[1])
	#print "data.GetWholeExtent()=",data.GetWholeExtent()
	img = vtkImageDataToWxImage(data)
	#if img.GetWidth()>255:
	#	 
	#	 img.Rescale(255,255)
	return img, ctf
	
def getZoomFactor(imageWidth, imageHeight, screenWidth, screenHeight):
	"""
	Created: KP
	Description: Calculate a zoom factor so that the image
				 will be zoomed to be as large as possible
				 while fitting to screenWidth, screenHeight
	"""		  
	widthProportion = float(screenWidth) / imageWidth
	heightProportion = float(screenHeight) / imageHeight
	return min(widthProportion, heightProportion)
	
def vtkZoomImage(image, zoomInFactor):
	"""
	Created: KP
	Description: Zoom a volume
	"""
	zoomOutFactor = 1.0 / zoomInFactor
	reslice = vtk.vtkImageReslice()
	reslice.SetInputConnection(image.GetProducerPort())
	
	spacing = image.GetSpacing()
	extent = image.GetExtent()
	origin = image.GetOrigin()
	extent = (extent[0], extent[1] / zoomOutFactor, extent[2], extent[3] / zoomOutFactor, extent[4], extent[5])
	
	spacing = (spacing[0] * zoomOutFactor, spacing[1] * zoomOutFactor, spacing[2])
	reslice.SetOutputSpacing(spacing)
	reslice.SetOutputExtent(extent)
	reslice.SetOutputOrigin(origin)

	# These interpolation settings were found to have the
	# best effect:
	# If we zoom out, no interpolation
	if zoomOutFactor > 1:
		reslice.InterpolateOff()
	else:
	# If we zoom in, use cubic interpolation
		reslice.SetInterpolationModeToCubic()
		reslice.InterpolateOn()
	#reslice.Update()
	#return reslice.GetOutput()
	data = optimize.execute_limited(reslice)
	data.Update()
	return data
	
def zoomImageToSize(image, width, height):
	"""
	Created: KP
	Description: Scale an image to a given size
	"""			  
	return image.Scale(width, height)
	
def zoomImageByFactor(image, zoomFactor):
	"""
	Created: KP
	Description: Scale an image by a given factor
	"""		  
	oldWidth, oldHeight = image.GetWidth(), image.GetHeight()
	newWidth, newHeight = int(zoomFactor * oldWidth), int(zoomFactor * oldHeight)
	return zoomImageToSize(image, newWidth, newHeight)

def getSlice(volume, zslice, startpos = None, endpos = None):
	"""
	Created: KP
	Description: Extract a given slice from a volume
	"""
# VOI is volume of interest
	voi = vtk.vtkExtractVOI()
	voi.SetInputConnection(volume.GetProducerPort())
	#print volume.GetDimensions(), volume.GetExtent()
	if startpos:
		startx, starty = startpos
		endx, endy = endpos
	else:
		startx, starty = 0, 0
		endx, endy = volume.GetDimensions()[0:2]
#	 Logging.info("VOI of dataset = (%d,%d,%d,%d,%d,%d)"%
#	(startx,endx-1,starty,endy-1,zslice,zslice),kw="preview")
	voi.SetVOI(startx, endx - 1, starty, endy - 1, zslice, zslice)
	voi.Update()
	data = voi.GetOutput()
	return data
	
def saveImageAs(imagedata, zslice, filename):
	"""
	Created: KP
	Description: Save a given slice of a volume
	"""		  
	if not filename:
		return
	ext = filename.split(".")[-1]		   
	extMap = {"tiff": "TIFF", "tif": "TIFF", "jpg": "JPEG", "jpeg": "JPEG", "png": "PNG"}
	if not extMap.has_key(ext):
		GUI.Dialogs.showerror(None, "Extension not recognized: %s" % ext, "Extension not recognized")
		return
	vtkclass = "vtk.vtk%sWriter()" % extMap[ext]
	writer = eval(vtkclass)
	img = getSlice(imagedata, zslice)
	writer.SetInputConnection(img.GetProducerPort())
	writer.SetFileName(filename)
	writer.Write()
	
def imageDataTo3Component(image, ctf):
	"""
	Created: 22.07.2005, KP
	Description: Processes image data to get it to proper 3 component RGB data
	"""			
	image.UpdateInformation()
	ncomps = image.GetNumberOfScalarComponents()
	#print "ncomps = ", ncomps
	
	if ncomps == 1:
		maptocolor = vtk.vtkImageMapToColors()
		maptocolor.SetInputConnection(image.GetProducerPort())
		maptocolor.SetLookupTable(ctf)
		maptocolor.SetOutputFormatToRGB()
		#maptocolor.Update()
		imagedata = maptocolor.GetOutput()
	elif ncomps > 3:
		Logging.info("Data has %d components, extracting"%ncomps, kw = "imageop")
		extract = vtk.vtkImageExtractComponents()
		extract.SetComponents(0, 1, 2)
		extract.SetInputConnection(image.GetProducerPort())
		imagedata = extract.GetOutput()

	else:
		imagedata = image
	#imagedata.Update()
	return imagedata
