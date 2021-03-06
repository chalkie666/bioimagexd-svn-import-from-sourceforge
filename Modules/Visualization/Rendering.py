# -*- coding: iso-8859-1 -*-

"""
 Unit: Rendering
 Project: BioImageXD
 Description:

 A 3D rendering mode for Visualizer
		   
 Copyright (C) 2005	 BioImageXD Project
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
import GUI.Dialogs
import GUI.MenuManager
import Modules
import Visualizer.Lights as Lights
import Visualizer.VisualizationFrame as VisualizationFrame
from Visualizer.VisualizationMode import VisualizationMode
import Visualizer.VisualizerWindow as VisualizerWindow
import wx
import Logging

def getName():
	"""
	Description:Return the name of this visualization mode (used to identify mode internally)
	"""
	return "3d"

def isDefaultMode():
	"""
	Return a boolean indicating whether this mode should be used as the default visualization mode
	"""
	return 0

def showInfoWindow():
	"""
	Return a boolean indicating whether the info window should be kept visible when this mode is loaded
	"""
	return 1

def showFileTree():
	"""
	Return a boolean indicating whether the file tree should be kept visible when this mode is loaded
	"""
	return 1

def showSeparator():
	"""
	return two boolean values indicating whether to place toolbar separator before or after this icon
	"""
	return (0, 0)

def getToolbarPos():
	"""
	return requested toolbar position for this visualization mode
	"""
	return 8

def getIcon():
	"""
	return the icon name for this visualization mode
	"""
	return "Vis_3D.png"

def getShortDesc():
	"""
	return a short description (used as menu items etc.) of this visualization mode
	"""
	return "3D mode"

def getDesc():
	"""
	return a description (used as tooltips etc.) of this visualization mode
	"""
	return "Render the dataset in three dimensions" 

def getClass():
	"""
	return the class that is instantiated as the actual visualization mode
	"""
	return RenderingMode

def getImmediateRendering():
	"""
	Return a boolean indicating whether this mode should in general update it's 
				 rendering after each and every change to a configuration affecting the rendering
	"""
	return False

def getConfigPanel():
	"""
	return the class that is instantiated as the configuration panel for the mode
	"""
	return None

def getRenderingDelay():
	"""
	return a value in milliseconds that is the minimum delay between two rendering events being sent
				 to this visualization mode. In general, the smaller the value, the faster the rendering should be
	"""
	return 5000

def showZoomToolbar():
	"""
	return a boolean indicating whether the visualizer toolbars (zoom, annotation) should be visible 
	"""
	return True
		
class RenderingMode(VisualizationMode):

	def __init__(self, parent, visualizer):
		"""
		Initialization
		"""
		VisualizationMode.__init__(self, parent, visualizer)
		self.PitchStep, self.YawStep, self.RollStep, self.ElevationStep = 2, 2, 2, 5
		self.parent = parent
		self.menuManager = visualizer.menuManager
		self.visualizer = visualizer
		self.wxrenwin = None
		self.timepoint = 0
		self.mapping = Modules.DynamicLoader.getRenderingModules()
		self.first = 1
		self.lightsManager = None
		self.configPanel = None
		self.dataUnit = None
		self.initialized = False
		self.nameToModule = {}
		self.defaultModule = "Volume rendering"
		self.modules = []
		
	def getRenderWindow(self):
		"""
		return a render window, if this mode uses one
		"""
		return self.renwin
		
	def reloadModules(self):
		"""
		Reload all the visualization modules.
		"""
		for key in self.mapping.keys():
			mod, conf, module = self.mapping[key]
			module = reload(module)
			self.mapping[key] = (mod, conf, module)
			
	def zoomObject(self):
		"""
		Zoom to a user selected portion of the image
		"""
		self.wxrenwin.zoomToRubberband()

	def showSideBar(self):
		"""
		Method that is queried to determine whether
					 to show the sidebar
		"""
		return True

	def getSidebarWinOrigSize(self):
		"""
		Return default size of sidebar win
		"""
		return (200,500)

	def showViewAngleCombo(self):
		"""
		Method that is queried to determine whether
					 to show the view angle combo box in the toolbar
		"""
		return True

	def setStereoMode(self, mode):
		"""
		Set the stereo rendering mode
		"""
		if mode:
			self.renwin.StereoRenderOn()
			cmd = "self.renwin.SetStereoTypeTo%s()" % mode
			eval(cmd)
		else:
			self.renwin.StereoRenderOff()
			
	def getSidebarWindow(self):
		"""
		return the sidebar window
		"""
		return self.configPanel
  
	def activate(self, sidebarwin):
		"""
		Set the mode of visualization
		"""
		scripting.preferRGB = 0
		scripting.wantAlphaChannel = 1
		scripting.wantWholeDataset = 1
		self.sidebarWin = sidebarwin
		# If we're preloading, don't create the render window
		# since it will mess up the rendering

		if not self.wxrenwin and not self.visualizer.preload:
			self.wxrenwin = VisualizerWindow.VisualizerWindow(self.parent, size = (512, 512))
			self.wxrenwin.Render()
			self.GetRenderWindow = self.wxrenwin.GetRenderWindow
			self.renwin = self.wxrenwin.GetRenderWindow()
			self.wxrenwin.Render()
			self.iactivePanel = self.wxrenwin
			scripting.renderWindow = self.renwin
			scripting.renderer = self.wxrenwin.getRenderer()
			self.getRenderer = self.GetRenderer = self.wxrenwin.getRenderer

		else:
			self.wxrenwin.iren.Enable()

		if not self.configPanel:
			# When we embed the sidebar in a sashlayoutwindow, the size
			# is set correctly
			self.container = wx.SashLayoutWindow(self.sidebarWin)
			
			self.configPanel = VisualizationFrame.ConfigurationPanel(self.container, self.visualizer, self)

		self.container.Show()
		self.configPanel.Show()

		if not self.lightsManager:
			self.lightsManager = Lights.LightManager(self.parent, self.wxrenwin, self.getRenderer(), mode = 'raymond')

		mgr = self.menuManager
		
		self.visualizer.tb.EnableTool(GUI.MenuManager.ID_ZOOM_TO_FIT, 0)
		
		if not scripting.TFLag:
			mgr.enable(GUI.MenuManager.ID_LIGHTS, self.configPanel.onConfigureLights)
		#mgr.enable(GUI.MenuManager.ID_RENDERWIN, self.configPanel.onConfigureRenderwindow)
		mgr.addMenuItem("file", GUI.MenuManager.ID_LOAD_SCENE, "Open 3D view scene...", \
						"Open a 3D view scene file", self.configPanel.onOpenScene, \
						before = GUI.MenuManager.ID_IMPORT_IMAGES)
		mgr.addMenuItem("file", GUI.MenuManager.ID_SAVE_SCENE, "Save 3D view scene...", \
						"Save a 3D view scene", self.configPanel.onSaveScene, \
						before = GUI.MenuManager.ID_IMPORT_IMAGES)
		mgr.addSeparator("file", sepid = GUI.MenuManager.ID_SEPARATOR, \
							before = GUI.MenuManager.ID_IMPORT_IMAGES)
							
							
		self.visualizer.pitch.Bind(wx.EVT_SPIN_UP, self.onPitchUp)
		self.visualizer.pitch.Bind(wx.EVT_SPIN_DOWN, self.onPitchDown)
		self.visualizer.yaw.Bind(wx.EVT_SPIN_UP, self.onYawUp)
		self.visualizer.yaw.Bind(wx.EVT_SPIN_DOWN, self.onYawDown)
		self.visualizer.roll.Bind(wx.EVT_SPIN_UP, self.onRollUp)
		self.visualizer.roll.Bind(wx.EVT_SPIN_DOWN, self.onRollDown)
		self.visualizer.elevation.Bind(wx.EVT_SPIN_UP, self.onElevationUp)
		self.visualizer.elevation.Bind(wx.EVT_SPIN_DOWN, self.onElevationDown)
		
		return self.wxrenwin
		
	def saveSnapshot(self, filename):
		"""
		Save a snapshot of the scene
		"""
		self.wxrenwin.save_screen(filename)
		
	def Render(self):
		"""
		Update the rendering
		"""
		self.wxrenwin.Render()
		
	def onElevationUp(self, evt):
		"""
		adjust the elevation of the 3D scene upwards
		"""
		self.getRenderer().GetActiveCamera().Elevation(self.ElevationStep)
		self.Render()

	def onElevationDown(self, evt):
		"""
		adjust the elevation of the 3D scene downwards
		"""
		self.getRenderer().GetActiveCamera().Elevation(-self.ElevationStep)
		self.Render()

	def onPitchUp(self, evt):
		"""
		adjust the pitch of the 3D scene upwards
		"""	
		self.getRenderer().GetActiveCamera().Pitch(self.PitchStep)
		self.Render()

	def onPitchDown(self, evt):
		"""
		adjust the pitch of the 3D scene downwards
		"""	
		self.getRenderer().GetActiveCamera().Pitch(-self.PitchStep)
		self.Render()

	def onRollUp(self, evt):
		"""
		adjust the roll of the 3D scene upwards
		"""
		self.getRenderer().GetActiveCamera().Roll(self.RollStep)
		self.Render()

	def onRollDown(self, evt):
		"""
		adjust the roll of the 3D scene downwards
		"""	
		self.getRenderer().GetActiveCamera().Roll(-self.RollStep)
		self.Render()

	def onYawUp(self, evt):
		"""
		adjust the yaw of the 3D scene upwards
		"""	
		self.getRenderer().GetActiveCamera().Yaw(self.YawStep)
		self.Render()

	def onYawDown(self, evt):
		"""
		adjust the yaw of the 3D scene upwards
		"""	
		self.getRenderer().GetActiveCamera().Yaw(-self.YawStep)
		self.Render()
			
	def setBackground(self, r, g, b):
		"""
		Set the background color
		"""
		ren = self.wxrenwin.getRenderer()
		ren.SetBackground(r / 255.0, g / 255.0, b / 255.0)
		
	def updateRendering(self):
		"""
		Update the rendering
		"""
		if not self.wxrenwin.enabled:
			Logging.info("Visualizer is disabled, won't render 3D scene", kw="visualizer")
			return
		for module in self.modules:
			module.showTimepoint(self.timepoint)
		self.wxrenwin.Render()
		
	def deactivate(self, newmode = None):
		"""
		Unset the mode of visualization
		"""
		mgr = self.menuManager
		mgr.remove(GUI.MenuManager.ID_SAVE_SCENE)
		mgr.remove(GUI.MenuManager.ID_LOAD_SCENE)
		mgr.removeSeparator(GUI.MenuManager.ID_SEPARATOR)
		
		self.visualizer.tb.EnableTool(GUI.MenuManager.ID_ZOOM_TO_FIT, 1)
		if self.wxrenwin:
			self.wxrenwin.Show(0)
			self.wxrenwin.iren.Disable()
		self.container.Show(0)
		self.configPanel.Show(0)
		mgr = self.menuManager
		if not scripting.TFLag:
			mgr.disable(GUI.MenuManager.ID_LIGHTS)
		#mgr.disable(GUI.MenuManager.ID_RENDERWIN)
		
		self.visualizer.pitch.Unbind(wx.EVT_SPIN_UP)
		self.visualizer.pitch.Unbind(wx.EVT_SPIN_DOWN)
		self.visualizer.yaw.Unbind(wx.EVT_SPIN_UP)
		self.visualizer.yaw.Unbind(wx.EVT_SPIN_DOWN)
		self.visualizer.roll.Unbind(wx.EVT_SPIN_UP)
		self.visualizer.roll.Unbind(wx.EVT_SPIN_DOWN)
		self.visualizer.elevation.Unbind(wx.EVT_SPIN_UP)
		self.visualizer.elevation.Unbind(wx.EVT_SPIN_DOWN)

		dataunit = self.getDataUnit()
		if dataunit:
			dataunit.resetColorTransferFunction()

		
	def setDataUnit(self, dataUnit):
		"""
		Set the dataunit to be visualized
		"""
		self.dataUnit = dataUnit
		print "Setting dataunit, modules=",self.modules, dataUnit
		if not len(self.modules):
			# we instruct loadModule not to render the scene, software
			# we can set the view before rendering
			module = self.loadModule(self.defaultModule, render = 0)
			module.setView((1, 1, 1, 0, 0, 1))
			module.showTimepoint(self.timepoint)
			self.configPanel.appendModuleToList(self.defaultModule)
		if dataUnit:
			for module in self.modules:
				module.setDataUnit(dataUnit)
			
	def getConfigurationPanel(self, name):
		"""
		Return the configuration panel of a module
		"""
		conf = None
		return self.mapping[name][1]

	def removeModule(self, name):
		"""
		Remove a visualization module
		"""
		to_be_removed = []
		if name in self.nameToModule:
			del self.nameToModule[name]
		for module in self.modules:
			if module.getName() == name:
				to_be_removed.append(module)
		for module in to_be_removed:
			module.disableRendering()
			self.modules.remove(module)
			del module

	def setRenderingStatus(self, name, status):
		"""
		Enable / disable rendering of a module
		"""
		for module in self.modules:
			if module.getName() == name:
				if not status:
					module.disableRendering()
				else:
					module.enableRendering()

	def getModule(self, name):
		"""
		return the module with the given name
		"""
		return self.nameToModule.get(name,None)
		

	def loadModule(self, name, lbl = None, render = 1):
		"""
		Load a visualization module
		"""
		if not lbl:
			lbl = name
		if not self.dataUnit and lbl not in ["Protein Data Bank"]:
			GUI.Dialogs.showerror(self.parent, \
									"No dataset has been loaded for visualization", \
									"Cannot load visualization module")
			return
		if not self.initialized:
			self.wxrenwin.initializeVTK()
			self.initialized = 1
		module = self.mapping[name][0](self, self.visualizer, label = lbl, moduleName = name)
		self.modules.append(module)
		self.nameToModule[name] = module
		module.setDataUnit(self.dataUnit)
		if render:
			module.showTimepoint(self.timepoint)
		return module
			
	def getModules(self):
		"""
		Return the modules
		"""	 
		return self.modules
		
	def setTimepoint(self, tp):
		"""
		Set the timepoint to be visualized
		"""
		self.timepoint = tp
		for module in self.modules:
			module.showTimepoint(self.timepoint)

	def __getstate__(self):
		"""
		A getstate method that saves the lights
		"""
		print "Saving state, modules = ",self.modules
		odict = {"lightsManager":self.lightsManager,
			   "timepoint":self.timepoint,
			   "modules":self.modules}
		return odict
		
	def __set_pure_state__(self, state):
		"""
		Set the state of the light
		"""
		self.lightsManager.__set_pure_state__(state.lightsManager)
		self.setTimepoint(state.timepoint)
		for module in self.modules:
			self.removeModule(module.getName())
		for module in state.modules:
			name = module.moduleName
			label = module.name
			mod = self.loadModule(name, label, 0)
			self.configPanel.appendModuleToList(label)
			mod.__set_pure_state__(module)

	def zoomToFit(self):
		"""
		Zoom the dataset to fit the available screen space
		"""
		pass
		
