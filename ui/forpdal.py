# -*- coding: utf-8 -*-

#                Ayuda de PDAL
# https://pdal.io/en/2.6.0/tutorial/index.html
#rangos filtro https://pdal.io/en/2.6.0/stages/filters.range.html#ranges
#https://pdal.io/en/2.7.1/stages/filters.html#ground-unclassified
#https://pdal.io/en/2.7.1/pipeline.html#dtm

#    forpdal.py     PDAL MODELO DIGITAL DE TERRENO

from PyQt5.QtWidgets import QDialog,QMessageBox
from qgis.PyQt import uic
from PyQt5.QtGui import QFont, QColor
import os
import json
import processing
import subprocess
import time
from qgis.utils import iface
from qgis.core import QgsProject,QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem,QgsExpressionContextUtils, QgsApplication


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "forpdal.ui"))

class FormularioPdal(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(FormularioPdal, self).__init__(parent)
        self.setupUi(self)
        self.pbpdal.mousePressEvent = self.jsonarchivo
        self.pbpdal.show() #muestra el boton pbpdal
        self.lbproceso2.hide()


        # inicializa el directorio del plugin
        self.plugin_dir = os.path.dirname(__file__)
        global malla,radio,tipo_salida, pdalconsola, contador,ejecutable,crs
        # INCORPORA LAS VARIABLES DE USUARIO GUARDADAS EN EL PROYECTO AL ARRANCAR
        # Carga en los objetos Qtdesigner el valor de la variable
        self.project = QgsProject.instance()
        proj_variables = QgsExpressionContextUtils.projectScope(self.project)  # llamada a todas las variables del proyecto
        # ejecutable cloudcompare
        ejecutable = str(proj_variables.variable('acbejecutable'))  # llamada a la variable 'acbtitulo' en formato cadena

        crs = QgsProject.instance().crs()
        malla=2
        self.qlemalla.setText(str(malla))
        radio=malla+1
        self.qleradio.setText(str(radio))
        tipo_salida="idw"
        self.cmbcalculo.currentText=tipo_salida
        self.qlelidar.setText("NUBE_PDAL_DEM.laz")
        self.qleraster.setText("DEM_PDAL.tif")
        self.qlecrs.setText("25830")

        # Muestra el mensaje
        titulo = "Procesado del archivo json. Creación ráster DEM. Nube única de puntos LAZ"
        cuerpo1 = "Fusión de nubes laz, Clasificación\nEliminación de Ruido, Creación Ráster DEM "
        cuerpo2 = "Archivo " + self.qlelidar.text() + " " + self.qleraster.text() #"DEM_PDAL.tif"
        self.lbproceso.setText(titulo)
        self.lbproceso1.setText(cuerpo1)
        self.lbproceso2.setText(cuerpo2)

    def jsonarchivo(self,event):
        #barra de progreso
        self.eliminasubgrupo(event)     #elimina previamente todos los archivos previos
        QgsRasterLayer().triggerRepaint()
        self.barra.show=True;contador=0
        self.barraprogreso(15, 0, "☻ Declaración de rutas")
        # Rutas
        global rutactual, rutapdal, rutamascara, rutaraster, rutalidar, rutarasterfill,rutahillshade,rutaestilos,rutapseudocolor, caparaster,rutacloud
        rutactual = QgsProject.instance().homePath() #ruta actual
        rutapdal = (os.path.join(rutactual, 'ACB-DATOS'))                                       #ruta del json
        rutamascara = (os.path.join(rutactual, 'ACB-CAPAS', "MASCARA.gpkg"))                    #ruta de la máscara
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_PDAL/', "DEM_PDAL_FILL.tif"))  # ruta del raster relleno
        rutahillshade = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_PDAL/', "DEM_PDAL_HILLSHADE.tif"))  # ruta del raster hillshade
        rutaraster = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_PDAL/', str(self.qleraster.text()))) #"DEM_PDAL.tif"
        rutalidar = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_PDAL/', str(self.qlelidar.text())))
        rutaestilos = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_PDAL/', str(self.qlelidar.text())))
        caparaster=QgsRasterLayer(rutarasterfill,self.qleraster.text()) #"DEM_PDAL.tif"
        rutacloud = (os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES/',str(self.qlelidar.text())))

        #barra de progreso
        self.barraprogreso(30, 15, "☺ Creación del archivo json")
        os.chdir(rutapdal) #cambia de directorio en la consola para crear el json en rutapdal
        malla=float(self.qlemalla.text())
        radio=malla+1
        tipo_salida=self.cmbcalculo.currentText
        self.selecciona(event)   #llama a la funcion selecciona para seleccionar la nube de puntos
        # Clasificacion 1 es no clasificado
        # Clasificacion 2 es terreno
        # Clasificacion 3 a 5 es vegetacion 3baja 1m   4media 1-3m   5alta 3-100m
        # Clasificacion 6 es edificio
        # Clasificacion 7 es punto bajo o ruido a eliminar
        # Clasificacion 9 es agua de mar
        # Clasificacion 12 puntos de solape
        # Clasificacion 17 puentes
        # filters.smrf solo retorna terrestres no se usa en DSM
        # filters.merge fusiona nubes
        # filters.elm filtro mínimo local extendido pasa los puntos bajos a ruido clasificacion 7
        # filters.outlier marca los puntos atípicos
        filename = rutapdal+"acb_pdal.json"

        acb_pdal = {}
        acb_pdal["pipeline"]=listanubes #Está leyenda NUBE.laz

        #MODELO DIGITAL DEL TERRENO
        self.barraprogreso(40, 30, "☺ Filtros en la nube LIDAR única")

        # Filtros outlier y elm
        self.barraprogreso(60, 40, "☺ Filtros outlier y elm")
        if self.chb2.isChecked():
            acb_pdal["pipeline"].append({"type": "filters.elm"}) #puntos bajos pasan a clasificación 7 ruido
        else: pass
        if self.chb1.isChecked():
            acb_pdal["pipeline"].append({"type": "filters.outlier"}) #filtro de valores atípicos pasando a 7 ruido
        else: pass

        # Clasificacion terreno 2 y excluye alturas inapropiadas y además excluye ruido 7
        acb_pdal["pipeline"].append({"type": "filters.range", "limits": "Classification[2:2]","limits": "Classification![7:7]","limits": "Z[0:8850]"})#Filtra solo terreno
        self.barraprogreso(70, 60, "☺ Genera ráster y archivo.laz resultado")

        #Crea DEM nube laz y raster tif
        acb_pdal["pipeline"].append({"type": "writers.las","compression": "true","minor_version": "2","dataformat_id": "3","filename": "../ACB-CAPAS/ACB_NUBES/"+self.qlelidar.text()})
        acb_pdal["pipeline"].append({"filename": "../ACB-CAPAS/ACB_DEM_PDAL/"+self.qleraster.text(),"gdaldriver": "GTiff","resolution": malla,"radius": radio,"output_type": tipo_salida,"type": "writers.gdal"})

        #Ejecuta consola PDAL
        with open('acb_pdal.json','w') as file:
            json.dump(acb_pdal,file,indent=4)
        self.barraprogreso(80, 70, "☻ Ejecución en consola del archivo json")
        pdalconsola=f'pdal pipeline acb_pdal.json' # Orden en consola para ejecutar el archivo json con pdal
        subprocess.run(pdalconsola, cwd=rutapdal, shell=True) #ejecuta cambio directorio y el pdalconsola

        #Rellena huecos en el raster
        self.barraprogreso(90, 80, "☻ Rellena huecos en el ráster")
        self.rellenaraster(event)    # llamada a la funcion rellena el raster elimina valores nulos "DEM_PDAL.tif"
        self.barraprogreso(95, 90, "☺ Carga el ráster en Qgis")

        #Recorta raster anulado
        #self.recortaraster(event)

        #Carga el raster DEM
        self.cargaraster(event)      # llamada a la funcion que carga el raster
        self.barraprogreso(101, 95, "☻ Genera el ráster de fondo Hillshade")

        #Genera y carga el Hillshade
        self.hillshade(event)  # llamada a la funcion que creará y cargará un hillshade

        #Proceso final
        self.lbproceso1.setText("Fin DEM PDAL")
        self.lbproceso3.setText("Proceso pdal DEM LIDAR Terminado\n Se abrirá CloudCompare con la Nube\n Apply All  Yes All")
        self.lbproceso1.setText("NUBE LIDAR y Ráster DEM "+str(malla)+"x"+str(malla)+tipo_salida+"\n Rectificado y Recortado")
        self.cambialetra("Arial Black","blue",10) #llama a la funcionpara cambiar tipo letra, color y tamaño del QLabel
        QMessageBox.information(None, "Fin del Proceso Pdal","Se genera en todas las nubes un escalar Coord Z\nSe abrirá CloudCompare con \nTodas las Nubes disponibles\n Clickea Apply All\n  Yes All")
        self.close()
        #self.cargalidar(event)       # llamada a la funcion que carga el lidar

    def rellenaraster(self,event):
        # Cerrar el archivo raster
        processing.run("gdal:fillnodata", {
            'INPUT': rutaraster,            #"DEM_PDAL.tif"
            'BAND': 1, 'DISTANCE': 50, 'ITERATIONS': 0,'MASK_LAYER': None, 'OPTIONS': '',
            #'EXTRA': QgsCoordinateReferenceSystem('EPSG:'+self.qlecrs.text()), #atención asigna extra crs
            #'EXTRA':crs.postgisSrid(),  # atención asigna extra crs
            'OUTPUT': rutarasterfill})
        # Eliminar el archivo raster
        os.remove(rutaraster)
        caparaster = QgsRasterLayer(rutarasterfill, self.qleraster.text())
        #caparaster.setCrs(crs)

    def recortaraster(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutamascara = (os.path.join(rutactual, 'ACB-CAPAS', "MASCARA.gpkg"))
        processing.run("gdal:cliprasterbymasklayer",
                       {'INPUT': rutarasterfill, 'MASK': rutamascara,
                        'SOURCE_CRS': crs, 'TARGET_CRS': crs, 'TARGET_EXTENT': None, 'NODATA': 255,
                        'ALPHA_BAND': False, 'CROP_TO_CUTLINE': True, 'KEEP_RESOLUTION': False, 'SET_RESOLUTION': False,
                        'X_RESOLUTION': None, 'Y_RESOLUTION': None, 'MULTITHREADING': False, 'OPTIONS': '',
                        'DATA_TYPE': 0,
                        'EXTRA': '',
                        'OUTPUT': rutarasterfill})
    def cargaraster(self,event):
        # Agrega la capa rutarasterfill ya recortado y rellenada celdas sin valor
        caparaster = QgsRasterLayer(rutarasterfill, self.qleraster.text())        #"DEM_PDAL.tif"

        #src = QgsCoordinateReferenceSystem(int(self.qlecrs.text()), QgsCoordinateReferenceSystem.EpsgCrsId) #define el src
        #caparaster.setCrs(src)  #asigna el src a la capa

        QgsProject.instance().addMapLayer(caparaster,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('DEM_PDAL')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, caparaster)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas

    def hillshade(self,event):
        processing.run("gdal:hillshade", {
            'INPUT': rutarasterfill,
            'BAND': 1, 'Z_FACTOR': 2, 'SCALE': 1, 'AZIMUTH': 225, 'ALTITUDE': 45, 'COMPUTE_EDGES': False,
            'ZEVENBERGEN': True, 'COMBINED': False, 'MULTIDIRECTIONAL': True,
            'OPTIONS': 'COMPRESS=DEFLATE|PREDICTOR=2|ZLEVEL=9',
            #'EXTRA': QgsCoordinateReferenceSystem('EPSG:'+self.qlecrs.text()), #atención asigna extra crs
            #'EXTRA': crs.postgisSrid(),  # atención asigna extra crs
            'OUTPUT': rutahillshade})
        # Agrega la capa rutahillshade
        caparaster=QgsRasterLayer(rutahillshade,'DEM_LIDAR_HILLSHADE.tif')
        #caparaster.setCrs(crs)
        QgsProject.instance().addMapLayer(caparaster,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('DEM_PDAL')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, caparaster)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas

    def cargalidar(self,event):
        # Agrega la capa de puntos LAZ
        capapuntos = QgsVectorLayer(rutalidar, self.qlelidar.text())
        src = QgsCoordinateReferenceSystem(int(self.qlecrs.text()), QgsCoordinateReferenceSystem.EpsgCrsId) #define el src
        capapuntos.setCrs(src)  #asigna el src a la capa
        QgsProject.instance().addMapLayer(capapuntos, False)
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('NUBES')          #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, capapuntos)           #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas

    def selecciona(self,event):
        # CREA LA LISTA CON LA RUTA RELATIVA ./NUBEPUNTOS/NOMBRE DE LA NUBE.laz o las
        global listanubes
        rutanube = "../ACB-CAPAS/ACB_NUBES/NUBE.laz"
        listanubes=[]    # Lista para almacenar los nombres de archivos de puntos
        listanubes.append(rutanube)
    def barraprogreso(self,tope,contador,mensaje):
        self.lbproceso1.setText(mensaje)
        while contador <= tope:
            time.sleep(0.2)
            self.barra.setValue(contador);contador += 1
    def abreccompare(self,nubeabrir):
        command = [ejecutable, nubeabrir]
        subprocess.Popen(command)

    def eliminasubgrupo(self,event):
        QgsProject.instance().write() #guarda el proyecto
        nombre_subgrupo = "DEM_PDAL"
        proyecto = QgsProject.instance()
        subgrupo = proyecto.layerTreeRoot().findGroup(nombre_subgrupo)
        if subgrupo is not None: #si el grupo existe
            capas_subgrupo = subgrupo.children()            # Obtener una lista de todas las capas dentro del subgrupo
            for capa in capas_subgrupo:            # Eliminar cada capa del subgrupo
                proyecto.removeMapLayer(capa.layer())
        else:
            pass
        rutactual = QgsProject.instance().homePath() #ruta actual
        carpeta=os.path.join(rutactual,'ACB-CAPAS/ACB_DEM_PDAL/')
        archivos=os.listdir(carpeta)
        for archivo in archivos: #borra todos los archivos en la carpeta
            rutafull=os.path.join(carpeta,archivo)
            os.remove(rutafull)
        QgsProject.instance().write() #guarda el proyecto
    def cambialetra(self,tipoletra,colorletra,tamaño):
        # Cambiando el tamaño de la fuente y el color del QLabel lbproceso3
        font = QFont(tipoletra, tamaño)  # Estableciendo la fuente y tamaño
        color = QColor(colorletra)  # Estableciendo el color del texto
        self.lbproceso3.setFont(font)
        self.lbproceso3.setStyleSheet("color: {}".format(color.name()))  # Aplicando el color

