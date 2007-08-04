# -*- coding: iso-8859-1 -*-

"""
 Unit: PainterHelpers
 Project: BioImageXD
 Created: 24.03.2005, KP
 Description:

 A module containing painter helper classes that work together with Interactive Panel
		 
 Copyright (C) 2007	 BioImageXD Project
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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import scripting
import lib.messenger
import math
import wx

def registerHelpers(interactivePanel):
	"""
	Created: 04.08.2007, KP
	Description: register the painter helpers to the interactive panel
	"""
	interactivePanel.registerPainter( AnnotationHelper(interactivePanel) )
	interactivePanel.registerPainter( CenterOfMassHelper(interactivePanel) )
	interactivePanel.registerPainter( VisualizeTracksHelper(interactivePanel) )
	

class PainterHelper:
	"""
	Created: 06.10.2006, KP
	Description: A base class for adding behaviour to the painting of the previews
				 in a standard way, that can be used for example to implement different
				 kinds of highlighting, annotations etc.
	"""
	def __init__(self, parent):		   
		self.parent = parent
		
		
	def setParent(self, parent):
		"""
		Created: 02.07.2007, KP
		Description: set the parent
		"""		   
		self.parent = parent
	def paintOnDC(self, dc):
		"""
		Created: 06.10.2006, KP
		Description: A method that is used to paint whatever this helper wishes to paint
					 on the DC
		"""
		pass
		
class VisualizeTracksHelper(PainterHelper):
	"""
	Created: 21.11.2006, KP
	Description: A helper for painting the tracks
	"""
	def __init__(self, parent):
		"""
		Created: 21.11.2006, KP
		Description: Initialize the helper
		"""
		PainterHelper.__init__(self, parent)
		self.selectedTracks = []
		lib.messenger.connect(None, "visualize_tracks", self.onShowTracks)		  
		
	def onShowTracks(self, obj, evt, tracks):
		"""
		Created: 25.09.2006, KP
		Description: Show the selected tracks
		"""
		if not tracks:
			return
		self.selectedTracks = tracks
		
				
	def paintOnDC(self, dc):			   
		"""
		Created: 21.11.2006, KP
		Description: Paint the selected tracks to the DC
		"""
		if self.selectedTracks:
			xc, yc, wc, hc = self.parent.GetClientRect()
			dc.SetPen(wx.Pen((255, 255, 255), 1))
			dc.SetBrush(wx.TRANSPARENT_BRUSH)
			for track in self.selectedTracks:
				mintp, maxtp = track.getTimeRange() 
				val = -1
				while val == -1 and mintp <= maxtp:
					val, (x0, y0, z0) = track.getObjectAtTime(mintp)
					x0 *= self.parent.zoomFactor
					y0 *= self.parent.zoomFactor
					x0 += self.parent.xoffset
					y0 += self.parent.yoffset	  
					x0 += xc
					y0 += yc
					mintp += 1
				dc.SetTextForeground((255, 255, 255))
				self.drawTimepoint(dc, mintp - 1, x0, y0)
				
				for i in range(mintp, maxtp + 1):
					objectValue, pos = track.getObjectAtTime(i)
					if objectValue != -1:
						x1, y1, z1 = pos
						
						x1 *= self.parent.zoomFactor
						y1 *= self.parent.zoomFactor
						x1 += self.parent.xoffset
						y1 += self.parent.yoffset				 
						
						x1 += xc
						y1 += yc
						self.drawTimepoint(dc, i, x1, y1)						 
							
						def angle(x_1, y_1, x_2, y_2):
							ang = math.atan2(y_2 - y_1, x_2 - x_1) * 180.0 / math.pi
							ang = math.atan2(y_2 - y_1, x_2 - x_1) * 180.0 / math.pi
							ang2 = ang
							#if ang<0:ang=180+ang
							return ang
							
						if x0 != x1:
							dc.DrawLine(x0, y0, x1, y1)
							a1 = angle(x0, y0, x1, y1)
							if 0:
								ang = ang * ((2 * math.pi) / 360.0)
								#l=5*self.parent.zoomFactor
								xs = 5
								ys = 5
								xs *= self.parent.zoomFactor
								ys *= self.parent.zoomFactor
								x2 = math.cos(ang) * xs - math.sin(ang) * ys
								y2 = math.sin(ang) * xs + math.cos(ang) * ys
								x2 += x0
								y2 += y0
								dc.DrawLine(x0, y0, x2, y2)
								l = 5 * self.parent.zoomFactor
								xs = -5
								ys = 5
								xs *= self.parent.zoomFactor
								ys *= self.parent.zoomFactor								
								x2 = math.cos(ang) * xs - math.sin(ang) * ys
								y2 = math.sin(ang) * xs + math.cos(ang) * ys
								x2 += x0
								y2 += y0
								dc.DrawLine(x0, y0, x2, y2)								   
						
							
						x0, y0 = x1, y1
						
	def drawTimepoint(self, dc, tp, x, y):
		"""
		Created: 26.11.2006, KP
		Description: Draw the text label for given timepoint
		"""
		if tp != scripting.visualizer.getTimepoint():
			dc.SetFont(wx.Font(7, wx.SWISS, wx.NORMAL, wx.NORMAL))
			dc.DrawCircle(x, y, 3)
		else:
			dc.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL))
			dc.DrawCircle(x, y, 5)
		dc.DrawText("%d" % (tp), x - 10, y)
	
class CenterOfMassHelper(PainterHelper):
	def __init__(self, parent):
		"""
		Created: 21.11.2006, KP
		Description: Initialize the helper
		"""
		PainterHelper.__init__(self, parent)
		self.centerOfMass = None
		lib.messenger.connect(None, "show_centerofmass", self.onShowCenterOfMass)
		
	def onShowCenterOfMass(self, obj, evt, label, centerofmass):
		"""
		Created: 04.07.2006, KP
		Description: Show the given center of mass
		"""			   
		self.centerOfMass = (label, centerofmass)
		
		
	def paintOnDC(self, dc):
		"""
		Created: 21.11.2006, KP
		Description: Paint the contents
		"""
		if self.centerOfMass:
			label, (x, y, z) = self.centerOfMass
			
			x *= self.parent.zoomFactor
			y *= self.parent.zoomFactor
			x += self.parent.xoffset
			y += self.parent.yoffset
			x0, y0, w, h = self.parent.GetClientRect()
			x += x0
			y += y0
			dc.SetBrush(wx.TRANSPARENT_BRUSH)
			dc.SetPen(wx.Pen((255, 255, 255), 2))
			dc.DrawCircle(x, y, 10)
			dc.SetTextForeground((255, 255, 255))
			dc.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
			dc.DrawText("%d" % label, x - 5, y - 5)	   
	
class AnnotationHelper(PainterHelper):
	"""
	Created: 06.10.2006, KP
	Description: A class that capsulates the behaviour of drawing the annotations
	"""
	def __init__(self, parent):
		PainterHelper.__init__(self, parent)
				
	def paintOnDC(self, dc):
		"""
		Created: 06.10.2006, KP
		Description: Paint the annotations on a DC
		"""
		self.parent.diagram.Redraw(dc)
		
		
	def setParent(self, parent):
		"""
		Created: 02.07.2007, KP
		Description: set the parent
		"""		   
		self.parent = parent		