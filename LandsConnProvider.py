# -*- coding: utf-8 -*-

"""
***************************************************************************
    LandsConnProvider.py
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
__date__ = 'August 2018'
__copyright__ = '(C) 2018, Guillem Domingo Ribas'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt.QtGui import QIcon

from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.core.ProcessingConfig import Setting, ProcessingConfig
from processing.tools import system

from landscape_connectivity.Pairwise import Pairwise
from landscape_connectivity.LCP_Network import LCP_Network
from landscape_connectivity.OneToAll import OneToAll
from landscape_connectivity.Advanced import Advanced
from landscape_connectivity.CircuitscapeUtils import CircuitscapeUtils

pluginPath = os.path.dirname(__file__)


class LandsConnProvider(AlgorithmProvider):

    def __init__(self):
        AlgorithmProvider.__init__(self)

        self.activate = False

        self.alglist = [Pairwise(), OneToAll(), Advanced(), LCP_Network()]
        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        AlgorithmProvider.initializeSettings(self)

        if system.isWindows():
            ProcessingConfig.addSetting(Setting(self.getDescription(),
                CircuitscapeUtils.CIRCUITSCAPE_FOLDER,
                'Circuitscape folder',
                CircuitscapeUtils.circuitscapePath()))

        ProcessingConfig.addSetting(Setting(self.getDescription(),
            CircuitscapeUtils.LOG_COMMANDS,
            'Log execution commands',
            True))
        ProcessingConfig.addSetting(Setting(self.getDescription(),
            CircuitscapeUtils.LOG_CONSOLE,
            'Log console output',
            True))

        ProcessingConfig.addSetting(Setting(self.getDescription(),
            CircuitscapeUtils.FOUR_NEIGHBOURS,
            'Connect raster cells to four neighbors instead of eight',
            False))
        ProcessingConfig.addSetting(Setting(self.getDescription(),
            CircuitscapeUtils.AVERAGE_CONDUCTANCE,
            'Use average conductance instead of resistance for connections '
            'between cells',
            False))
        ProcessingConfig.addSetting(Setting(self.getDescription(),
            CircuitscapeUtils.PREEMPT_MEMORY,
            'Preemptively release memory when possible',
            False))
        ProcessingConfig.addSetting(Setting(self.getDescription(),
            CircuitscapeUtils.MAX_CURRENT_MAPS,
            'Write maximum of current maps',
            False))
        ProcessingConfig.addSetting(Setting(self.getDescription(),
            CircuitscapeUtils.CUM_MAX_MAPS,
            'Write cumulative & maximum current maps only',
            False))
        ProcessingConfig.addSetting(Setting(self.getDescription(),
            CircuitscapeUtils.ZERO_FOCAL,
            'Set focal nodes currents to zero',
            False))
        ProcessingConfig.addSetting(Setting(self.getDescription(),
            CircuitscapeUtils.LOG_TRANSFORM,
            'Log-transform current maps',
            False))
        ProcessingConfig.addSetting(Setting(self.getDescription(),
            CircuitscapeUtils.COMPRESS_OUTPUT,
            'Compress output grids',
            False))

    def unload(self):
        AlgorithmProvider.unload(self)

        if system.isWindows():
            ProcessingConfig.removeSetting(
                CircuitscapeUtils.CIRCUITSCAPE_FOLDER)

        ProcessingConfig.removeSetting(CircuitscapeUtils.LOG_COMMANDS)
        ProcessingConfig.removeSetting(CircuitscapeUtils.LOG_CONSOLE)

        ProcessingConfig.removeSetting(CircuitscapeUtils.FOUR_NEIGHBOURS)
        ProcessingConfig.removeSetting(CircuitscapeUtils.AVERAGE_CONDUCTANCE)
        ProcessingConfig.removeSetting(CircuitscapeUtils.PREEMPT_MEMORY)
        ProcessingConfig.removeSetting(CircuitscapeUtils.MAX_CURRENT_MAPS)
        ProcessingConfig.removeSetting(CircuitscapeUtils.CUM_MAX_MAPS)
        ProcessingConfig.removeSetting(CircuitscapeUtils.ZERO_FOCAL)
        ProcessingConfig.removeSetting(CircuitscapeUtils.LOG_TRANSFORM)
        ProcessingConfig.removeSetting(CircuitscapeUtils.COMPRESS_OUTPUT)

    def getName(self):
        return 'Circuitscape'

    def getDescription(self):
        return 'Landscape Connectivity Toolbox'

    def getIcon(self):
        return QIcon(os.path.join(pluginPath, 'icons', 'mobility.png'))

    def _loadAlgorithms(self):
        self.algs = self.alglist
