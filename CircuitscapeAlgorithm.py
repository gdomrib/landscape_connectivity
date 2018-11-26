# -*- coding: utf-8 -*-

"""
***************************************************************************
    CircuitscapeAlgorithm.py
    ---------------------
    Date                 : June 2018
    Copyright            : (C) 2018 by Guillem Domingo Ribas
    Email                : guillem.dri@gmail.com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Guillem Domingo Ribas'
__date__ = 'June 2018'
__copyright__ = '(C) 2018, Guillem Domingo Ribas'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt.QtGui import QIcon

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import (ParameterRaster,
                                        ParameterVector,
                                        ParameterFile)

from processing.tools import system

from CircuitscapeUtils import CircuitscapeUtils

pluginPath = os.path.dirname(__file__)

sessionExportedLayers = {}


class CircuitscapeAlgorithm(GeoAlgorithm):

    def __init__(self):
        GeoAlgorithm.__init__(self)

        self.exportedLayers = {}

    def getIcon(self):
        return QIcon(os.path.join(pluginPath, 'icons', 'circuitscape.png'))

    def exportRasterLayer(self, source):
        global sessionExportedLayers

        if source in sessionExportedLayers:
            self.exportedLayers[source] = sessionExportedLayers[source]
            return None

        fileName = os.path.basename(source)
        validChars = \
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:'
        fileName = ''.join(c for c in fileName if c in validChars)
        if len(fileName) == 0:
            fileName = 'layer'

        destFilename = system.getTempFilenameInTempFolder(fileName + '.asc')
        self.exportedLayers[source] = destFilename
        sessionExportedLayers[source] = destFilename

        return ''.format(source, destFilename)


    def prepareInputs(self):
        commands = []
        self.exportedLayers = {}
        for param in self.parameters:
            if isinstance(param, ParameterRaster):
                if param.value is None:
                    continue
                value = param.value
                if not value.lower().endswith('asc'):
                    exportCommand = self.exportRasterLayer(value)
                    if exportCommand is not None:
                        commands.append(exportCommand)
        return commands
