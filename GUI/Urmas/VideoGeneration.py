#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: VideoGeneration
 Project: BioImageXD
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This module contains a panel that can be used to control the creation of a movie
 out of a set of rendered images.
 
 Copyright (C) 2005	 BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
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


import Configuration
import GUI.Dialogs
import lib.messenger
import lib.RenderingInterface
import Logging
import math
import platform
import os
import scripting
import sys
import wx
import subprocess

class VideoGenerationDialog(wx.Dialog):
	"""
	a dialog for re-encoding a project based on a project file
	"""
	def __init__(self, parent, filename):
		wx.Dialog.__init__(self, parent, -1)
		self.sizer = wx.GridBagSizer(10,10)
		
		self.videoGeneration = VideoGeneration(self, filename = filename)
		self.sizer.Add(self.videoGeneration,(0,0),flag=wx.EXPAND|wx.ALL)
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.sizer.Fit(self)
		
		lib.messenger.connect(None, "video_generation_close", self.onClose)

	def disableFrameDeletion(self):
		"""
		disable the option to delete the frames / save a projet
		"""
		self.videoGeneration.disableFrameDeletion()
		
	def onClose(self, *args):
		"""
		close the dialog
		"""
		self.Close()
		if self.videoGeneration.abort:
			self.EndModal(wx.ID_CANCEL)
		else:
			self.EndModal(wx.ID_OK)

class VideoEncoder:
	"""
	Description: a class encapsulating the logic for rendering a list of frames into a movie
	"""
	def __init__(self):
		self.quality = 0
		self.path = ""
		self.name = ""
		self.codec = "QuickTime MPEG4"
		self.size = (320,240)
		self.frameList = []
		self.fps = 15
		self.videoFileName = ""
		self.outputCodecs = {"MPEG1":("mpeg1video", "mpg"), "MPEG2":("mpeg2video", "mpg"), \
							"WMV1":("wmv1", "wmv"), "WMV2":("wmv2", "wmv"), "MS MPEG4":("msmpeg4", "avi"), \
							"MS MPEG4 v2":("msmpeg4v2", "avi"), "QuickTime MPEG4":("mpeg4", "mov"), "AVI MPEG4":("mpeg4", "avi")}
		self.presets = [(0, 0, 0,""), ((720, 576), (25), 6000, "pal-dvd"), ((720, 480), (29.97), 6000,"ntsc-dvd")]
		self.bitrate = 0
		self.target = ""
		self.format = ""
		self.preset = 0
		
		
	def getExtensionForCodec(self, codec):
		"""
		return the proper file extension for given codec
		"""
		if codec not in self.outputCodecs:return ""
		return self.outputCodecs[codec][1]
		
	def getFrameAmount(self): 
		"""
		return the number of frames
		"""
		return len(self.frameList)
	
	def getFormat(self): return self.format
	def setFormat(self, format):
		"""
		set the format of the filenames
		"""
		self.format = format
	def getPreset(self): return self.preset
	def setPreset(self, i):
		"""
		set the parameters according to the given preset
		"""
		if not self.preset and i:
			self.oldSize, self.oldFps, self.oldBitrate, self.oldTarget = self.size, self.fps, self.bitrate, self.target
		
		if self.preset and not i:
			self.size, self.fps, self.bitrate, self.target = self.oldSize, self.oldFps, self.oldBitrate, self.oldTarget
		self.preset = i
		if i:
			self.size, self.fps, self.bitrate, self.target = self.presets[i]
				
	def getVideoFileName(self): return self.videoFileName
	def setVideoFileName(self, name):
		"""
		set the video file name
		"""
		self.videoFileName = name
	
	def getFPS(self): return self.fps
	def setFPS(self, fps):
		"""
		set the frames per second
		"""
		self.fps = fps
		
	def getFrameList(self): return self.frameList
	def setFrameList(self, frameList):
		"""
		set the frame list
		"""
		self.frameList = frameList
		
	def getSize(self): return self.size
	def setSize(self, w, h):
		"""
		set the frame size
		"""
		self.size = (w, h)

	def getQuality(self): return self.quality
	def setQuality(self, quality):
		"""
		set the quality of the rendered video
		"""
		self.quality = quality
		
	def getPath(self): return self.path
	def setPath(self, path):
		"""
		set the path in which the frames are located
		"""
		self.path = path
		
	def getFrameName(self): return self.name
	def setFrameName(self, name):
		"""
		Set the frame name
		"""
		self.name = name
		
	def getCodec(self): return (self.codec)
	def setCodec(self, codec):
		"""
		Set the codec ) used to render the movie
		"""
		self.codec = codec
		
	def encode(self):
		"""
		encode the movie
		"""
		codec = self.getCodec()
		vcodec, ext = self.outputCodecs[codec]
		#file_coms = self.videoFileName.split(".")
		#file_coms[-1] = ext
		#file = ".".join(file_coms)
		
		cmdLine = self.getCommandLine(vcodec, self.videoFileName)
		if not os.path.exists(cmdLine[0]):
			GUI.Dialogs.showmessage(self, "Encoding failed: FFMPEG binary %s does not exist!" % ffmpeg, "Encoding failed")
			return False
		subprocess.call(cmdLine)
		return True
		
	def deleteFrames(self):
		"""
		clean up the frames after the rendering
		"""
		for file in self.frameList:
			os.unlink(file)
		self.frameList = []
		
	def writeOut(self, filename):
		"""
		write out a project file with the necessary info
		"""
		f = open(filename,"w")
		f.write("%s # video file\n"%self.videoFileName)
		f.write("%s # frame name\n"%self.name)
		f.write("%s # frame path\n"%self.path)
		f.write("%d # quality\n"%self.quality)
		f.write("%d # preset\n"%self.preset)
		f.write("%s # codec\n"%self.codec)
		f.write("%d, %d # frame size\n"%self.size)
		f.write("%f # fps\n"%self.fps)
		f.write("%s # filename format\n"%self.format)
		for file in self.frameList:
			f.write("%s\n"%file)
		f.close()
		
	def readIn(self, filename):
		"""
		read a project file with the information necessary 
		"""
		f = open(filename, "r")
		lines = []
		inputLines = f.readlines()
		
		for line in inputLines[0:9]:
			txt, comment = line.split(" #")
			lines.append(txt)
		videoFile, name, path, quality, preset, codec, size, fps, format = lines[0:9]
		quality = int(quality)
		fps = float(fps)
		w, h = size.split(",")
		self.size = (int(w), int(h))
		self.videoFileName = videoFile
		self.name = name
		self.path = path
		self.quality = quality
		self.codec = codec
		self.fps = fps
		self.format = format
		self.frameList = inputLines[9:]
		self.setPreset(int(preset))
		
	def getPattern(self):
		"""
		return the filename pattern
		"""
		if not self.format:
			renderingInterface = lib.RenderingInterface.getRenderingInterface()
			pattern = renderingInterface.getFilenamePattern()
			framename = renderingInterface.getFrameName()
			self.setFrameName(framename)
			self.setFormat(pattern)
		else:
			framename = self.getFrameName()
			pattern = self.getFormat()

		# FFMPEG uses %3d instead of %.3d for files numbered 000 - 999
		pattern = pattern.replace("%.", "%")
		pattern = pattern.split(os.path.sep)[-1]
		pattern = pattern.replace("%s", framename)
		pattern = os.path.join(self.getPath(), pattern)
		Logging.info("Pattern for files = ", pattern, kw = "animator")
		return pattern

	def getCommandLine(self, vcodec, filename):
		"""
		return the command line for using ffmpeg to render the video
		"""
		target = ""
		pattern = self.getPattern()
		if self.preset != 0:
			(x, y), fps, br, target = self.presets[self.preset]
		
		cmdLine = []
		if not scripting.main_is_frozen():
			ffmpegs = {"linux": "bin/ffmpeg", "linux2": "bin/ffmpeg", "win32": "bin\\ffmpeg.exe", "darwin": "bin/ffmpeg.osx"}
		else:
			ffmpegs = {"linux": "bin/ffmpeg", "linux2": "bin/ffmpeg", "win32": "bin\\ffmpeg.exe", "darwin": "../Resources/Bin/ffmpeg.osx"}
		ffmpeg = "ffmpeg"
		for i in ffmpegs.keys():
			if i == sys.platform:
				ffmpeg = ffmpegs[i]
				break
			
			
		bindir = scripting.get_main_dir()
		ffmpeg = os.path.join(bindir, ffmpeg)
		cmdLine.append(ffmpeg)
		# scale the quality into the range understood by ffmpeg
		quality = 11 - self.quality
		quality = math.ceil(1 + (3.22222 * (quality - 1)))
		frameRate = self.fps
		width, height = self.getSize()

		if not target:
			cmdLine.append("-y")
			cmdLine.append("-qscale")
			cmdLine.append("%d"%quality)
			cmdLine.append("-r")
			cmdLine.append("%.2f"%frameRate)
			cmdLine.append("-s")
			cmdLine.append("%dx%d"%(width, height))
			cmdLine.append("-i")
			cmdLine.append('%s'%pattern)
			cmdLine.append('-vcodec')
			cmdLine.append('%s'%vcodec)
			cmdLine.append('%s'%filename)
			#commandLine = "\"%s\" -y -qscale %d -r %.2f -s %dx%d -i \"%s\" -vcodec %s \"%s\"" \
			#				% (ffmpeg, quality, frameRate, width, height, pattern, vcodec, file)
		else:
			#commandLine = "\"%s\" -y -qscale %d -s %dx%d -i \"%s\" -target %s \"%s\"" % (ffmpeg, quality, width, height, pattern, target, file)
			cmdLine.append("-y")
			cmdLine.append("-qscale")
			cmdLine.append("%d"%quality)
			cmdLine.append("-s")
			cmdLine.append("%dx%d"%(width, height))
			cmdLine.append("-i")
			cmdLine.append('%s'%pattern)
			cmdLine.append('-target')
			cmdLine.append('%s'%target)
			cmdLine.append('%s'%filename)
		Logging.info("Command line for ffmpeg="+str(cmdLine), kw = "animator")
		return cmdLine

class VideoGeneration(wx.Panel):
	"""
	A panel for controlling video generation
	"""
	def __init__(self, parent, control = None, visualizer = None, filename = ""):
		"""
		Initialization
		"""
		wx.Panel.__init__(self, parent, -1)
		self.encoder = VideoEncoder()
		self.control = control
		if filename:
			self.encoder.readIn(filename)
			self.renderingDone = 1
		else:
			self.renderingDone = 0
		
		scripting.videoGeneration = self
			
		self.visualizer = visualizer
		if visualizer:
			# The slider panel will be unlocked by UrmasWindow, not 
			# VideoGeneration
			self.visualizer.getCurrentMode().lockSliderPanel(1)
		
		self.oldSelection = 0
		self.rendering = 0
		self.abort = 0
		self.parent = parent

		if self.control:
			size = self.control.getFrameSize()
			self.encoder.setSize(*size)
			self.frames = self.control.getFrames()
			self.fps = self.control.getFrames() / float(self.control.getDuration())
			self.encoder.setFPS(self.fps)
			self.durationInSecs = self.control.getDuration()
		else:
			self.frames = self.encoder.getFrameAmount()
			self.fps = self.encoder.getFPS()
			self.durationInSecs = self.frames / self.fps
			
		self.frameDeletionDisabled = False

		self.outputExts = [["png", "bmp", "jpg", "tif", "pnm"], ["mpg", "mpg", "avi", "wmv", "avi", "avi", "mov"]]
		self.outputFormats = [["PNG", "BMP", "JPEG", "TIFF", "PNM"],
							 ["MPEG1", "MPEG2", "WMV1",
							  "WMV2", "MS MPEG4", "MS MPEG4 v2",
							  "QuickTime MPEG4", "AVI MPEG4"]]

		self.mainsizer = wx.GridBagSizer()
		self.generateGUI()

			
		# Produce quicktime MPEG4 by default but MS MPEG4 v2 on windows
		sel = 6
		if platform.system() == "Windows":
			sel = 5
		self.outputFormat.SetSelection(sel)
		self.encoder.setCodec(self.outputFormat.GetStringSelection())
		self.defformat = (sel, self.outputFormat.GetSelection())
		self.buttonBox = wx.BoxSizer(wx.HORIZONTAL)
		self.okButton = wx.Button(self, -1, "Create animation")
		self.cancelButton = wx.Button(self, -1, "Cancel")

		self.okButton.Bind(wx.EVT_BUTTON, self.onOkButton)
		self.cancelButton.Bind(wx.EVT_BUTTON, self.onCancelButton)
		

		#if not filename:
			#self.loadButton = wx.Button(self,-1,"Load project")
			#self.loadButton.Bind(wx.EVT_BUTTON, self.onLoadProject)	
			#self.buttonBox.Add(self.loadButton)
		
		self.buttonBox.Add(self.okButton)
		self.buttonBox.Add(self.cancelButton)

		self.mainsizer.Add(self.buttonBox, (5, 0), flag = wx.EXPAND | wx.RIGHT | wx.LEFT)

		self.SetSizer(self.mainsizer)
		self.SetAutoLayout(True)
		self.mainsizer.Fit(self)
		
		if filename:
			wx.CallAfter(self.updateGUIFromEncoder)
		
	def onLoadProject(self, event):
		"""
		load a project file for re-rendering
		"""
		filenames = GUI.Dialogs.askOpenFileName(self, "Open rendering project", "Rendering project (*.bxr)|*.bxr")
		if filenames:
			filename = unicode(filenames[0])
			do_cmd = "scripting.videoGeneration.readProjectFile(ur'%s')" % filename
			cmd = lib.Command.Command(lib.Command.GUI_CMD, None, None, do_cmd, "", \
									desc = "Save a rendering project file")
			cmd.run()
				
	def onCancelButton(self, event):
		"""
		Close the video generation window
		"""
		if self.rendering:
			lib.messenger.send(None, "stop_rendering")
			self.abort = 1
		lib.messenger.send(None, "video_generation_close")
		
		
	def onOkButton(self, event):
		"""
		Render the whole damn thing
		"""
		self.okButton.Enable(0)
		self.encoder.setPath(self.rendir.GetValue())
		videofile = self.videofile.GetValue()
		
		self.encoder.setVideoFileName(self.videofile.GetValue())

		quality = self.qualitySlider.GetValue()
		self.encoder.setQuality(quality)
		path = self.encoder.getPath()
		file = self.encoder.getVideoFileName()

		if os.path.exists(file):
			dlg = wx.MessageDialog(self, "File '%s' already exists. Overwrite?"%os.path.basename(file), "File already exists")
			if dlg.ShowModal() not in [wx.ID_YES, wx.ID_OK]:
				self.okButton.Enable(1)
				return

		if not os.path.isdir(path):
			dlg = wx.MessageDialog(self, "Directory '%s' doesn't exist. Create it?"%path, "Directory does not exist.")
			if dlg.ShowModal() in [wx.ID_CANCEL, wx.ID_NO]:
				self.okButton.Enable(1)
				return
			dn = path
			while not os.path.exists(dn):
				os.mkdir(dn)
				dn = os.path.dirname(dn)
		# If the rendering has been done already, then only do the encoding
		if self.renderingDone:
			lib.messenger.connect(None, "rendering_done", self.cleanUp)
			self.cleanUp()
			return
		
		# Do the rendering
		lib.messenger.send(None, "set_play_mode")
		lib.messenger.connect(None, "playback_stop", self.onCancelButton)
		self.abort = 0
		if self.visualizer.getCurrentModeName() != "3d":
			self.visualizer.setVisualizationMode("3d")
	

		conf = Configuration.getConfiguration()
		conf.setConfigItem("FramePath", "Paths", path)
		conf.setConfigItem("VideoPath", "Paths", file)
		conf.writeSettings()
	
		renderingInterface = lib.RenderingInterface.getRenderingInterface()
		renderingInterface.setVisualizer(self.visualizer)
		# if we produce images, then set the correct file type
		if self.formatMenu.GetSelection() == 0:
			formatNum = self.outputFormat.GetSelection()
			imageExt = self.outputExts[0][formatNum]
			Logging.info("Setting output image format to ", imageExt, kw = "animator")
			renderingInterface.setType(imageExt)

		Logging.info("Setting duration to", self.durationInSecs, "and frames to", self.frames, kw = "animator")
		self.control.configureTimeline(self.durationInSecs, self.frames)

		Logging.info("Will produce %s, rendered frames go to %s" % (file, path), kw = "animator")

		width, height = self.encoder.getSize()
		
		Logging.info("Will set render window to ", (width,height), kw = "animator")
		self.visualizer.setRenderWindowSize((width, height), self.parent)
		self.rendering = 1
		lib.messenger.connect(None, "rendering_done", self.cleanUp)
		flag = self.control.renderProject(0, renderpath = path)
		
		self.rendering = 0
		if flag == -1:
			return
			
	def cleanUp(self, *args):
		"""
		Method to clean up after rendering is done
		""" 
		if not self.renderingDone:
			renderingInterface = lib.RenderingInterface.getRenderingInterface()
			frameList = renderingInterface.getFrameList()
			self.encoder.setFrameList(frameList)
			# if the rendering wasn't aborted, then restore the animator
			if not self.abort:
				self.visualizer.restoreWindowSizes()
				self.parent.SetDefaultSize(self.parent.origSize)
				self.parent.parent.OnSize(None)
					
		if self.formatMenu.GetSelection() == 1:
			Logging.info("Will produce video", kw = "animator")
			self.encodeVideo()
			
		# clear the flags so that urmaswindow will destroy as cleanly
		
		self.abort = 0
		self.rendering = 0
		self.renderingDone = 1

		lib.messenger.send(None, "video_generation_close")
		lib.messenger.disconnect(None, "rendering_done")

	def encodeVideo(self):
		"""
		Encode video from the frames produced
		""" 
		success = 0
		if self.encoder.encode() == True:
			vidFile = self.encoder.getVideoFileName()
			if os.path.exists(vidFile):
				GUI.Dialogs.showmessage(self, "Encoding was successful!", "Encoding done")
				success = 1
			else:
				GUI.Dialogs.showmessage(self, "Encoding failed: File %s does not exist!" % vidFile, "Encoding failed")
				
		deleteFrames = (self.saveProjectBox.GetSelection() == 0) and not self.frameDeletionDisabled

		if success and deleteFrames:
			self.encoder.deleteFrames()
		"""
		elif not deleteFrames and not self.frameDeletionDisabled:
			filename = GUI.Dialogs.askSaveAsFileName(self, "Save rendering project as", "rendering.bxr", \
												"BioImageXD Rendering Project (*.bxr)|*.bxr")
			
			if platform.system() == "Windows":
				filename = filename.encode('mbcs')
			else:
				filename = filename.encode(sys.getfilesystemencoding())

			if filename:
				do_cmd = "scripting.videoGeneration.saveProjectFile(r'%s')"%filename
				cmd = lib.Command.Command(lib.Command.GUI_CMD, None, None, do_cmd, "", \
										desc = "Save a rendering project file")
				cmd.run()
		"""
			
	def readProjectFile(self, filename):
		"""
		read the relevant settings from a project file
		"""
		self.encoder.readIn(filename)
		self.encodingDone = 1
		self.updateGUIFromEncoder()
		
	def saveProjectFile(self, filename):
		"""
		save a project file to enable later rendering of the project
		"""
		self.encoder.writeOut(filename)
		
	def onUpdateFormat(self, event):
		"""
		Update the gui based on the selected output format
		""" 
		sel = self.formatMenu.GetSelection()
		
		if sel:
			self.outputFormatLbl.SetLabel("Video Codec:")
		else:
			self.outputFormatLbl.SetLabel("Image Format:")
		self.saveProjectBox.Enable(sel)
		self.qualitySlider.Enable(sel)
		self.videofile.Enable(sel)

		self.videofileBtn.Enable(sel)
		
		currentSelection = self.outputFormat.GetSelection()
		self.outputFormat.Clear()
		for i in self.outputFormats[sel]:
			self.outputFormat.Append(i)
		self.outputFormat.SetSelection(self.oldSelection)
		self.oldSelection = currentSelection

			
	def onUpdateCodec(self, event):
		"""
		Update the gui based on the selected output codec
		""" 
		sel = self.formatMenu.GetSelection()
		if sel == 1:
			codec = self.outputFormat.GetStringSelection()
			self.encoder.setCodec(codec)

			newext = self.encoder.getExtensionForCodec(codec)
			filename = self.videofile.GetValue()
			name, ext = os.path.splitext(filename)
			filename = "%s.%s"%(name, newext)
			self.videofile.SetValue(filename)
			self.encoder.setVideoFileName(filename)
			
	def onUpdatePreset(self, event = None):
		"""
		Update the GUI based on the selected preset
		"""
		sel = self.preset.GetSelection()
		flag = (sel == 0)
		self.formatMenu.Enable(flag)
		self.outputFormat.Enable(flag)
		self.encoder.setPreset(sel)
		if not flag:
			self.formatMenu.SetStringSelection("Video")
			self.outputFormat.SetStringSelection("MPEG2")
			self.frameSize.SetLabel("%d x %d"%self.encoder.presets[sel][0])
			fps = self.encoder.presets[sel][1]
			self.frameRate.SetLabel("%.2f"%fps)
			self.frames = int(fps * self.durationInSecs)
			self.totalFrames.SetLabel("%d"%self.frames)
		else:
			if self.defformat:
				defformat1, defformat2 = self.defformat
				self.formatMenu.SetSelection(defformat1)
				self.outputFormat.SetSelection(defformat2)
			self.frameSize.SetLabel("%d x %d"%self.encoder.getSize())
			self.frameRate.SetLabel("%.2f"%self.encoder.getFPS())
			self.frames = int(self.encoder.getFPS() * self.durationInSecs)
			self.totalFrames.SetLabel("%d"%self.frames)

	def createDuration(self, durationInSecs):
		"""
		Create duration presentation from secs
		"""
		t = durationInSecs
		h = t / 3600
		m = t / 60
		s = t % 60
		t = "%.2d:%.2d:%.2d" % (h, m, s)
		return t
			
	def generateGUI(self):
		"""
		Generate the GUI
		""" 
		self.outputsizer = wx.GridBagSizer(0, 5)
		box = wx.StaticBox(self, wx.HORIZONTAL, "Rendering")
		self.outputstaticbox = wx.StaticBoxSizer(box, wx.HORIZONTAL)
		self.outputstaticbox.Add(self.outputsizer)

		self.formatLabel = wx.StaticText(self, -1, "Output format:")
		self.formatLabel.SetForegroundColour(scripting.COLOR_EXPERIENCED)
		self.formatMenu = wx.Choice(self, -1, choices = ["Images", "Video"])
		self.formatMenu.SetSelection(1)
		self.formatMenu.Bind(wx.EVT_CHOICE, self.onUpdateFormat)
		self.formatMenu.SetForegroundColour(scripting.COLOR_EXPERIENCED)
		
		self.totalFramesLabel = wx.StaticText(self, -1, "Frames:")
		self.durationLabel = wx.StaticText(self, -1, "Duration:")

		self.totalFrames = wx.StaticText(self, -1, "%d" % self.frames, size = (50, -1))
		
		t = self.createDuration(self.durationInSecs)
		self.duration = wx.StaticText(self, -1, t, size = (100, -1))

		self.outputFormatLbl = wx.StaticText(self, -1, "Video codec:")
		self.outputFormatLbl.SetForegroundColour(scripting.COLOR_EXPERIENCED)
		self.outputFormat = wx.Choice(self, -1, choices = self.outputFormats[1])
		self.outputFormat.Bind(wx.EVT_CHOICE, self.onUpdateCodec)
		self.outputFormat.SetSelection(2)
		self.outputFormat.SetForegroundColour(scripting.COLOR_EXPERIENCED)
		
		self.frameSizeLbl = wx.StaticText(self, -1, "Frame size:")
		self.frameSize = wx.StaticText(self, -1, "%d x %d" % self.encoder.getSize())

		self.frameRateLbl = wx.StaticText(self, -1, "Frame rate:")
		self.frameRate = wx.StaticText(self, -1, "%.2f" % self.encoder.getFPS())
		
		self.qualityLbl = wx.StaticText(self, -1, "Encoding quality (1 = worst, 10 = best)")
		self.qualityLbl.SetForegroundColour(scripting.COLOR_EXPERIENCED)
		self.qualitySlider = wx.Slider(self, -1, value = 10, minValue = 1, maxValue = 10, \
										style = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_AUTOTICKS, size = (250, -1))
		self.qualitySlider.SetForegroundColour(scripting.COLOR_EXPERIENCED)
		
		self.presetLbl = wx.StaticText(self, -1, "Presets:")
		self.preset = wx.Choice(self, -1, choices = ["Use settings below", "PAL-DVD", "NTSC-DVD"])
		self.preset.Bind(wx.EVT_CHOICE, self.onUpdatePreset)
		self.preset.SetSelection(0)
		n = 0
		self.outputsizer.Add(self.presetLbl, (n, 0))
		n += 1
		self.outputsizer.Add(self.preset, (n, 0))
		
		n += 1
		self.outputsizer.Add(self.formatLabel, (n, 0))
		self.outputsizer.Add(self.formatMenu, (n, 1))
		n += 1
		self.outputsizer.Add(self.outputFormatLbl, (n, 0))
		self.outputsizer.Add(self.outputFormat, (n, 1))
		n += 1
		self.outputsizer.Add(self.frameSizeLbl, (n, 0))
		self.outputsizer.Add(self.frameSize, (n, 1))
		n += 1
		self.outputsizer.Add(self.frameRateLbl, (n, 0))
		self.outputsizer.Add(self.frameRate, (n, 1))
		n += 1
		self.outputsizer.Add(self.durationLabel, (n, 0))
		self.outputsizer.Add(self.duration, (n, 1))		   
		n += 1
		self.outputsizer.Add(self.totalFramesLabel, (n, 0))
		self.outputsizer.Add(self.totalFrames, (n, 1))
		n += 1
		self.outputsizer.Add(self.qualityLbl, (n, 0), span = (1, 2))
		n += 1
		self.outputsizer.Add(self.qualitySlider, (n, 0), span = (1, 2))
		
		self.mainsizer.Add(self.outputstaticbox, (0, 0))
	
		conf = Configuration.getConfiguration()
		path = conf.getConfigItem("FramePath", "Paths")
		video = conf.getConfigItem("VideoPath", "Paths")
		if not path:
			path = os.path.expanduser("~")
		if not video:
			video = os.path.join(path, "video.avi")
		self.rendir = wx.TextCtrl(self, -1, path, size = (150, -1))
		
	
		self.encoder.setPath(path)
		self.encoder.setVideoFileName(video)
		
		self.rendirLbl = wx.StaticText(self,
		-1, "Save frames in directory:")
		
		self.saveProjectBox = wx.RadioBox(self,-1,"Save rendered frames", choices=["Delete frames after encoding video","Save frames for later use"], majorDimension=2, style=wx.RA_SPECIFY_ROWS)
		
		self.dirBtn = wx.Button(self, -1, "...")
		self.dirBtn.Bind(wx.EVT_BUTTON, self.onSelectDirectory)
		
		self.renderingsizer = wx.GridBagSizer(5, 5)

		
		self.renderingsizer.Add(self.rendirLbl, (0, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		self.renderingsizer.Add(self.rendir, (1, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		self.renderingsizer.Add(self.dirBtn, (1, 1))
		self.renderingsizer.Add(self.saveProjectBox, (2, 0))
		
		self.videofile = wx.TextCtrl(self, -1, video, size = (150, -1))
		self.videofileLbl = wx.StaticText(self, -1, "Video file name:")
		self.videofileBtn = wx.Button(self, -1, "...")
		self.videofileBtn.Bind(wx.EVT_BUTTON, self.onSelectOutputFile)
		
		self.renderingsizer.Add(self.videofileLbl, (3, 0), flag = wx.EXPAND | wx.ALL)
		self.renderingsizer.Add(self.videofile, (4, 0), flag = wx.EXPAND | wx.ALL)
		self.renderingsizer.Add(self.videofileBtn, (4, 1), flag = wx.EXPAND | wx.ALL)
		self.mainsizer.Add(self.renderingsizer, (1, 0), flag = wx.EXPAND | wx.ALL)

		self.guidance = wx.StaticText(self, -1, "When you click \"Create animation\", every frame is rendered using the 3D mode, and after that the (optional) video file is created. This process may take a long time, and you should not touch the computer during this time. A message will appear when the process is complete. Note that you can save and open animation projects from the \"Animation\" menu.")
		self.guidance.Wrap(350)
		self.guideSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.guideSizer.Add(self.guidance)
		self.mainsizer.Add(self.guideSizer, (3,0), flag = wx.EXPAND | wx.ALL)
		
	def disableFrameDeletion(self):
		"""
		disable the option to delete the frames / save a projet
		"""
		self.saveProjectBox.Enable(False)
		self.frameDeletionDisabled = True
		
	def updateGUIFromEncoder(self):
		"""
		update the GUI entries based on values from the encoder
		"""
		self.rendir.SetValue(self.encoder.getPath())
		self.videofile.SetValue(self.encoder.getVideoFileName())
		self.fps = self.encoder.getFPS()
		w,h = self.encoder.getSize()
		self.frameSize.SetLabel("%d x %d"%(w,h))
		self.frameRate.SetLabel("%.2f" % self.fps)
		preset = self.encoder.getPreset()
		self.preset.SetSelection(preset)
		if preset:
			print "Updating preset to ",preset
			self.onUpdatePreset()
		
	def onSelectDirectory(self, event = None):
		"""
		A callback that is used to select the directory where
					 the rendered frames are stored
		"""
		dirname = GUI.Dialogs.askDirectory(self, "Directory for rendered frames", ".")
		if dirname:
			self.rendir.SetValue(dirname)
			self.encoder.setPath(dirname)
			
	def onSelectOutputFile(self, event = None):
		"""
		A callback that is used to select the video file 
					 that is produced.
		"""
		sel = self.formatMenu.GetSelection()
		codec = self.outputFormat.GetSelection()
		codecname = self.outputFormats[sel][codec]
		ext = self.outputExts[sel][codec]
		wc = "%s File (*.%s)|*.%s" % (codecname, ext, ext)
		filename = GUI.Dialogs.askSaveAsFileName(self, "Select output filename", "movie.%s" % ext, wc)
		if filename:
			self.videofile.SetValue(filename)
			self.encoder.setVideoFileName(filename)
			
