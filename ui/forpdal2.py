# -*- coding: utf-8 -*-
#las librerias se importan a python en la consola osgeo4w shell
#teclenado python3 -m pip install pdal o cualquier otra libreria

#                Ayuda de PDAL
# https://pdal.io/en/2.6.0/tutorial/index.html
#rangos filtro https://pdal.io/en/2.6.0/stages/filters.range.html#ranges
#https://pdal.io/en/2.7.1/stages/filters.html#ground-unclassified
#https://pdal.io/en/2.7.1/pipeline.html#dtm

#    forpdal2.py     PDAL MODELO DIGITAL DE ELEVACIONES

from PyQt5.QtWidgets import QDialog
from qgis.PyQt import uic
from PyQt5.QtGui import QFont, QColor
import os
import json
import processing
import subprocess
import time
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsProject,QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem,QgsExpressionContextUtils


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "forpdal2.ui"))

class FormularioPdal2(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(FormularioPdal2, self).__init__(parent)
        self.setupUi(self)
        self.pbpdal2.mousePressEvent = self.jsonarchivo2
        self.pbcierra.clicked.connect(self.cierraformulario)
        self.pbpdal2.show() #muestra el boton pbpdal2
        self.pbcierra.hide() #oculta el boton cierra
        self.lbproceso2.hide()

        # inicializa el directorio del plugin
        self.plugin_dir = os.path.dirname(__file__)
        global malla,radio,tipo_salida, pdalconsola2, contador, ejecutable,crs
        crs = QgsProject.instance().crs()
        malla=2
        self.qlemalla.setText(str(malla))
        radio=max(50,malla+4)
        self.qleradio.setText(str(radio))
        tipo_salida="idw" #Algoritmo idw  Shepard’s inverse distance weighting omito la media mean
        self.cmbcalculo.currentText=tipo_salida
        self.qlelidar.setText("NUBE_PDAL_DSM.laz")
        self.qleraster2.setText("DSM_PDAL.tif")
        self.qlecrs.setText("25830")

        # Muestra el mensaje
        titulo = "Ejecución archivo json y Creación archivos tif y laz"
        cuerpo1 = "Fusión de nubes laz, Clasificación \nEliminación de Ruido, Creación Ráster DSM "
        cuerpo2 = "Archivo " + self.qlelidar.text() + " " + self.qleraster2.text()
        self.lbproceso.setText(titulo)
        self.lbproceso1.setText(cuerpo1)
        self.lbproceso2.setText(cuerpo2)
        # INCORPORA LAS VARIABLES DE USUARIO GUARDADAS EN EL PROYECTO AL ARRANCAR
        # Carga en los objetos Qtdesigner el valor de la variable
        self.project = QgsProject.instance()
        # ejecutable cloudcompare
        proj_variables = QgsExpressionContextUtils.projectScope(self.project)  # llamada a todas las variables del proyecto
        ejecutable = str(proj_variables.variable('acbejecutable'))  # llamada a la variable 'acbtitulo' en formato cadena
    def jsonarchivo2(self,event):
        #barraprogreso
        self.barra.show=True;contador=0
        self.barraprogreso(15, 0, "☻ Declaración de rutas")
        self.elimina(event)     #elimina previamente todos los archivos previos
        # Rutas
        global rutactual2, rutapdal2, rutamascara2, rutaraster2, rutalidar2, rutaraster2delimitado, rutaraster2fill,rutahillshade2,rutapseudocolor,rutacloud,rutacloud1,rutacloud2
        rutactual2 = QgsProject.instance().homePath() #ruta actual
        rutapdal2 = (os.path.join(rutactual2, 'ACB-DATOS'))                                       #ruta del json
        rutamascara2 = (os.path.join(rutactual2, 'ACB-CAPAS', "MASCARA.gpkg"))                    #ruta de la máscara
        rutaraster2fill = (os.path.join(rutactual2, 'ACB-CAPAS/ACB_DSM_PDAL/', "DSM_PDAL_FILL.tif"))  # ruta del raster relleno
        rutahillshade2 = (os.path.join(rutactual2, 'ACB-CAPAS/ACB_DSM_PDAL/', "DSM_PDAL_HILLSHADE.tif"))  # ruta del raster hillshade
        rutaraster2delimitado = (os.path.join(rutactual2, 'ACB-CAPAS/ACB_DSM_PDAL/', "DSM_PDAL_RECOR.tif"))  #ruta del raster recortado
        rutaraster2 = (os.path.join(rutactual2, 'ACB-CAPAS/ACB_DSM_PDAL/', str(self.qleraster2.text())))# "DSM_PDAL.tif"
        rutalidar2 = (os.path.join(rutactual2, 'ACB-CAPAS/ACB_DSM_PDAL/', str(self.qlelidar.text()))) #"NUBE_PDAL_DSM.laz"
        rutacloud = (os.path.join(rutactual2, 'ACB-CAPAS/ACB_NUBES/',str(self.qlelidar.text())))#"NUBE_PDAL_DSM.laz"
        rutacloud2 = (os.path.join(rutactual2, 'ACB-CAPAS/ACB_NUBES/VEGETACION_PDAL.laz'))

        #barraprogreso
        self.barraprogreso(25, 15, "☺ Creación del archivo json")
        os.chdir(rutapdal2) #cambia de directorio en la consola para crear el json en rutapdal2
        malla=float(self.qlemalla.text())
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
        filename = rutapdal2+"acb_pdal2.json"

        #MODELO DIGITAL SUPERFICIE COMPLETO
        # Abre NUBE.laz
        self.barraprogreso(30, 25, "☺ Abre NUBE.laz")
        acb_pdal = {}
        acb_pdal["pipeline"]=listanubes #está leyendo NUBE.laz

        # Filtros outlier y elm
        self.barraprogreso(40, 30, "☺ Filtros outlier y elm")
        if self.chb1.isChecked():
            acb_pdal["pipeline"].append({"type": "filters.outlier"}) #filtro de valores atípicos pasando a 7 ruido
        else: pass
        if self.chb2.isChecked():
            acb_pdal["pipeline"].append({"type": "filters.elm"}) #puntos bajos pasan a clasificación 7 ruido
        else: pass

        # Clasifica por cota >0 y excluye 7 ruido
        self.barraprogreso(45, 40, "☺ Clasifica por cota entre 0m y 8850m excluyendo ruido")
        acb_pdal["pipeline"].append({"type": "filters.range","limits": "Z[0:8850]","limits": "Classification![7:7]"}) #limita ptos cota entre el nivel del mar y el Everest y excluye ruido 7

        # Guarda la nube procesada y crea un ráster para el MDS
        self.barraprogreso(50, 45, "☺ Genera ráster y archivo.laz DSM_PDAL")
        acb_pdal["pipeline"].append({"type": "writers.las","compression": "true","minor_version": "2","dataformat_id": "3","filename": "../ACB-CAPAS/ACB_NUBES/"+self.qlelidar.text()})
        acb_pdal["pipeline"].append({"filename": "../ACB-CAPAS/ACB_DSM_PDAL/"+self.qleraster2.text(),"gdaldriver": "GTiff","resolution": malla,"radius": radio,"output_type": tipo_salida,"type": "writers.gdal"})

        # VEGETACION Genera la nube VEGETACION_PDAL.laz y el ráster VEGETACIÓN
        self.barraprogreso(60, 50, "☺ Genera ráster VEGETACIÓN y la nube VEGETACION_PDAL.laz")
        acb_pdal["pipeline"].append({"type": "filters.range","limits": "Z[0:8850]", "limits": "Classification[3:5]"})
        acb_pdal["pipeline"].append({"type": "writers.las", "compression": "true", "minor_version": "2", "dataformat_id": "3","filename": "../ACB-CAPAS/ACB_NUBES/VEGETACION_PDAL.laz"})
        acb_pdal["pipeline"].append({"filename": "../ACB-CAPAS/ACB_DSM_PDAL/VEGETACION_PDAL.tif", "gdaldriver": "GTiff", "resolution": malla,"radius": radio, "output_type": tipo_salida, "type": "writers.gdal"})

        # Orden en consola para ejecutar el archivo json con pdal
        with open('acb_pdal2.json','w') as file:
            json.dump(acb_pdal,file,indent=4)
        self.barraprogreso(80, 70, "☻ Ejecución en consola del archivo json")
        pdalconsola2=f'pdal pipeline acb_pdal2.json'
        # Ejecutar el comando pdalconsola2 en la ruta definida como rutapdal2
        subprocess.run(pdalconsola2, cwd=rutapdal2, shell=True) #ejecuta cambio directorio y el pdalconsola2

        #RELLENA RASTER
        self.barraprogreso(90, 80, "☻ Rellena huecos en el ráster")
        self.rellenaraster(event)    # llamada a la funcion rellena el raster elimina valores nulos

        #RECORTA CONTRA MASCARA ANULADO
        #self.recortaraster(event)

        #CARGA EL RASTER EN QGIS DSM
        self.barraprogreso(95, 90, "☺ Carga el ráster en Qgis")
        self.cargaraster(event)      # llamada a la funcion que carga el raster

        #GENERA Y CARGA EL HILLSHADE
        self.barraprogreso(98, 95, "☻ Genera el ráster de fondo Hillshade")
        self.hillshade(event)  # llamada a la funcion que creará y cargará un hillshade
        self.cargaraster2(event)

        #PROCESO FINAL
        self.lbproceso1.setText("Fin DEM PDAL")
        self.lbproceso.setText("Proceso pdal DEM LIDAR Terminado")
        self.lbproceso1.setText("NUBE LIDAR y Ráster DEM "+str(malla)+"x"+str(malla)+tipo_salida+"\n Rectificado y Recortado")
        self.barraprogreso(101, 98, "☺ Carga el ráster en Qgis")
        self.pbpdal2.hide()
        self.pbcierra.show()
        self.lbproceso3.setText("Proceso pdal DES LIDAR Terminado\n\nSe genera en todas las nubes un escalar Coord Z\n Se abrirá CloudCompare con la Nube\n Apply All  Yes All")
        self.cambialetra("Arial Black", "blue",10)  # llama a la funcionpara cambiar tipo letra, color y tamaño del QLabel
        QMessageBox.information(None, "Fin del Proceso Pdal",
                                "Se genera en todas las nubes un escalar Coord Z\nSe abrirá CloudCompare con \nTodas las Nubes disponibles\n Clickea Apply All\n  Yes All")
        self.close()

    def cierraformulario(self,event):
        self.close()
    def rellenaraster(self,event):
        processing.run("gdal:fillnodata", {
            'INPUT':"../ACB-CAPAS/ACB_DSM_PDAL/" + self.qleraster2.text(),# "DSM_PDAL.tif"
            'BAND': 1, 'DISTANCE': 50, 'ITERATIONS': 0, 'NO_MASK': False, 'MASK_LAYER': None, 'OPTIONS': '',
            #'EXTRA': QgsCoordinateReferenceSystem('EPSG:'+self.qlecrs.text()), #atención asigna extra crs
            #'EXTRA': crs.postgisSrid(),  # atención asigna extra crs
            'OUTPUT':"../ACB-CAPAS/ACB_DSM_PDAL/DSM_PDAL_FILL.tif"})



    def recortaraster(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutamascara = (os.path.join(rutactual, 'ACB-CAPAS', "MASCARA.gpkg"))
        processing.run("gdal:cliprasterbymasklayer",
                       {'INPUT': "../ACB-CAPAS/ACB_DSM_PDAL/DSM_PDAL_FILL.tif", 'MASK': rutamascara,
                        'SOURCE_CRS': crs, 'TARGET_CRS': crs, 'TARGET_EXTENT': None, 'NODATA': 255,
                        'ALPHA_BAND': False, 'CROP_TO_CUTLINE': True, 'KEEP_RESOLUTION': False, 'SET_RESOLUTION': False,
                        'X_RESOLUTION': None, 'Y_RESOLUTION': None, 'MULTITHREADING': False, 'OPTIONS': '',
                        'DATA_TYPE': 0,
                        'EXTRA': '',
                        'OUTPUT': "../ACB-CAPAS/ACB_DSM_PDAL/DSM_PDAL_FILL.tif"})

    def cargaraster(self,event):
        # Agrega la capa rutaraster2fill ya recorado y rellenada celdas sin valor
        rutaraster2fill = "../ACB-CAPAS/ACB_DSM_PDAL/DSM_PDAL_FILL.tif"
        caparaster=QgsRasterLayer(rutaraster2fill,self.qleraster2.text())# "DSM_PDAL.tif"
        #src = QgsCoordinateReferenceSystem(int(self.qlecrs.text()), QgsCoordinateReferenceSystem.EpsgCrsId) #define el src
        #caparaster.setCrs(src)  #asigna el src a la capa
        QgsProject.instance().addMapLayer(caparaster,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('DSM_PDAL')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, caparaster)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas
    def hillshade(self,event):
        rutaraster2fill = "../ACB-CAPAS/ACB_DSM_PDAL/DSM_PDAL_FILL.tif"
        processing.run("gdal:hillshade", {
            'INPUT': rutaraster2fill,
            'BAND': 1, 'Z_FACTOR': 2, 'SCALE': 1, 'AZIMUTH': 225, 'ALTITUDE': 45, 'COMPUTE_EDGES': False,
            'ZEVENBERGEN': True, 'COMBINED': False, 'MULTIDIRECTIONAL': True,
            'OPTIONS': 'COMPRESS=DEFLATE|PREDICTOR=2|ZLEVEL=9',
            #'EXTRA': QgsCoordinateReferenceSystem('EPSG:'+self.qlecrs.text()), #atención asigna extra crs
            #'EXTRA': crs.postgisSrid(),  # atención asigna extra crs
            'OUTPUT': rutahillshade2})
        # Agrega la capa rutahillshade2
        caparaster=QgsRasterLayer(rutahillshade2,'DSM_PDAL_HILLSHADE.tif')
        QgsProject.instance().addMapLayer(caparaster,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('DSM_PDAL')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, caparaster)               #inserta la capa raster al final del grupo
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
    def cargaraster2(self,event):
        # Agrega la capa rutaraster2fill ya recorado y rellenada celdas sin valor
        rutavegetacion = "../ACB-CAPAS/ACB_DSM_PDAL/VEGETACION_PDAL.tif"
        caparaster=QgsRasterLayer(rutavegetacion,"VEGETACION_PDAL")
        #src = QgsCoordinateReferenceSystem(int(self.qlecrs.text()), QgsCoordinateReferenceSystem.EpsgCrsId) #define el src
        #caparaster.setCrs(src)  #asigna el src a la capa
        QgsProject.instance().addMapLayer(caparaster,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('VEGETACION')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, caparaster)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas

    def elimina(self,event):
        proyecto = QgsProject.instance()
        nombre_subgrupo = "DSM_PDAL"
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

    def cambialetra(self,tipoletra,colorletra,tamaño):
        # Cambiando el tamaño de la fuente y el color del QLabel lbproceso3
        font = QFont(tipoletra, tamaño)  # Estableciendo la fuente y tamaño
        color = QColor(colorletra)  # Estableciendo el color del texto
        self.lbproceso3.setFont(font)
        self.lbproceso3.setStyleSheet("color: {}".format(color.name()))  # Aplicando el color


