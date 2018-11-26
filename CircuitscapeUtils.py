# -*- coding: utf-8 -*-

"""
***************************************************************************
    CircuitscapeUtils.py
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
import stat
import subprocess
import ConfigParser

from processing.core.ProcessingLog import ProcessingLog
from processing.core.ProcessingConfig import ProcessingConfig
from processing.tools.system import getTempFilename, isWindows, userFolder


class CircuitscapeUtils:

    LOG_COMMANDS = 'LOG_COMMANDS'
    LOG_CONSOLE = 'LOG_CONSOLE'
    CIRCUITSCAPE_FOLDER = 'CIRCUITSCAPE_FOLDER'
    FOUR_NEIGHBOURS = 'FOUR_NEIGHBOURS'
    AVERAGE_CONDUCTANCE = 'AVERAGE_CONDUCTANCE'
    PREEMPT_MEMORY = 'PREEMPT_MEMORY'
    MAX_CURRENT_MAPS = 'MAX_CURRENT_MAPS'
    CUM_MAX_MAPS = 'CUM_MAX_MAPS'
    ZERO_FOCAL = 'ZERO_FOCAL'
    COMPRESS_OUTPUT = 'COMPRESS_OUTPUT'
    LOG_TRANSFORM = 'LOG_TRANSFORM'

    @staticmethod
    def circuitscapePath():
        folder = ProcessingConfig.getSetting(
            CircuitscapeUtils.CIRCUITSCAPE_FOLDER)
        if folder is None or folder == '':
            folder = ''
            if isWindows():
                testPath = 'C:/Program Files/Circuitscape'
                if os.path.exists(os.path.join(testPath, 'cs_run.exe')):
                    folder = testPath
        return folder

    @staticmethod
    def writeConfiguration():
        cfg = ConfigParser.SafeConfigParser()

        cfg.add_section('Options for advanced mode')
        cfg.set(
            'Options for advanced mode', 'ground_file_is_resistances', 'True')
        cfg.set('Options for advanced mode', 'remove_src_or_gnd', 'keepall')
        cfg.set('Options for advanced mode', 'ground_file', '')
        cfg.set('Options for advanced mode', 'use_unit_currents', 'False')
        cfg.set('Options for advanced mode', 'source_file', '')
        cfg.set('Options for advanced mode', 'use_direct_grounds', 'False')

        cfg.add_section('Mask file')
        cfg.set('Mask file', 'mask_file', '')
        cfg.set('Mask file', 'use_mask', 'False')

        cfg.add_section('Calculation options')
        cfg.set('Calculation options', 'low_memory_mode', 'False')
        cfg.set('Calculation options', 'parallelize', 'False')
        cfg.set('Calculation options', 'solver', 'cg+amg')
        cfg.set('Calculation options', 'print_timings', 'True')
        value = str(
            ProcessingConfig.getSetting(CircuitscapeUtils.PREEMPT_MEMORY))
        cfg.set('Calculation options', 'preemptive_memory_release', value)
        cfg.set('Calculation options', 'print_rusages', 'False')
        cfg.set('Calculation options', 'max_parallel', '0')

        cfg.add_section('Short circuit regions (aka polygons)')
        cfg.set('Short circuit regions (aka polygons)', 'polygon_file', '')
        cfg.set('Short circuit regions (aka polygons)',
            'use_polygons', 'False')

        cfg.add_section('Options for one-to-all and all-to-one modes')
        cfg.set('Options for one-to-all and all-to-one modes',
            'use_variable_source_strengths', 'False')
        cfg.set('Options for one-to-all and all-to-one modes',
            'variable_source_file', '')

        cfg.add_section('Output options')
        cfg.set('Output options', 'set_null_currents_to_nodata', 'False')
        value = str(ProcessingConfig.getSetting(CircuitscapeUtils.ZERO_FOCAL))
        cfg.set('Output options', 'set_focal_node_currents_to_zero', value)
        cfg.set('Output options', 'set_null_voltages_to_nodata', 'False')
        value = str(
            ProcessingConfig.getSetting(CircuitscapeUtils.COMPRESS_OUTPUT))
        cfg.set('Output options', 'compress_grids', value)
        cfg.set('Output options', 'write_cur_maps', 'True')
        cfg.set('Output options', 'write_volt_maps', 'True')
        cfg.set('Output options', 'output_file', '')
        value = str(
            ProcessingConfig.getSetting(CircuitscapeUtils.CUM_MAX_MAPS))
        cfg.set('Output options', 'write_cum_cur_map_only', value)
        value = str(
            ProcessingConfig.getSetting(CircuitscapeUtils.LOG_TRANSFORM))
        cfg.set('Output options', 'log_transform_maps', value)
        value = str(
            ProcessingConfig.getSetting(CircuitscapeUtils.MAX_CURRENT_MAPS))
        cfg.set('Output options', 'write_max_cur_maps', value)

        cfg.add_section('Options for reclassification of habitat data')
        cfg.set('Options for reclassification of habitat data',
            'reclass_file', '')
        cfg.set('Options for reclassification of habitat data',
            'use_reclass_table', 'False')

        cfg.add_section('Logging Options')
        cfg.set('Logging Options', 'log_level', 'INFO')
        cfg.set('Logging Options', 'log_file', 'None')
        cfg.set('Logging Options', 'profiler_log_file', 'None')
        cfg.set('Logging Options', 'screenprint_log', 'False')

        cfg.add_section(
            'Options for pairwise and one-to-all and all-to-one modes')
        cfg.set('Options for pairwise and one-to-all and all-to-one modes',
            'included_pairs_file', '')
        cfg.set('Options for pairwise and one-to-all and all-to-one modes',
            'use_included_pairs', 'False')
        cfg.set('Options for pairwise and one-to-all and all-to-one modes',
            'point_file', '')

        cfg.add_section('Connection scheme for raster habitat data')
        value = str(
            ProcessingConfig.getSetting(CircuitscapeUtils.AVERAGE_CONDUCTANCE))
        cfg.set('Connection scheme for raster habitat data',
            'connect_using_avg_resistances', value)
        value = str(
            ProcessingConfig.getSetting(CircuitscapeUtils.FOUR_NEIGHBOURS))
        cfg.set('Connection scheme for raster habitat data',
            'connect_four_neighbors_only', value)

        cfg.add_section('Habitat raster or graph')
        cfg.set('Habitat raster or graph',
            'habitat_map_is_resistances', 'True')
        cfg.set('Habitat raster or graph', 'habitat_file', '')

        cfg.add_section('Circuitscape mode')
        cfg.set('Circuitscape mode', 'data_type', 'raster')
        cfg.set('Circuitscape mode', 'scenario', '')

        iniPath = getTempFilename('.ini')
        with open(iniPath, 'wb') as f:
            cfg.write(f)

        return iniPath

    @staticmethod
    def batchJobFilename():
        if isWindows():
            fileName = 'circuitscape_batch_job.bat'
        else:
            fileName = 'circuitscape_batch_job.sh'

        batchFile = userFolder() + os.sep + fileName

        return batchFile

    @staticmethod
    def createBatchJobFileFromCommands(commands):
        batchFile = open(CircuitscapeUtils.batchJobFilename(), 'w')
        for command in commands:
            batchFile.write(command.encode('utf8') + '\n')

        batchFile.write('exit')
        batchFile.close()

    @staticmethod
    def executeCircuitscape(command, progress):
        if isWindows():
            command = ['cmd.exe', '/C ', CircuitscapeUtils.batchJobFilename()]
        else:
            os.chmod(CircuitscapeUtils.batchJobFilename(), stat.S_IEXEC
                     | stat.S_IREAD | stat.S_IWRITE)
            command = [CircuitscapeUtils.batchJobFilename()]

        fused_command = ''.join(['"%s" ' % c for c in command])
        loglines = []
        loglines.append('Circuitscape execution console output')
        proc = subprocess.Popen(
            fused_command,
            shell=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            ).stdout
        for line in iter(proc.readline, ''):
            loglines.append(line)

        if ProcessingConfig.getSetting(CircuitscapeUtils.LOG_CONSOLE):
            ProcessingLog.addToLog(ProcessingLog.LOG_INFO, loglines)
