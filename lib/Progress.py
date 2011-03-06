"""
 Unit: Progress.py
 Project: BioImageXD
 Description:

 A module that can be used to report progress of complex filters

 Copyright (C) 2005	 BioImageXD Project
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
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111 - 1307	 USA

"""
__author__ = "BioImageXD Project <http://www.bioimagexd.net/>"
__version__ = "$Revision$"
__date__ = "$Date$"

class Progress:
	"""
	"""
	def __init__(self):
		"""
		Initialization
		"""
		self.name = ""
		self.progress = 0.0

	def getProgress(self):
		"""
		Return filter progress
		"""
		return self.progress

	def setProgress(self, progress):
		"""
		Sets new progress
		"""
		self.progress = progress
		
