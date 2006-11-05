#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: SettingsWindow
 Project: BioImageXD
 Created: 09.02.2005, KP
 Description:

 A wxPython wxDialog window that is used to control the settings for the
 whole application.

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

import os.path

import wx
import  wx.lib.filebrowsebutton as filebrowse
import  wx.lib.intctrl
import Configuration
import scripting

class GeneralSettings(wx.Panel):
    """
    Created: 09.02.2005, KP
    Description: A window for controlling the general settings of the application
    """ 
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,-1)
        self.sizer = wx.GridBagSizer(5,5)
        conf = Configuration.getConfiguration()
        format = conf.getConfigItem("ImageFormat","Output")
        showTips=conf.getConfigItem("ShowTip","General")
        askOnQuit=conf.getConfigItem("AskOnQuit","General")
        
        #print "showTip=",showTip
        if showTips and type(showTips)==type(""):
            showTips = eval(showTips)
        if askOnQuit and type(askOnQuit)==type(""):
            askOnQuit = eval(askOnQuit)
            
        self.imageBox=wx.StaticBox(self,-1,"Image Format",size=(600,150))
        self.imageBoxSizer=wx.StaticBoxSizer(self.imageBox,wx.VERTICAL)
#        self.imageBoxSizer.SetMinSize(self.imageBox.GetSize())
        
        self.lbl=wx.StaticText(self,-1,"Default format for Images:")
        self.choice=wx.Choice(self,-1,choices=["PNG","PNM","BMP","JPEG","TIFF"])
        
        self.choice.SetStringSelection(format.upper())

        self.imageBoxSizer.Add(self.lbl)
        self.imageBoxSizer.Add(self.choice)
        
        self.sizer.Add(self.imageBoxSizer,(2,0))

        self.tipBox=wx.StaticBox(self,-1,"Startup tips")
        self.tipBoxSizer=wx.StaticBoxSizer(self.tipBox,wx.VERTICAL)
        self.tipCheckbox=wx.CheckBox(self,-1,"Show tips at startup")
        self.tipCheckbox.SetValue(showTips)
        self.tipBoxSizer.Add(self.tipCheckbox)
        
        self.sizer.Add(self.tipBoxSizer,(0,0))

        self.quitBox=wx.StaticBox(self,-1,"Closing the application")
        self.quitBoxSizer=wx.StaticBoxSizer(self.quitBox,wx.VERTICAL)
        self.askOnQuitCheckbox=wx.CheckBox(self,-1,"Verify before quitting BioImageXD")
        self.askOnQuitCheckbox.SetValue(askOnQuit)
        self.quitBoxSizer.Add(self.askOnQuitCheckbox)
        
        self.sizer.Add(self.quitBoxSizer,(1,0)) 
#        self.imageBox=wx.StaticBox(self,-1,"Image Format",size=(600,150))
#        self.imageBoxSizer=wx.StaticBoxSizer(self.imageBox,wx.VERTICAL)
#        self.imageBoxSizer.SetMinSize(self.imageBox.GetSize())
        
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        
    def writeSettings(self,conf):
        """
        Created: 05.04.2005, KP
        Description: A method that writes out the settings that have been modified
                     in this window.
        """     
        format=self.choice.GetStringSelection()
        #print "Setting format to ",format.lower()
        conf.setConfigItem("ImageFormat","Output",format.lower())
        showTip=self.tipCheckbox.GetValue()
        conf.setConfigItem("ShowTip","General",str(showTip))

        askOnQuit=self.askOnQuitCheckbox.GetValue()
        conf.setConfigItem("AskOnQuit","General",str(askOnQuit))
        
class PathSettings(wx.Panel):
    """
    Created: 09.02.2005, KP
    Description: A window for controlling the path settings of the application
    """ 
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,-1,size=(640,480))
        self.sizer=wx.GridBagSizer(5,5)
        #self.SetBackgroundColour(wx.Colour(255,0,0))
        
        conf=Configuration.getConfiguration()
        vtkpath = conf.getConfigItem("VTKPath","VTK")
        
        datapath=conf.getConfigItem("DataPath","Paths")
        
        removevtk = conf.getConfigItem("RemoveOldVTK","VTK")
        remember =conf.getConfigItem("RememberPath","Paths")

        self.dataBox=wx.StaticBox(self,-1,"Data Files Directory",size=(600,150))
        self.dataBoxSizer=wx.StaticBoxSizer(self.dataBox,wx.VERTICAL)
        self.dataBoxSizer.SetMinSize(self.dataBox.GetSize())
        self.databrowse=filebrowse.DirBrowseButton(self,-1,labelText="Location of Data Files",
        toolTip="Set the default directory for data files",
        startDirectory=datapath)
        self.databrowse.SetValue(datapath)

        self.dataBoxSizer.Add(self.databrowse,0,wx.EXPAND)
        self.useLastCheckbox = wx.CheckBox(self,-1,"Use last opened directory as default directory")
        if type(remember)==type(""):
            remember=eval(remember)
        self.useLastCheckbox.SetValue(remember)
        self.dataBoxSizer.Add(self.useLastCheckbox)        
        
        
        #self.sizer.Add(self.vtkBoxSizer, (0,0),flag=wx.EXPAND|wx.ALL)
        self.sizer.Add(self.dataBoxSizer,(0,0),flag=wx.EXPAND|wx.ALL)        
        self.SetAutoLayout(1)
        self.SetSizer(self.sizer)
        self.Layout()
        self.sizer.Fit(self)
        
    def writeSettings(self,conf):
        """
        Created: 12.03.2005, KP
        Description: A method that writes out the settings that have been modified
                     in this window.
        """     
        #vtkpath=self.vtkbrowse.GetValue()
        
        datapath=self.databrowse.GetValue()
        rememberlast=self.useLastCheckbox.GetValue()
        
        #removevtk=self.removeVTKCheckbox.GetValue()
        #conf.setConfigItem("VTKPath","VTK",vtkpath)
        conf.setConfigItem("DataPath","Paths",datapath)
        
        #conf.setConfigItem("RemoveOldVTK","VTK",removevtk)
        conf.setConfigItem("RememberPath","Paths",rememberlast)        


class PerformanceSettings(wx.Panel):
    """
    Created: 27.04.2006, KP
    Description: A window for controlling the performance settings of the application
    """ 
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,-1,size=(640,480))
        self.sizer=wx.GridBagSizer(5,5)
        #self.SetBackgroundColour(wx.Colour(255,0,0))
        
        conf=Configuration.getConfiguration()

        self.resampleBox=wx.StaticBox(self,-1,"Image resampling",size=(600,150))
        self.resampleBoxSizer=wx.StaticBoxSizer(self.resampleBox,wx.VERTICAL)
        self.resampleBoxSizer.SetMinSize(self.resampleBox.GetSize())

        self.resampleCheckbox = wx.CheckBox(self,-1,"Resample large images automatically")
        resampleLbl = wx.StaticText(self,-1,"Resample images larger than:")
        resample2Lbl = wx.StaticText(self,-1,"Resample to image size:")
        
        
        val = conf.getConfigItem("DoResample","Performance")
        if val:
            val = eval(val)
        else:
            val=False
        #val = not (not doresample)
        #print "Setting to value=",val
        self.resampleCheckbox.SetValue(val)
        try:
            rx,ry=eval(conf.getConfigItem("ResampleDims","Performance"))
            tx,ty = eval(conf.getConfigItem("ResampleTo","Performance"))
        except:
            rx,ry,tx,ty=1024,1024,1024,1024
            
        
        self.resampleX = wx.TextCtrl(self,-1,str(rx))
        self.resampleY = wx.TextCtrl(self,-1,str(ry))
        self.resampleToX = wx.TextCtrl(self,-1,str(tx))
        self.resampleToY = wx.TextCtrl(self,-1,str(ty))
        
        x1=wx.StaticText(self,-1,"x")
        x2=wx.StaticText(self,-1,"x")
        resampleGrid = wx.GridBagSizer()
        self.resampleBoxSizer.Add(self.resampleCheckbox)
        resampleGrid.Add(resampleLbl,(0,0))
        resampleGrid.Add(resample2Lbl,(1,0))
        resampleGrid.Add(self.resampleX,(0,1))
        resampleGrid.Add(x1,(0,2))
        resampleGrid.Add(self.resampleY,(0,3))
        resampleGrid.Add(self.resampleToX,(1,1))
        resampleGrid.Add(x2,(1,2))
        resampleGrid.Add(self.resampleToY,(1,3))        
        self.resampleBoxSizer.Add(resampleGrid)
        
        
        self.memoryBox=wx.StaticBox(self,-1,"Memory usage",size=(600,150))
        self.memoryBoxSizer=wx.StaticBoxSizer(self.memoryBox,wx.VERTICAL)
        self.memoryBoxSizer.SetMinSize(self.memoryBox.GetSize())
        
        self.limitMemoryCheckbox = wx.CheckBox(self,-1,"Limit memory used by a single operation")
        
        val = not not conf.getConfigItem("LimitMemory","Performance")
        self.limitMemoryCheckbox.SetValue(val)
        
        try:
            limitval = eval(conf.getConfigItem("LimitTo","Performance"))
        except:
            limitval = 512
        
        limitLbl = wx.StaticText(self,-1,"Memory limit (MB):")
        mblbl = wx.StaticText(self,-1,"MB")
        self.memoryLimit = wx.lib.intctrl.IntCtrl(self,value=limitval,min=1,max=4096,limited=True)
        
        memgrid=wx.GridBagSizer()
        self.memoryBoxSizer.Add(self.limitMemoryCheckbox)
        memgrid.Add(limitLbl,(0,0))
        memgrid.Add(self.memoryLimit,(0,1))
        memgrid.Add(mblbl,(0,2))
        self.memoryBoxSizer.Add(memgrid)

        
        self.rescaleBox = wx.StaticBox(self,-1,"Intensity rescaling",size=(600,100))
        self.rescaleBoxSizer = wx.StaticBoxSizer(self.rescaleBox, wx.VERTICAL)
        self.rescaleBoxSizer.SetMinSize(self.rescaleBox.GetSize())
        
        self.rescaleCheckbox = wx.CheckBox(self,-1,"Rescale 12- and 16-bit datasets to 8-bit when loading")
        self.rescaleBoxSizer.Add(self.rescaleCheckbox)
        val = conf.getConfigItem("RescaleOnLoading","Performance")
        if val:
            val = eval(val)
        else:
            val=0
        self.rescaleCheckbox.SetValue(val)
    
        self.sizer.Add(self.rescaleBoxSizer,(0,0),flag=wx.EXPAND|wx.ALL)        
        self.sizer.Add(self.memoryBoxSizer,(1,0),flag=wx.EXPAND|wx.ALL)        
        self.sizer.Add(self.resampleBoxSizer,(2,0),flag=wx.EXPAND|wx.ALL)        
        
        self.SetAutoLayout(1)
        self.SetSizer(self.sizer)
        self.Layout()
        self.sizer.Fit(self)
        
    def writeSettings(self,conf):
        """
        Created: 12.03.2005, KP
        Description: A method that writes out the settings that have been modified
                     in this window.
        """     
        forceResample = self.resampleCheckbox.GetValue()
        try:
            rx = int(self.resampleX.GetValue())
            ry = int(self.resampleY.GetValue())
            rtx = int(self.resampleToX.GetValue())
            rty = int(self.resampleToY.GetValue())
        except:
            forceResample=0
        conf.setConfigItem("DoResample","Performance",str(not not forceResample))
        if forceResample:
            conf.setConfigItem("ResampleDims","Performance",str((rx,ry)))
            conf.setConfigItem("ResampleTo","Performance",str((rtx,rty)))
        
        rescaleOnLoad=self.rescaleCheckbox.GetValue()
        print "Setting rescale on load to ",rescaleOnLoad
        conf.setConfigItem("RescaleOnLoading","Performance",str(rescaleOnLoad))        
        limitMem = self.limitMemoryCheckbox.GetValue()
        limitTo = self.memoryLimit.GetValue()
        
        conf.setConfigItem("LimitMemory","Performance",str(not not limitMem))
        conf.setConfigItem("LimitTo","Performance",str(limitTo))

class MovieSettings(wx.Panel):
    """
    Created: 09.02.2005, KP
    Description: A window for controlling the movie generation settings of the application
    """ 
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,-1)
    


class SettingsWindow(wx.Dialog):
    """
    Created: 09.02.2005, KP
    Description: A window for controlling the settings of the application
    """ 
    def __init__(self,parent):
        wx.Dialog.__init__(self,parent,-1,"Settings for BioImageXD",style=wx.CAPTION|wx.STAY_ON_TOP|wx.CLOSE_BOX|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.RESIZE_BORDER|wx.DIALOG_EX_CONTEXTHELP,
        size=(640,480))
        self.listbook=wx.Listbook(self,-1,style=wx.LB_LEFT)
        self.listbook.SetSize((640,480))
        self.sizer=wx.BoxSizer(wx.VERTICAL)
        try:
            self.imagelist=wx.ImageList(32,32)
            self.listbook.AssignImageList(self.imagelist)
            imgpath = scripting.get_icon_dir()
            for i in ["general.gif","paths.gif","performance.gif"]:
                icon=os.path.join(imgpath,i)
                bmp=wx.Bitmap(icon,wx.BITMAP_TYPE_GIF)
                self.imagelist.Add(bmp)
        except:
            pass
        self.generalPanel=GeneralSettings(self.listbook)
        self.pathsPanel=PathSettings(self.listbook)
        self.performancePanel = PerformanceSettings(self.listbook)
        #self.moviePanel=MovieSettings(self.listbook)
        
        self.listbook.AddPage(self.generalPanel,"General",imageId=0)
        self.listbook.AddPage(self.pathsPanel,"Paths",imageId=1)
        self.listbook.AddPage(self.performancePanel,"Performance",imageId=2)

        self.sizer.Add(self.listbook,flag=wx.EXPAND|wx.ALL)
        
        self.staticLine=wx.StaticLine(self,-1)
        self.sizer.Add(self.staticLine,flag=wx.EXPAND)
        self.buttonSizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        self.sizer.Add(self.buttonSizer,1,flag=wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT)
        
        wx.EVT_BUTTON(self,wx.ID_OK,self.writeSettings)
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    def writeSettings(self,evt):
        conf=Configuration.getConfiguration()
        self.pathsPanel.writeSettings(conf)
        self.generalPanel.writeSettings(conf)
        self.performancePanel.writeSettings(conf)
        conf.writeSettings()
        self.Close()
        
