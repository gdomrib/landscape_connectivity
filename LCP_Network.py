# -*- coding: utf-8 -*-
"""
Created on Sat Jul  7 19:06:28 2018

@author: Guillem
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 16:09:58 2018

@author: Guillem
"""

# -*- coding: utf-8 -*-

"""
***************************************************************************
    LCP_Network.py
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
import os.path
import numpy as np

import numpy.ma as ma

import timeit

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

from landscape_connectivity.LCPAlgorithm import LCPAlgorithm


class LCP_Network(LCPAlgorithm):

    ORIGIN_LAYER = 'ORIGIN_LAYER'
    DESTINATION_LAYER = 'DESTINATION_LAYER'
    BASE_RASTER = 'BASE_RASTER'
    DIRECTORY = 'DIRECTORY'
    BASENAME = 'BASENAME'

    def __init__(self):
        LCPAlgorithm.__init__(self)

    def defineCharacteristics(self):
        self.name = 'LCP Network modelling'
        self.group = 'Least-Cost Path'

        self.addParameter(ParameterVector(self.ORIGIN_LAYER,
            'Points of origin'))
        self.addParameter(ParameterVector(self.DESTINATION_LAYER,
            'Points of destination'))
        self.addParameter(ParameterRaster(self.BASE_RASTER,
            'Cost surface raster'))
        self.addParameter(ParameterString(self.BASENAME,
            'Output basename', 'lcp_network'))

        self.addOutput(OutputDirectory(self.DIRECTORY, 'Output directory'))

        
    def loadBaseRaster(self):
        path =  str(self.getParameterValue(self.BASE_RASTER))
        return gdal.Open(path)
        
    def getCell( self, point, surface ):
#        get local coordinates for point in surface
        transform = surface.GetGeoTransform()
        topLeft = QgsPoint(transform[0], transform[3])

        pointInRaster = QgsPoint(point.x() - topLeft.x(), topLeft.y() - point.y())
        # swap axes
        cell = QgsPoint(int(pointInRaster.y()/-transform[5]), int(pointInRaster.x()/transform[1]))
        return cell
        
    def getGlobalPos(self, localPos, surface):
#       get global coordinates for local point in surface

        transform = surface.GetGeoTransform()
        topLeft = QgsPoint(transform[0], transform[3])

        # swap axes
        pos = QgsPoint(localPos.y()*(-transform[5]), localPos.x()*(-transform[1]))
        globalPoint = QgsPoint(pos.x()+topLeft.x(), pos.y()+topLeft.y())
        
        return globalPoint
        
    def isInside(self, cell, surface ):
#       returns true if cellin surface or false if it is not
        if cell.x() < 0 or cell.x() >= surface.RasterYSize or cell.y() <0 or cell.y() >= surface.RasterXSize :
            return False
        return True
        
    def getNeighbors(self, point, surface, costMap ):
#        current: only four direct neighbors
        neighbors = list()
        nodata = int(surface.GetRasterBand(1).GetNoDataValue())

        candidate = QgsPoint(point.x()-1, point.y())
        if self.isInside(candidate, surface) and costMap[int(candidate.x()), int(candidate.y())] != nodata:
            neighbors.append(candidate)

        candidate = QgsPoint(point.x()+1, point.y())
        if self.isInside(candidate, surface) and costMap[int(candidate.x()), int(candidate.y())] != nodata:
            neighbors.append(candidate)

        candidate = QgsPoint(point.x(), point.y()-1)
        if self.isInside(candidate, surface) and costMap[int(candidate.x()), int(candidate.y())] != nodata:
            neighbors.append(candidate)

        candidate = QgsPoint(point.x(), point.y()+1)
        if self.isInside(candidate, surface) and costMap[int(candidate.x()), int(candidate.y())] != nodata:
            neighbors.append(candidate)


        return neighbors
        
        
    def getMinimumUnvisited(self, visited, distances ):
        # set to nul values of already visited (kind of a mask)
        possibleValues = ma.masked_array(distances, mask=visited)
        candidates = np.where(possibleValues == np.nanmin(possibleValues))  

        if len(candidates[0]) == 0:
            return None

        selected = np.random.randint(len(candidates[0]))
        return QgsPoint(candidates[0][selected], candidates[1][selected])
        
    def computeCost( self, originGeo, baseRaster):        
        origin = self.getCell(originGeo, baseRaster)
        costValues = baseRaster.GetRasterBand(1).ReadAsArray()

        if not self.isInside(origin, baseRaster):
            return None

        # initialize helper matrices
        width,height = costValues.shape
        visited = np.full([width, height], False, dtype=bool)
        distances = np.full([width,height], np.nan, dtype=np.float32)

        # initialize current
        current = origin

        visited[int(current.x()), int(current.y())] = True
        distances[int(current.x()), int(current.y())] = 0

        candidates = True
        while candidates: 
            neighbors = self.getNeighbors(current, baseRaster, costValues)
            for neighbor in neighbors:
                
                tentativeDistance = distances[int(current.x()), int(current.y())] + costValues[int(neighbor.x()), int(neighbor.y())]
                # cost can never be negative
                if tentativeDistance < 0:
                    tentativeDistance = 0
                if np.isnan(distances[int(neighbor.x()), int(neighbor.y())]) or distances[int(neighbor.x()), int(neighbor.y())] > tentativeDistance:
                    distances[int(neighbor.x()), int(neighbor.y())] = tentativeDistance

            visited[int(current.x()), int(current.y())] = True

            current = self.getMinimumUnvisited(visited, distances)
            if not current:
                candidates = False

        return distances
        
    def getPath( self, originGeo, destinationGeo, baseRaster, costMap):
    
        pathLine = []
        origin = self.getCell(originGeo, baseRaster)
        destination = self.getCell(destinationGeo, baseRaster)
            
        if not self.isInside(destination, baseRaster):
            return None

        width,height = costMap.shape
        
        current = destination
    
        while current != origin:
            pathLine.append(current)
            neighbors = self.getNeighbors(current, baseRaster, costMap)
        
            minValue = costMap[int(current.x()), int(current.y())]
       
            for neighbor in neighbors:
        
                # if already in path:
                alreadyInPath = False 
                for pathPoint in pathLine:
                    if pathPoint.sqrDist(neighbor)<1.0:
                        alreadyInPath = True
                        break

                if alreadyInPath:
                    continue

                if costMap[int(neighbor.x()),int(neighbor.y())] <= minValue:
                    minValue = costMap[int(neighbor.x()),int(neighbor.y())]
                    current = neighbor


        pathLine.append(current)

        globalPath = []
        for localPoint in pathLine:
            globalPath.append(self.getGlobalPos(localPoint, baseRaster))

        return globalPath
        
        
    def storeCostMap(self, costMap, baseRaster, index):
        directory = self.getOutputValue(self.DIRECTORY)
        baseName = self.getParameterValue(self.BASENAME)
        outputName = str(directory)+"/"+str(baseName)+"_distances_"+str(index)+".tif"

        newRaster = gdal.GetDriverByName('GTiff').Create(outputName, baseRaster.RasterXSize, baseRaster.RasterYSize, 1, gdal.GDT_Float32)
        newRaster.SetProjection(baseRaster.GetProjection())
        newRaster.SetGeoTransform(baseRaster.GetGeoTransform())
        newRaster.GetRasterBand(1).WriteArray(costMap,0,0)
        newRaster.GetRasterBand(1).SetNoDataValue(np.nan)
        newRaster.GetRasterBand(1).FlushCache()
        newRaster = None
        
        newRasterQGIS = QgsRasterLayer(outputName, "distances_"+str(index))
        newRasterQGIS.setContrastEnhancement(QgsContrastEnhancement.StretchToMinimumMaximum)

        
        
    def processAlgorithm(self,progress):


        origins = QgsVectorLayer(self.getParameterValue(self.ORIGIN_LAYER), "creator", "ogr")
        destinations = QgsVectorLayer(self.getParameterValue(self.DESTINATION_LAYER), "creator", "ogr")
        baseRaster = self.loadBaseRaster()

        transform = baseRaster.GetGeoTransform()

        topLeft = QgsPoint(transform[0], transform[3])
    
        pointsListO = []
        for point in origins.getFeatures():
            pointsListO.append(point.geometry().asPoint())
  
        pointsListD = []
        for point in destinations.getFeatures():
            pointsListD.append(point.geometry().asPoint())


        index = 0          

        ## create the shapefile
        projection = baseRaster.GetProjection()        
        lineLayer = QgsVectorLayer("linestring?crs=" + projection, "least cost path network", "memory")

        for source in pointsListO:

        # compute cost map for the entire area
               

            distances = self.computeCost(source, baseRaster)



            self.storeCostMap(distances, baseRaster, index)

            for destination in pointsListD:
                if destination == source:
                    continue
                pathLine = self.getPath(source, destination, baseRaster, distances)
                if pathLine==None:

                    return
                
                features = QgsFeature()
                ## set geometry from the list of QgsPoint's to the feature
                features.setGeometry(QgsGeometry.fromPolyline(pathLine))
                lineLayer.dataProvider().addFeatures([features])
            index = index + 1
            
        directory = self.getOutputValue(self.DIRECTORY)
        QgsVectorFileWriter.writeAsVectorFormat(lineLayer, str(directory)+"\least_cost_path.shp", "CP1250", None, "ESRI Shapefile", False)
