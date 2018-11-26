# -*- coding: utf-8 -*-

"""
***************************************************************************
    OneToAll.py
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
import ConfigParser
import glob
import tempfile
import subprocess

from qgis.core import *
from qgis.analysis import *

from osgeo import gdal

from processing.tools import dataobjects, vector
from processing.core.Processing import Processing
from processing.core.ProcessingLog import ProcessingLog
from processing.core.ProcessingConfig import ProcessingConfig
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import \
    GeoAlgorithmExecutionException

from processing.core.parameters import (ParameterRaster,
                                        ParameterVector,
                                        ParameterBoolean,
                                        ParameterString,
                                        ParameterFile,
                                        ParameterSelection)
from processing.core.outputs import OutputDirectory

from processing.tools import system

from landscape_connectivity.CircuitscapeAlgorithm import CircuitscapeAlgorithm
from CircuitscapeUtils import CircuitscapeUtils


class OneToAll(CircuitscapeAlgorithm):

    MODE = 'MODE'
    RESISTANCE_MAP = 'RESISTANCE_MAP'
    IS_CONDUCTANCES = 'IS_CONDUCTANCES'
    FOCAL_NODE = 'FOCAL_NODE'
    WRITE_CURRENT_MAP = 'WRITE_CURRENT_MAP'
    WRITE_VOLTAGE_MAP = 'WRITE_VOLTAGE_MAP'
    MASK = 'MASK'
    SHORT_CIRCUIT = 'SHORT_CIRCUIT'
    SOURCE_STRENGTH = 'SOURCE_STRENGTH'
    BASENAME = 'BASENAME'
    DIRECTORY = 'DIRECTORY'

    MODES = ['One to all',
             'All to one'
            ]
    MODES_DICT = {0: 'one-to-all',
                  1: 'all-to-one'
                 }

    def __init__(self):
        CircuitscapeAlgorithm.__init__(self)

    def defineCharacteristics(self):
        self.name = 'One-to-all / All-to-one modelling'
        self.group = 'Circuitscape'

        self.addParameter(ParameterSelection(self.MODE,
            'Modelling mode', self.MODES, 0))
        self.addParameter(ParameterRaster(self.RESISTANCE_MAP,
            'Raster resistance map'))
        self.addParameter(ParameterBoolean(self.IS_CONDUCTANCES,
            'Data represent conductances instead of resistances', False))
        self.addParameter(ParameterVector(self.FOCAL_NODE,
            'Focal node location'))
        self.addParameter(ParameterBoolean(self.WRITE_CURRENT_MAP,
            'Create current map', True))
        self.addParameter(ParameterBoolean(self.WRITE_VOLTAGE_MAP,
            'Create voltage map', True))
        self.addParameter(ParameterRaster(self.MASK,
            'Raster mask file', optional=True))
        self.addParameter(ParameterRaster(self.SHORT_CIRCUIT,
            'Raster short-circuit region file', optional=True))
        self.addParameter(ParameterRaster(self.SOURCE_STRENGTH,
            'Source strength file', optional=True))
        self.addParameter(ParameterString(self.BASENAME,
            'Output basename', 'csoutput'))

        self.addOutput(OutputDirectory(self.DIRECTORY, 'Output directory'))

    def processAlgorithm(self, progress):
        if system.isWindows():
            path = CircuitscapeUtils.circuitscapePath()
            if path == '':
                raise GeoAlgorithmExecutionException(
                    'Circuitscape folder is not configured.\nPlease '
                    'configure it before running Circuitscape algorithms.')

        
        rasterFile = self.getParameterValue(self.RESISTANCE_MAP)
        
        if rasterFile.endswith('.asc'):
            rasterLocation = rasterFile
        else:
            gdal_translate = "C:\\Program Files\\GDAL\\gdal_translate.exe"
            tempFileDirectory = tempfile.gettempdir()            
            rasterSource = str(self.getParameterValue(self.RESISTANCE_MAP))
            rasterDest = str(tempFileDirectory + "/translatedRaster.asc")
            cmd = "-of AAIGrid"
#            fullCMD = ' '.join([gdal_translate, cmd, rasterSource, rasterDest])
            subprocess.call(["gdal_translate","-of","AAIGrid", rasterSource, rasterDest])
            rasterLocation = rasterDest
        
        
   
        tempFileDirectory = tempfile.gettempdir()
        output_file = open(tempFileDirectory + "/cs_points.txt", 'w')
        i=1
        layer = QgsVectorLayer(self.getParameterValue(self.FOCAL_NODE), "creator", "ogr")
        for feature in layer.getFeatures():
            geom = feature.geometry()
#                line = (str(i) + "\t" + str(geom.asPoint().x()) + "\t" + str(geom.asPoint().y() )+ "\n")
#                unicode_line = line.encode('utf-8')
            line = (str(i) + "\t" + str(geom.asPoint().x()) + "\t" + str(geom.asPoint().y() )+ "\n")
            output_file.write(line)
            i = i+1
        output_file.close()
        
        
        mode = self.MODES_DICT[self.getParameterValue(self.MODE)]
        resistance = str(rasterLocation)
        useConductance = str(not self.getParameterValue(self.IS_CONDUCTANCES))
        focal = str(tempFileDirectory + "\cs_points.txt")
        writeCurrent = str(self.getParameterValue(self.WRITE_CURRENT_MAP))
        writeVoltage = str(self.getParameterValue(self.WRITE_VOLTAGE_MAP))

        # advanced parameters
        mask = self.getParameterValue(self.MASK)
        shortCircuit = self.getParameterValue(self.SHORT_CIRCUIT)
        sourceStrength = self.getParameterValue(self.SOURCE_STRENGTH)

        baseName = self.getParameterValue(self.BASENAME)
        directory = self.getOutputValue(self.DIRECTORY)
        basePath = os.path.join(directory, baseName)

        iniPath = CircuitscapeUtils.writeConfiguration()
        cfg = ConfigParser.SafeConfigParser()
        cfg.read(iniPath)

        commands = self.prepareInputs()

        # set parameters
        cfg.set('Circuitscape mode', 'scenario', mode)

        cfg.set('Habitat raster or graph',
                'habitat_map_is_resistances',
                useConductance)
        if resistance in self.exportedLayers.keys():
            resistance = self.exportedLayers[resistance]
        cfg.set('Habitat raster or graph', 'habitat_file', resistance)

        if focal in self.exportedLayers.keys():
            focal = self.exportedLayers[focal]
        cfg.set('Options for pairwise and one-to-all and all-to-one modes',
                'point_file',
                focal)

        if sourceStrength is not None:
            cfg.set('Options for one-to-all and all-to-one modes',
                    'variable_source_file',
                    sourceStrength)
            cfg.set('Options for one-to-all and all-to-one modes',
                    'use_variable_source_strengths',
                    'True')

        if mask is not None:
            if mask in self.exportedLayers.keys():
                mask = self.exportedLayers[mask]
            cfg.set('Mask file', 'mask_file', mask)
            cfg.set('Mask file', 'use_mask', 'True')

        if shortCircuit is not None:
            if shortCircuit in self.exportedLayers.keys():
                shortCircuit = self.exportedLayers[shortCircuit]
            cfg.set('Short circuit regions (aka polygons)',
                    'polygon_file',
                    shortCircuit)
            cfg.set('Short circuit regions (aka polygons)',
                    'use_polygons',
                    'True')

        cfg.set('Output options', 'write_cur_maps', writeCurrent)
        cfg.set('Output options', 'write_volt_maps', writeVoltage)
        cfg.set('Output options', 'output_file', basePath)

        # write configuration back to file
        with open(iniPath, 'wb') as f:
            cfg.write(f)

        if system.isWindows():
            commands.append('"{}" {}'.format(os.path.join(path, 'cs_run.exe'), iniPath))
        else:
            commands.append('csrun.py {}'.format(iniPath))

        CircuitscapeUtils.createBatchJobFileFromCommands(commands)
        loglines = []
        loglines.append('Circuitscape execution commands')
        for line in commands:
            progress.setCommand(line)
            loglines.append(line)

        if ProcessingConfig.getSetting(CircuitscapeUtils.LOG_COMMANDS):
            ProcessingLog.addToLog(ProcessingLog.LOG_INFO, loglines)

        CircuitscapeUtils.executeCircuitscape(commands, progress)
