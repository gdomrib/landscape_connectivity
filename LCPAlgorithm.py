# -*- coding: utf-8 -*-

"""
***************************************************************************
    LCPAlgorithm.py
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

from osgeo import gdal

from qgis.PyQt.QtGui import QIcon

from processing.core.GeoAlgorithm import GeoAlgorithm


from processing.tools import system



pluginPath = os.path.dirname(__file__)


class LCPAlgorithm(GeoAlgorithm):

    def __init__(self):
        GeoAlgorithm.__init__(self)


    def getIcon(self):
        return QIcon(os.path.join(pluginPath, 'icons', 'lcp.png'))
    