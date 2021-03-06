# -*- coding: iso-8859-1 -*-

"""
 Unit: DataUnitSetting
 Project: BioImageXD
 Description:

 This is a class that holds all settings of a dataunit. A dataunit's 
 setting object is the only thing differentiating it from another
 dataunit.
 
 This code was re-written for clarity. The code produced by the
 Selli-project was used as a starting point for producing this code.
 http://sovellusprojektit.it.jyu.fi/selli/

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
__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

#import zlib

import vtk
import vtkbxd
import lib.ImageOperations
import pickle
import Logging
import Modules.DynamicLoader
import ConfigParser

class DataUnitSettings:
	"""
	Description: This is a class that holds all settings of a dataunit
	"""	   
	# Global settings, shared by all instances
	# The different source units differentiate by having a number
	# and using the counted keys
	settings = {}
	
	def __init__(self, dataSetNumber = -1, **keyWords):
		"""
		Constructor
		@param n	Number of the dataset this is associated to
				Reflects in that set() and get() of counted variables
				will set only the nth variable
		"""
		self.counted = {}
		self.registered = {}
		self.parser = None
		self.private = {}
		self.isPrivate = {}
		self.type = None
		self.modules = Modules.DynamicLoader.getTaskModules()
		self.dataunit = None
		self.channels = 0
		self.timepoints = 0
		if keyWords.has_key("type"):
			self.setType(keyWords["type"])
		self.dataSetNumber = dataSetNumber
		self.serialized = {}
		self.register("SettingsOnly", serialize = 1)
		self.registerPrivate("ColorTransferFunction", serialize = 1)
		self.register("PreviewedDataset")
		self.set("PreviewedDataset", -1)
		self.register("Annotations", serialize = 1)
#		 self.register("SourceCount")
		self.registerCounted("Source")
		self.register("VoxelSize")
		self.register("Spacing")
		self.registerPrivate("EmissionWavelength")
		self.registerPrivate("ExcitationWavelength")
		self.register("NumericalAperture")
		#self.register("Origin")
		self.register("Dimensions")
		self.register("ShowOriginal", serialize = 1)
		self.register("Type")
		self.registerPrivate("Name")
		self.register("BitDepth")
		self.register("TimeStamps", serialize = 1)
		self.register("AbsoluteTimeStamps", serialize = 1)
		
	def getDatasetNumber(self):
		"""
		return the index of this dataset
		"""
		return self.dataSetNumber
		
	def resetSettings(self):
		"""
		Reset the settings
		"""
		# Delete keys that have not been registered. This is to ensure
		# nothing added by tasks is retained after the task has been closed
		
		for i in self.private.keys():
			if i not in self.registered:
				del self.private[i]
		for i in self.settings.keys():
			if i not in self.registered:
				del self.settings[i]
		
	def asType(self, newtype):
		"""
		Return this setting as given type
		"""
		newclass = eval(newtype)

		settings = newclass(self.dataSetNumber)
		settings.initialize(self.dataunit, self.channels, self.timepoints)
		return settings
		
	def setType(self, newtype):
		"""
		Set the type of this dataunit
		"""
		self.type = newtype
		self.set("Type", newtype)
		
	def getType(self):
		"""
		Set the type of this dataunit
		"""
		return self.type
		
	def register(self, name, serialize = 0):
		"""
		Register a name as valid key. 
		Parameters:
			serialize	The value will be written out/read through
						the serialize/deserialize methods
		"""	   
		self.registered[name] = 1
		self.serialized[name] = serialize
		self.isPrivate[name] = 0

	def registerPrivate(self, name, serialize = 0):
		"""
		Register a name as valid key.
		Parameters:
			serialize	The value will be written out/read through
						the serialize/deserialize methods
		"""
		self.registered[name] = 1
		self.isPrivate[name] = 1
		self.serialized[name] = serialize
		
	def registerCounted(self, name, serialize = 0):
		"""
		Register a name as valid key that is counted
		Parameters:
			serialize	The value will be written out/read through
						the serialize/deserialize methods
		"""
		self.registered[name] = 1
		self.counted[name] = 1
		self.serialized[name] = serialize
		self.isPrivate[name] = 0

	def readFrom(self, parser):
		"""
		Attempt to read all registered keys from a parser
		"""
		self.parser = parser
		if not self.get("Type"):
			self.parser = parser
			type = None
			try:
				type = parser.get("Type", "Type")
			except ConfigParser.NoOptionError:
				type = parser.get("Type", "type")
			except ConfigParser.NoSectionError:
				pass
			# if we can determine the settings type, then we instantiate a class corresponding
			# to that type and read the settings using that class
			# this is done so that all the settings will be read correctly
			# if the type cannot be determined, then just read the settings that we know how
			if type:
				if type in self.modules:
					settingsclass = self.modules[type][2].getSettingsClass()
				else:
					settingsclass = self.__class__
				Logging.info("Type = %s, settings class = %s" % (type, str(settingsclass)), kw = "processing")
				obj = settingsclass(self.dataSetNumber)
				obj.setType(type)
				return obj.readFrom(parser)

		for key in self.registered.keys():
			ser = self.serialized[key]
			if key in self.counted:
				try:
					n = parser.get("Count", key)
				except:
					try:
						n = parser.get("Count", key.lower())
					except:
						Logging.info("Got no key count for %s" % key, kw = "dataunit")
						continue
				n = int(n)
				Logging.info("Got %d keys for %s" % (n, key), kw = "dataunit")
				
				for i in range(n + 1):
					ckey = "%s[%d]" % (key, i)
					try:
						try:
							value = parser.get(key, ckey)
						except ConfigParser.NoOptionError:
							try:
								value = parser.get(key, ckey.lower())
							except ConfigParser.NoOptionError:
								continue
					
						if ser:
							value = self.deserialize(key, value)
							#Logging.info("Deserialized ", key, " = ", value, kw = "dataunit")
						self.setCounted(key, i, value)
						self.counted[key] = i
					except ConfigParser.NoSectionError:
						Logging.info("Got no keys for section %s" % key, kw = "dataunit")
			else:
				#value = parser.get("ColorTransferFunction", "ColorTransferFunction")
				try:
					try:
						value = parser.get(key, key)
					except ConfigParser.NoOptionError:
						value = parser.get(key, key.lower())
					
					if ser:
						#Logging.info("Trying to deserialize ", key, value, kw = "dataunit")
						value = self.deserialize(key, value)
						#Logging.info("Deserialized ", key, " = ", value, kw = "dataunit")
					self.set(key, value)
				except ConfigParser.NoSectionError:
					#Logging.info("Got no keys for section %s" %key, kw = "dataunit")
					pass
		return self
				
	def writeKey(self, key, parser, n = -1):
		"""
		Write a key and it's value to parser
		"""
		nkey = "%s[%d]" % (key, n)
		if not (key in self.settings or nkey in self.settings) \
			and not (key in self.private or nkey in self.private):
			#Logging.info("neither ", key, "nor", nkey, "in ", self.settings.keys(), kw = "dataunit")
			return
		okey = key
		if n != -1:
			key = nkey

		if self.isPrivate[okey] == 1 and (key in self.private or okey in self.private):
			if (key in self.private):
				value = self.private[key]
			else:	
				value = self.private[okey]
		else:
			if (key in self.settings):
				value = self.settings[key]
			else:
				value = self.settings[okey]
		
		if self.serialized[okey]:
			value = self.serialize(okey, value)
		if not parser.has_section(okey):
			parser.add_section(okey)
		parser.set(okey, key, value)
 
	def writeTo(self, parser):
		"""
		Attempt to write all keys to a parser
		"""
		if not parser.has_section("Settings"):
			parser.add_section("Settings")

		for key in self.registered.keys():
			if key in self.counted:
				for i in range(self.counted[key] + 1):
					self.writeKey(key, parser, i)
			else:
				self.writeKey(key, parser)
			   
		if len(self.counted.keys()):
			if not parser.has_section("Count"):
				parser.add_section("Count")
		for key in self.counted.keys():
			value = self.counted[key]
			parser.set("Count", key, value)
			
	def set(self, name, value, overwrite = 1):
		"""
		Sets the value of a key
		"""
		if not overwrite and self.settings.has_key(name):
			return
		if self.dataSetNumber != -1 and name in self.counted:
			return self.setCounted(name, self.dataSetNumber, value, overwrite)
		if name not in self.registered:
			raise "No key %s registered" % name
		if self.isPrivate[name]:
			if name == "FilterList":
				print "\n\n\n",repr(self),"Setting filterlist to",value
			self.private[name] = value
		else:
			self.settings[name] = value

	def setCounted(self, name, count, value, overwrite = 1):
		"""
		If there are more than one setting associated,
					 for example, with different channels, then this
					 can be used to set the value of that variable
					 properly.
		"""
		if not name in self.registered:
			raise "No key %s registered" % name
		keyval = "%s[%d]" % (name, count)
		if not overwrite and (keyval in self.settings):
			return
		self.settings[keyval] = value
		if self.counted[name] < count:
			self.counted[name] = count

	def get(self, name):
		"""
		Return the value of a key
		"""
		if self.dataSetNumber != -1 and name in self.counted:
			name = "%s[%d]" % (name, self.dataSetNumber)
		if name in self.private:
			return self.private[name]
		if name in self.settings:
			return self.settings[name]
		return None

	def getCounted(self, name, count):
		"""
		Return the value of a key
		"""
		key = "%s[%d]" % (name, count)
		return self.get(key)

	@staticmethod
	def serialize(name, value):
		"""
		Returns the value of a given key in a format
					 that can be written to disk.
		"""
#		Logging.info("Serializing name ", name, kw = "dataunit")
		if "ColorTransferFunction" in name:
			s = lib.ImageOperations.lutToString(value, luttype = "BioImageXD")
			s2 = ""
			for i in s:
				s2 += repr(i)
			return s2
		# Annotations is a list of classes that can easily be
		# pickled / unpickled
		if "Annotations" in name:
			Logging.info("Pickling %d annotations" % len(value), kw = "dataunit")
			s = pickle.dumps(value, protocol = pickle.HIGHEST_PROTOCOL)
			#s = zlib.compress(s)
			return s

		if name not in ["IntensityTransferFunction", "IntensityTransferFunctions", "AlphaTransferFunction"]:
			return str(value)

		val = lib.ImageOperations.getAsParameterList(value)
		return str(val)

	@staticmethod
	def deserialize(name, value):
		"""
		Returns the value of a given key
		"""
		if "ColorTransferFunction" in name:
			data = eval(value)
			colorTransferFunction = vtk.vtkColorTransferFunction()
			lib.ImageOperations.loadLUTFromString(data, colorTransferFunction)
			return colorTransferFunction
		
		# Annotations is a list of classes that can easily be
		# pickled / unpickled
		if "Annotations" in name:
			Logging.info("deserializing Annotations", kw = "dataunit")
			#val = zlib.decompress(value)
			val = pickle.loads(value)
			Logging.info("unpickled %d annotations" % len(val), kw = "dataunit")
			return val
		if name not in ["IntensityTransferFunction", "IntensityTransferFunctions", "AlphaTransferFunction"]:
			return eval(value)
		transferFunction = vtkbxd.vtkIntensityTransferFunction()
		lst = eval(value)
		lib.ImageOperations.setFromParameterList(transferFunction, lst)
		return transferFunction
		
	def __str__(self):
		"""
		Returns the string representation of this class
		"""
		return "%s %s ( %s )" % (repr(self), str(self.__class__), str(self.settings))

	def initialize(self, dataunit, channels, timepoints):
		"""
		Set initial values for settings based on 
					 number of channels and timepoints
		"""
		self.channels = channels
		self.timepoints = timepoints
		self.dataunit = dataunit

	def __getstate__(self):
		ret = {}
		ret["counted"] = self.counted
		ret["registered"] = self.registered
		ret["private"] = self.private
		ret["isPrivate"] = self.isPrivate
		ret["type"] = self.type
		ret["channels"] = self.channels
		ret["timepoints"] = self.timepoints
		ret["n"] = self.dataSetNumber
		ret["serialized"] = self.serialized
		return ret

	def __setstate__(self, state):
		self.counted = state["counted"]
		self.registered = state["registered"]
		self.private = state["private"] 
		self.isPrivate = state["isPrivate"] 
		self.type = state["type"] 
		self.channels = state["channels"] 
		self.timepoints = state["timepoints"] 
		self.dataSetNumber = state["n"] 
		self.serialized	 = state["serialized"] 
