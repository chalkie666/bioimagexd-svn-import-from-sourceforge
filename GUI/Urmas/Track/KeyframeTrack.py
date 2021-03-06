# -*- coding: iso-8859-1 -*-

"""
 Unit: KeyframeTrack
 Project: BioImageXD
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 Urmas is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 The widgets that implement the Tracks of the timeline are implemented in this module.

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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

from GUI.Urmas.UrmasPalette import UrmasDropTarget
from GUI.Urmas.TrackItem.KeyframePoint import KeyframePoint
from GUI.Urmas.TrackItem.KeyframePoint import KeyframeEndPoint
import lib.messenger
import Logging
from SplineTrack import SplineTrack

class KeyframeTrack(SplineTrack):
	"""
	A class representing a Keyframe track in the timeline
	"""
	def __init__(self, name, parent, **kws):
		self.nameColor = (255, 51, 153)
		self.fg = (0, 0, 0)
		self.bg = self.nameColor
		
		# A flag that indicates that keyframe track is similiar to
		# camera path track in that it defines the camera movement
		self.trackType = "DEFINE_CAMERA"
		
		kws["height"] = 80

		SplineTrack.__init__(self, name, parent, **kws)
		
		self.paintOverlay = 1
		self.overlayColor = ((0, 255, 0), 25)        
		
		self.itemClass = kws.get("item", KeyframePoint)
		dt = UrmasDropTarget(self, "Keyframe")
		self.SetDropTarget(dt)
		lib.messenger.connect(None, "set_camera", self.onSetCamera)
		lib.messenger.connect(None, "show_time_pos", self.onDisableOverlay)

	def onDisableOverlay(self, obj, evt, *arg):
		"""
		Disable the overlay when the user uses the timeslider
		"""        
		self.overlayPos = -1
		self.overlayItem = None
		
	def onDown(self, event):
		"""
		Item is clicked
		"""
		ret = SplineTrack.onDown(self, event)
		if self.overlayItem and self.overlayPos != -1:
			lib.messenger.send(None, "set_timeslider_value", self.overlayPos * 10.0)
			lib.messenger.send(None, "render_time_pos", self.overlayPos)
			self.paintTrack()
			self.Refresh()
			return ret
		return ret
			
	def onSetCamera(self, obj, evt, cam):
		"""
		Set the camera for the current item
		"""             
		#print "overlayItem=",self.overlayItem
		if self.overlayItem:    
			self.overlayItem.getThumbnail()
			self.overlayItem.drawItem()
			self.paintTrack()
			#self.Refresh()
			
	def AcceptDrop(self, x, y, data):
		"""
		Method called to indicate that a user is no longer dragging
					 something to this track
		"""     
		oldlen = len(self.items)
		pos = self.dragEndPosition
		if pos == -1:
			pos = len(self.items) - 1
		if pos == len(self.items):
			pos -= 1
		Logging.info("Adding keyframe at pos ", pos, kw = "animator")
		self.addKeyframePoint(pos)
		pos = pos + 1
		self.Refresh()
		self.Layout()
				
		# If there were no items before this, then expand to max
		#if not oldlen:
		#    self.expandToMax()
			
	def removeItem(self, position):
		"""
		Remove an item from this track
		"""
		self.removeItem(position)
		#self.showKeyframe()
		self.Layout()
		#self.sizer.Fit(self)     
		
	def addKeyframePoint(self, position, update = 1, **kws):
		"""
		A method to add a new item to this track
		"""
		h = self.height
		itemkws = {"itemnum":position, "editable":self.editable}
		if "add_endpoint" not in kws:
			item = self.itemClass(self, "%d" % position, (20, h), **itemkws)
			if self.color:
				item.setColor(self.color, self.headercolor)
			if position >= len(self.items):
				Logging.info("Appending item ", item.itemnum, kw = "animator")
				self.items.append(item)
			else:
				Logging.info("Inserting item ", item.itemnum, kw = "animator")
				self.items.insert(position, item)
			# +1 accounts for the empty item
		spc = 0
		# if this is the first item to be added, then we insert an endpoint
		# as well. Also by having kw add_endpoint in kws, it is possible
		# to only insert the endpoint
		if "add_endpoint" in kws or (len(self.items) == 1 and "no_endpoint" not in kws):
			item = KeyframeEndPoint(self, "", (20, h), **itemkws)
			self.items.append(item)        
		for i, item in enumerate(self.items):
			if not item.isStopped():
				self.items[i].setItemNumber(spc)
				self.items[i].setText("%d" % spc)
				spc += 1
				if update:
					self.items[i].updateItem()
					self.items[i].drawItem()

		self.updatePositions()

		if update:
			self.paintTrack()
			self.Refresh()
			#self.sizer.Fit(self)
		return item
			
	def __getstate__(self):
		"""
		Return the dict that is to be pickled to disk
		"""      
		odict = SplineTrack.__getstate__(self)
		#n=0
		#pos=0
		#for key in ["closed","maintainUpDirection"]:
		#    odict[key]=self.__dict__[key]
		return odict        
		
	def setSelected(self, event):
		"""
		Selects this track
		""" 
		SplineTrack.setSelected(self, event)
		if event:
			self.showKeyframe()
			#self.control.setKeyframeInteractionCallback(self.updateLabels)        
			
	def showKeyframe(self):
		"""
		Show Keyframe represented by this track
		""" 
		lib.messenger.send(None, "set_keyframe_mode", 1)
		self.splineEditor.setViewMode(1)
			
			
	def __set_pure_state__(self, state):
		"""
		Method called by UrmasPersist to allow the object
					 to refresh before it's items are created
		"""
		#SplineTrack.__set_pure_state__(self, state)
		spc = 0
		
		for i, item in enumerate(state.items[:-1]):
			if not "stopitem" in  dir(item):
				Logging.info("Add Keyframe point spc=%d,i=%d, itemnum=%d" % (spc, i, item.itemnum), kw = "animator")
				tp = self.addKeyframePoint(spc, 0, point = item.point, no_endpoint = 1)
				tp.__set_pure_state__(item)
				
				spc += 1
			else:
				Logging.info("Add stop point i=%d, itemnum=%d" % (i, item.itemnum), kw = "animator")
				tp = self.addStopPoint(i)
				tp.__set_pure_state__(item)
				
		# Add the endpoint manually
		tp = self.addKeyframePoint(spc, 0, point = state.items[-1].point, add_endpoint = 1)
		tp.__set_pure_state__(state.items[-1])
		
		
		#self.updatePositions()
		for i, item in enumerate(self.items):
			item.updateThumbnail()
			item.drawItem()
		self.paintTrack()
		
		
