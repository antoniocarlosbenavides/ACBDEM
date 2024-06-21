# -*- coding: utf-8 -*-
#las librerias se importan a python en la consola osgeo4w shell
#teclenado python3 -m pip install pdal o cualquier otra libreria
#    forcc2.py     CLOUDCOMPARE MODELO DIGITAL DE TERRENO
# Ayuda de CloudCompare: https://www.cloudcompare.org/doc/wiki/index.php/Command_line_mode
# GEOSTATISTICAL KRIGING INTERPOLATION https://youtu.be/dg1BosmdIwc

import pathlib
from pathlib import Path, PureWindowsPath, PurePath

from PyQt5.QtWidgets import QDialog,QLabel, QApplication
from qgis.PyQt import uic
import os
import processing
import subprocess
from qgis.utils import iface
from qgis.core import QgsProject,QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem,QgsExpressionContextUtils
from qgis.PyQt.QtWidgets import QMessageBox

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "forcc2.ui"))

class FormularioCloudComp2(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(FormularioCloudComp2, self).__init__(parent)
        self.setupUi(self)
        self.btnccomp.mousePressEvent = self.malladtm
        self.pbcierra.clicked.connect(self.cierraformulario)
        self.btnccomp.show() #muestra el boton pbpdal
        self.pbcierra.hide() #oculta el boton cierra
        self.pbrutacc.mousePressEvent = self.localizacc
        global malla,radio,tipo_salida, pdalconsola,ejecutable,rutacloudcompare,crs
        self.project = QgsProject.instance() #llamada a todas las variables del proyecto
        proj_variables = QgsExpressionContextUtils.projectScope(self.project)  # llamada a todas las variables del proyecto
        rutacloudcompare = str(proj_variables.variable('acbrutacc'))#llamada a la variable 'acbrutacc' en formato cadena
        self.lerutacc.setText(rutacloudcompare)
        ejecutable = str(proj_variables.variable('acbejecutable'))  # llamada a la variable 'acbejecutable' en formato cadena
        self.filecc.setFilePath(ejecutable) #asigna al QgsFileWidget la ruta de la variable ejecutable
        filtro = "Archivos ejecutables (*.exe);;Todos los archivos (*)"
        self.filecc.setFilter(filtro) #aplica el filtro para la ruta de cloudcompare solo exe

        malla=2
        self.qlemalla.setText(str(malla))
        radio=max(50,malla+2)
        self.qleradio.setText(str(radio))
        tipo_salida="KRIGING"
        self.qlelidar.setText("NUBE_DEM_CC.laz")
        self.qleraster2.setText("DEM_CC.tif")
        crs = QgsProject.instance().crs()
        self.qlecrs.setText(format(crs.postgisSrid()))
        self.qlecrs5.setText(format(crs.description()))
        self.qlemalla.textChanged.connect(self.actualiza)   #cuando el texto de malla cambie se actualiza el formulario


    def actualiza(self,event):
        radio=max(50,float(self.qlemalla.text())+2) #toma el valor flotante del texto en label qlemalla y procesa
        self.qleradio.setText(str(radio)) #actualiza el valor del radio
        self.repaint() #repinta

    def recortanube(self,event):
        # Establecer la variable de entorno PATH

        capas_corte= QgsProject.instance().mapLayersByName("MASCARA")
        if capas_corte:
            capa_corte=capas_corte[0]
        extension = capa_corte.extent()
        #COORDENADAS DE EXTENSIÓN DE LA CAPA
        xmin = extension.xMinimum()
        ymin = extension.yMinimum()
        xmax = extension.xMaximum()
        ymax = extension.yMaximum()

        rutanube2 =rutanube+"/NUBEUNIDA.laz"
        rutanube3 =rutanube+"/NUBEUNIDAREC.laz"

        os.environ["PATH"] = self.lerutacc.text() + ";" + os.environ["PATH"]  # Posicionado en la ruta de CloudCompare
        rutafilecc = self.filecc.filePath()  # ruta seleccionada en QgsFileWidget incluso archivo y extensión
        ejecutable = os.path.basename(rutafilecc)  # solo nombre del ejecutable CloudCompare.exe
        # Comando de CloudCompare
        comandocc = [
            # "CloudCompare.exe", # Ejecuta cloudcompare aunque no lo abre
            ejecutable,  # Ejecuta cloudcompare aunque no lo abre
            "-AUTO_SAVE OFF",  # Neutraliza que adopte el nombre del resultado automatico
            "-O", "-GLOBAL_SHIFT AUTO", f'"{rutanube2}"',
            "-CROP xmin xmax ymin ymax", #Recorta la nube contra una máscara
            "-C_EXPORT_FMT LAS -EXT LAZ",  # cambia el formato para exportar a laz
            "-SAVE_CLOUDS FILE", f'"{rutanube3}"',  # exporta la nube a laz
        ]

    def cargalidar(self,event):
        # Agrega la capa de puntos LAZ
        capapuntos = QgsVectorLayer(rutalidar, self.qlelidar.text())
        src = QgsCoordinateReferenceSystem(int(self.qlecrs.text()), QgsCoordinateReferenceSystem.EpsgCrsId) #define el src
        capapuntos.setCrs(src)  #asigna el src a la capa
        QgsProject.instance().addMapLayer(capapuntos, False)
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('NUBE_CCOMP')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, capapuntos)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas

    def localizacc(self,event):
        rutafilecc=self.filecc.filePath() #ruta seleccionada en QgsFileWidget incluso archivo y extensión
        rutafoldercc=os.path.dirname(rutafilecc) #ruta de la carpeta que contiene el archivo (solo carpetas)
        self.lerutacc.setText(str(rutafoldercc)) #presenta la ruta en el label lerutacc (solo carpetas sin el archivo)
        # V A R I A B L E S
        self.project = QgsProject.instance()
        proj_variables = QgsExpressionContextUtils.projectScope(
            self.project)  # llamada a todas las variables del proyecto
        # cambia el valor de la variable de proyecto
        QgsExpressionContextUtils.setProjectVariable(self.project, 'acbrutacc', rutafoldercc) #variable de la ruta del ejecutable CloudCompare.exe
        QgsExpressionContextUtils.setProjectVariable(self.project, 'acbejecutable', ejecutable) #variable del ejecutable CloudCompare.exe a veces se instala como cloudcompare.exe y no es lo mismo

    def cierraformulario(self,event):
        self.close()

    def malladtm(self,event):

        # Rutas
        rutactual = QgsProject.instance().homePath() #ruta actual
        rutanube=(os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES'))
        rutapdal = (os.path.join(rutactual, 'ACB-DATOS'))                                       #ruta del json
        rutalidar = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/', str(self.qlelidar.text())))
        os.chdir(rutapdal) #cambia de directorio en la consola para crear el archivo bat

        malla=float(self.qlemalla.text())
        radio=float(self.qleradio.text())
        tipo_salida="KRIGING"

        # Ayuda de CloudCompare: https://www.cloudcompare.org/doc/wiki/index.php/Command_line_mode

        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutanubedtm=os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES/DEM_CC_TERRENO.laz')

        # Establecer la variable de entorno PATH
        os.environ["PATH"] = self.lerutacc.text() + ";" + os.environ["PATH"] #Posicionado en la ruta de CloudCompare
        rutafilecc=self.filecc.filePath() #ruta seleccionada en QgsFileWidget incluso archivo y extensión
        ejecutable=os.path.basename(rutafilecc) #solo nombre del ejecutable CloudCompare.exe

        self.elimina(event)  # elimina previamente todos los archivos previos

        # Comando de CloudCompare2 MODELO DIGITAL DEL TERRENO
        comandocc = [
            ejecutable, # Ejecuta cloudcompare aunque no lo abre
            "-AUTO_SAVE OFF", # Neutraliza que adopte el nombre del resultado automatico
            "-O",
            "-GLOBAL_SHIFT AUTO",
            f'"{rutanubedtm}"',
            "-NO_TIMESTAMP",# Evita marcas de tiempo en el nombre del archivo de salida
            "-RASTERIZE",  # crea el raster MDT la nube la malla o la imagen
            "-GRID_STEP " + str(malla),  # rejilla de resolución del raster producto
            "-VERT_DIR 2",  # Especifica dimension z (2)
            "-PROJ MAX",  # Se computa la altura de celda como minimo media y maximo MIN/AVG/MAX
            "-MAX_EDGE_LENGTH 100.0", #Lado del triangulo máximo para interpolar
            #"-EMPTY_FILL INTERP", #Delaunay triangulacion para interpolación del terreno
            #"-EMPTY_FILL KRIGING", # celdas vacias se rellenan por interpolacion MIN_H/MAX_H/CUSTOM_H/INTERP/KRIGING
            #"-KRIGING_KNN 8", #Número de vecinos a considerar en la interpolación de KRIGING
            "-OUTPUT_RASTER_Z", #salida como geotiff raster de elevación
            "-OUTPUT_CLOUD",
            "-C_EXPORT_FMT LAS -EXT LAZ",  # cambia el formato para exportar nube a laz
            "-SAVE_CLOUDS FILE ../ACB-CAPAS/ACB_NUBES/DEM_CC_TERRENO.laz", #exporta la nube a laz
            # MALLA DELAUNAY MESH
            #"-DELAUNAY -AA",  # Triangulación de Delaunay en plano XY
            #"-MAX_EDGE_LENGTH 100.0",  # Lado del triangulo máximo para interpolar
            #"-M_EXPORT_FMT STL -EXT STL",  # cambia el formato para exportar la malla BIN, OBJ, PLY, STL, VTK, MA, FBX.
            #"-SAVE_MESHES FILE ../ACB-CAPAS/ACB_MALLAS/DEM_MALLA.STL",  # exporta la malla

            "-CLEAR",  # Cierra todas las entidades cargadas
        ]
        subprocess.run(" ".join(comandocc), shell=True) #ejecuta cambio directorio y el comando

        self.muevearchivos2(event) # llamada a la funcion que mueve todos los archivos generados a ACBDATOS
        self.recortaraster(event)  # llamada a la funcion que recorta contra la máscara asumiendo que ya están rellenas las celdas con kriging
        self.rellenaraster2(event)    # llamada a la funcion rellena el raster elimina valores nulos
        self.cargaraster2(event)      # llamada a la funcion que carga el raster
        self.hillshade2(event)  # llamada a la funcion que creará y cargará un hillshade
        self.remuevearchivos(event)    # llamada a la funcion que elimina archivos
        self.btnccomp.hide()
        self.pbcierra.show()
        self.close()
    def muevearchivos2(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutanube = os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES/')
        rutadatos = (os.path.join(rutactual, 'ACB-DATOS'))
        rutaraster = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/', str(self.qleraster2.text())))


        for archivo in os.listdir(rutanube):
            rutaentrada = os.path.join(rutanube, archivo)
            if "RASTER_Z" in archivo: # Verifica si el archivo tiene la cadena MERGED_RASTER
                os.replace(rutaentrada, rutaraster)
            else:
                pass

    def recortaraster(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutaraster = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/', str(self.qleraster2.text())))
        rutamascara = (os.path.join(rutactual, 'ACB-CAPAS', "MASCARA.gpkg"))
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/', "DEM_CC_FILL.tif"))  # ruta del raster relleno
        processing.run("gdal:cliprasterbymasklayer",
                       {'INPUT': rutaraster, 'MASK': rutamascara,
                        'SOURCE_CRS': crs, 'TARGET_CRS': crs, 'TARGET_EXTENT': None, 'NODATA': 255,
                        'ALPHA_BAND': False, 'CROP_TO_CUTLINE': True, 'KEEP_RESOLUTION': True, 'SET_RESOLUTION': False,
                        'X_RESOLUTION': None, 'Y_RESOLUTION': None, 'MULTITHREADING': False, 'OPTIONS': '',
                        'DATA_TYPE': 0,
                        'EXTRA': '',
                        'OUTPUT': rutarasterfill})
        # NODATA:255 las celdas sin datos pasa a 255 en principio no deberían verse
    def rellenaraster2(self,event):
        distancia=radio
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutaraster = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/', str(self.qleraster2.text())))
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/', "DEM_CC_FILL.tif"))  # ruta del raster relleno
        processing.run("gdal:fillnodata", {
            'INPUT': rutarasterfill,
            'BAND': 1, 'DISTANCE': distancia, 'ITERATIONS': 0, 'NO_MASK': False,'MASK_LAYER': None, 'OPTIONS': '',
            'EXTRA':crs.postgisSrid(),#atención asigna extra crs
            'OUTPUT': rutarasterfill})


    def cargaraster2(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/', "DEM_CC_FILL.tif"))  # ruta del raster relleno
        # Agrega la capa rutarasterfill ya recorado y rellenada celdas sin valor

        caparaster=QgsRasterLayer(rutarasterfill,self.qleraster2.text())
        QgsProject.instance().addMapLayer(caparaster,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('DEM_CCOMP')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, caparaster)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas

    def hillshade2(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/', "DEM_CC_FILL.tif"))  # ruta del raster relleno
        rutahillshade = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/', "DEM_CC_HILLSHADE.tif"))  # ruta del raster hillshade

        processing.run("gdal:hillshade", {
            'INPUT': rutarasterfill,
            'BAND': 1, 'Z_FACTOR': 2, 'SCALE': 1, 'AZIMUTH': 225, 'ALTITUDE': 45, 'COMPUTE_EDGES': False,
            'ZEVENBERGEN': True, 'COMBINED': False, 'MULTIDIRECTIONAL': True,
            'OPTIONS': 'COMPRESS=DEFLATE|PREDICTOR=2|ZLEVEL=9',
            'EXTRA': QgsCoordinateReferenceSystem('EPSG:'+self.qlecrs.text()), #atención asigna extra crs
            'OUTPUT': rutahillshade})

        # Agrega la capa rutahillshade
        caparaster=QgsRasterLayer(rutahillshade,'DEM_CC_HILLSHADE.tif')
        QgsProject.instance().addMapLayer(caparaster,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('DEM_CCOMP')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, caparaster)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas

    def elimina(self,event):
        proyecto = QgsProject.instance()
        nombre_subgrupo = "DEM_CCOMP"
        subgrupo = proyecto.layerTreeRoot().findGroup(nombre_subgrupo)
        if subgrupo is not None: #si el grupo existe
            capas_subgrupo = subgrupo.children()            # Obtener una lista de todas las capas dentro del subgrupo
            for capa in capas_subgrupo:            # Eliminar cada capa del subgrupo
                proyecto.removeMapLayer(capa.layer())
        else:
            pass

        nombre_subgrupo = "VEGETACION"
        subgrupo = proyecto.layerTreeRoot().findGroup(nombre_subgrupo)
        if subgrupo is not None: #si el grupo existe
            capas_subgrupo = subgrupo.children()            # Obtener una lista de todas las capas dentro del subgrupo
            for capa in capas_subgrupo:            # Eliminar cada capa del subgrupo
                proyecto.removeMapLayer(capa.layer())
        else:
            pass

    def remuevearchivos(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutafile = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP'))

        for archivo in os.listdir(rutafile):
            if "RECOR" in archivo: # Verifica si el archivo tiene la cadena
                try:
                    os.remove(os.path.join(rutafile, archivo))
                except FileNotFoundError:
                    pass