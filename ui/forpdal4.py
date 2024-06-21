# -*- coding: utf-8 -*-
#las librerias se importan a python en la consola osgeo4w shell
#teclenado python3 -m pip install pdal o cualquier otra libreria

#    forcc4.py     CLOUDCOMPARE MODELO DIGITAL DE V E G E T A C I O N
# Ayuda de CloudCompare: https://www.cloudcompare.org/doc/wiki/index.php/Command_line_mode

import pathlib
from pathlib import Path, PureWindowsPath, PurePath
from PyQt5.QtWidgets import QDialog,QLabel, QApplication
from qgis.PyQt import uic
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
import os
import time
import json
import processing
from PyQt5.QtGui import QFont, QColor
import subprocess
from qgis.utils import iface
from qgis.core import QgsProject, QgsRasterLayer, QgsCoordinateReferenceSystem,QgsExpressionContextUtils
from qgis.PyQt.QtWidgets import QMessageBox


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "forpdal4.ui"))

class FormularioPdal4(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(FormularioPdal4, self).__init__(parent)
        self.setupUi(self)

        self.btnccomp.mousePressEvent = self.jsonarchivo3


        self.pbcierra.clicked.connect(self.cierraformulario)
        self.btnccomp.show() #muestra el boton pbpdal
        self.pbcierra.hide() #oculta el boton cierra

        global malla,radio,tipo_salida, pdalconsola

        malla=2
        self.qlemalla.setText(str(malla))
        radio=malla+1
        self.qleradio.setText(str(radio))
        tipo_salida="INTERP"
        self.cmbcalculo.currentText=tipo_salida
        self.qlelidar.setText("TERyVEG_PDAL.laz")
        self.qleraster2.setText("VEGETACION_PDAL.tif")
        self.qlecrs.setText("25830")


        # Muestra el mensaje
        QMessageBox.information(None,"Aviso","Se precisa paso previo por DSM PDAL")
        titulo = "\nEn proceso \nCreación archivos  RASTER .tif y Nube .laz"
        cuerpo1 = "Fusión de nubes laz, Clasificación\nEliminación de Ruido, Creación Ráster"
        cuerpo2 = "Archivo " + self.qlelidar.text() + " " + self.qleraster2.text() #"VEGETACION_PDAL.tif"
        self.lbproceso.setText(titulo)
        self.lbproceso1.setText(cuerpo1)
        self.lbproceso2.setText(cuerpo2)

    def calculaveg(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutaA = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_PDAL/',"VEGyTER_PDAL.tif"))# ruta del raster VEGETACION Y TERRENO
        rutaB = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_PDAL/',"DEM_PDAL_FILL.tif"))  # ruta del raster TERRENO

        rutaC = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_PDAL/',"VEGbyALTURA_PDAL.tif"))
        capaC = QgsRasterLayer(rutaC, "VEGbyALTURA_PDAL")
        rutaD = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_PDAL/', "VEG_0a1_PDAL.tif"))
        capaD = QgsRasterLayer(rutaD, "VEG_0a1_PDAL")
        rutaE = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_PDAL/', "VEG_1a4_PDAL.tif"))
        capaE = QgsRasterLayer(rutaE, "VEG_1a4_PDAL")
        rutaF = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_PDAL/', "VEG_4a20_PDAL.tif"))
        capaF = QgsRasterLayer(rutaF, "VEG_4a20_PDAL")
        rutaG = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_PDAL/', "VEG_MAS20_PDAL.tif"))
        capaG = QgsRasterLayer(rutaG, "VEG_MAS20_PDAL")


        entradas=[]
        capa1 = QgsRasterLayer(rutaA,"VEGyTER_PDAL.tif@1")
        capa2 = QgsRasterLayer(rutaB,"DEM_PDAL.tif@1")

        rutas = [capaG,capaF,capaE,capaD,capaC]

        ras = QgsRasterCalculatorEntry()
        ras1=capa1.name()
        ras.ref=capa1.name()
        ras.raster=capa1
        ras.bandNumber = 1
        entradas.append(ras)

        ras = QgsRasterCalculatorEntry()
        ras.ref=capa2.name()
        ras2 = capa2.name()
        ras.raster=capa2
        ras.bandNumber = 1
        entradas.append(ras)

        #con esta expresión se calcula la diferencia de altura solo cuando sea mayor que 0 rutaC
        calc=QgsRasterCalculator(f"({ras1} - {ras2} > 0) * ({ras1} - {ras2}) ", rutaC,'GTiff', capa1.extent(), capa1.width(), capa1.height(), entradas)
        calc.processCalculation()
        #con esta expresión se calcula la diferencia de altura solo cuando las alturas esten entre 0 y 1m rutaD
        calc=QgsRasterCalculator(f"({ras1} - {ras2} > 0.3 and {ras1} - {ras2} <= 1) * ({ras1} - {ras2}) ", rutaD,'GTiff', capa1.extent(), capa1.width(), capa1.height(), entradas)
        calc.processCalculation()
        #con esta expresión se calcula la diferencia de altura solo cuando las alturas esten entre 1 y 4m rutaE
        calc=QgsRasterCalculator(f"({ras1} - {ras2} > 1 and {ras1} - {ras2} <= 4) * ({ras1} - {ras2}) ", rutaE,'GTiff', capa1.extent(), capa1.width(), capa1.height(), entradas)
        calc.processCalculation()
        #con esta expresión se calcula la diferencia de altura solo cuando las alturas esten entre 4 y 20m rutaF
        calc=QgsRasterCalculator(f"({ras1} - {ras2} > 4 and {ras1} - {ras2} <= 20) * ({ras1} - {ras2}) ", rutaF,'GTiff', capa1.extent(), capa1.width(), capa1.height(), entradas)
        calc.processCalculation()
        # con esta expresión se calcula la diferencia de altura solo cuando las alturas MAYORES QUE 20m rutaI
        calc = QgsRasterCalculator(f"({ras1} - {ras2} > 20) * ({ras1} - {ras2}) ", rutaG,'GTiff', capa1.extent(), capa1.width(), capa1.height(), entradas)
        calc.processCalculation()

        for ruta in rutas:
            #carga el raster resultado en el mapa ya clasificado por alturas contra terreno
            QgsProject.instance().addMapLayer(ruta,False) #aguanta la carga del raster
            root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
            grupomapa=root.findGroup('VEGETACION')           #localiza el grupo en el árbol
            grupomapa.insertLayer(0, ruta)               #inserta la capa raster al final del grupo
            iface.mapCanvas().refresh()                     # Refresca canvas

    def jsonarchivo3(self,event):
        #barraprogreso
        self.barra.show=True;contador=0
        self.barraprogreso(15, 0, "☻ Declaración de rutas")
        self.elimina(event)     #elimina previamente todos los archivos previos
        # Rutas
        global rutactual2, rutapdal2, rutaraster2,rutarasterfill2,crs
        rutactual2 = QgsProject.instance().homePath() #ruta actual
        rutapdal2 = (os.path.join(rutactual2, 'ACB-DATOS'))                               #ruta del json
        rutaraster2 = (os.path.join(rutactual2, 'ACB-CAPAS/ACB_DSM_PDAL/', str(self.qleraster2.text())))   #self.qleraster2.setText("VEGETACION_PDAL.tif")
        rutarasterfill2 = (os.path.join(rutactual2, 'ACB-CAPAS/ACB_DSM_PDAL/', "VEGyTER_PDAL.tif"))  # ruta del raster relleno
        rutacloud = (os.path.join(rutactual2, 'ACB-CAPAS/ACB_NUBES/',str(self.qlelidar.text())))

        self.barraprogreso(30, 15, "☺ Creación del archivo json")#barraprogreso
        os.chdir(rutapdal2) #cambia de directorio en la consola para crear el json en rutapdal2
        malla=float(self.qlemalla.text())

        crs = QgsProject.instance().crs()
        radio=malla+1
        tipo_salida=self.cmbcalculo.currentText

        self.barraprogreso(50, 30, "☺ Procesa Nube de puntos solo VEGETACION")
        self.vegpdal(event) #ejecuta pdal solo la nube de puntos VEGETACION
        self.vgyte(event) #ejecuta pdal para unir terreno y VEGETACION
        self.barraprogreso(60, 50, "☺ Genera ráster y archivo.laz EDF_PDAL")
        self.barraprogreso(70, 60, "☻ Ejecución en consola del archivo json")
        self.barraprogreso(80, 70, "☻ Rellena huecos del ráster DEM")
        self.barraprogreso(85, 80, "☺ Carga el ráster en Qgis")
        self.cargaraster(event)      # llamada a la funcion que carga el raster
        self.barraprogreso(95, 85, "☻ Genera el ráster de fondo Hillshade")
        self.barraprogreso(101, 95, "☺ Carga el ráster en Qgis")
        self.calculaveg(event) #calcula vegetacion por alturas calculadora raster contra terreno
        self.lbproceso1.setText("Fin PDAL")
        self.lbproceso.setText("Proceso pdal EDF LIDAR Terminado")
        self.lbproceso1.setText("NUBE LIDAR y Ráster EDF "+str(malla)+"x"+str(malla)+tipo_salida+"\n Rectificado y Recortado")
        self.btnccomp.hide()
        self.pbcierra.show()
        self.lbproceso3.setText("Proceso pdal VEG LIDAR Terminado\n Se abrirá CloudCompare con la Nube\n Apply All  Yes All")
        self.cambialetra("Arial Black","blue",10) #llama a la funcionpara cambiar tipo letra, color y tamaño del QLabel
        QMessageBox.information(None, "Fin del Proceso Pdal",
                                "Se genera en todas las nubes un escalar Coord Z\nSe abrirá CloudCompare con \nTodas las Nubes disponibles\n Clickea Apply All\n  Yes All")
        self.close()
    def cierraformulario(self,event):
        self.close()
    def cargaraster(self,event):
        caparaster=QgsRasterLayer(rutarasterfill2,"VEGyTER_PDAL.tif")
        #src = QgsCoordinateReferenceSystem(int(self.qlecrs.text()), QgsCoordinateReferenceSystem.EpsgCrsId) #define el src
        #caparaster.setCrs(src)  #asigna el src a la capa
        QgsProject.instance().addMapLayer(caparaster,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('VEGETACION')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, caparaster)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas

    def selecciona(self,event):
        # CREA LA LISTA CON LA RUTA RELATIVA ./NUBEPUNTOS/NOMBRE DE LA NUBE.laz o las
        global listanubes
        rutanube = "../ACB-CAPAS/ACB_NUBES/VEGETACION_PDAL.laz"
        listanubes=[]    # Lista para almacenar los nombres de archivos de puntos
        listanubes.append(rutanube)

    def selecciona2(self,event):
        # CREA LA LISTA CON LA RUTA RELATIVA ./NUBEPUNTOS/NOMBRE DE LA NUBE.laz o las
        global listanubes2
        ruta1= "../ACB-CAPAS/ACB_NUBES/NUBE_PDAL_DEM.laz"
        ruta2 = "../ACB-CAPAS/ACB_NUBES/VEGETACION_PDAL"
        listanubes2=[]    # Lista para almacenar los nombres de archivos de puntos
        listanubes2.append(ruta1)
        listanubes2.append(ruta2)
    def barraprogreso(self,tope,contador,mensaje):
        self.lbproceso1.setText(mensaje)
        while contador <= tope:
            time.sleep(0.2)
            self.barra.setValue(contador);contador += 1

    def elimina(self,event):
        nombre_subgrupo = "VEGETACION"
        proyecto = QgsProject.instance()
        subgrupo = proyecto.layerTreeRoot().findGroup(nombre_subgrupo)
        if subgrupo is not None: #si el grupo existe
            capas_subgrupo = subgrupo.children()            # Obtener una lista de todas las capas dentro del subgrupo
            for capa in capas_subgrupo:            # Eliminar cada capa del subgrupo
                proyecto.removeMapLayer(capa.layer())
        else:
            pass

    def vegpdal(self,event):
        # VEGETACION
        self.selecciona(event)
        filename = rutapdal2 + "acb_pdal5.json"
        acb_pdal = {}
        acb_pdal["pipeline"]=listanubes
        acb_pdal["pipeline"].append({"filename": "../ACB-CAPAS/ACB_DSM_PDAL/VEG_PDAL.tif", "gdaldriver": "GTiff", "resolution": malla,"radius": radio, "output_type": tipo_salida, "type": "writers.gdal"})
        with open('acb_pdal5.json','w') as file:
            json.dump(acb_pdal,file,indent=4)
        pdalconsola5=f'pdal pipeline acb_pdal5.json'        # Orden en consola para ejecutar el archivo json con pdal
        subprocess.run(pdalconsola5, cwd=rutapdal2, shell=True) #ejecuta cambio directorio y el pdalconsola3

    def vgyte(self,event):
        # VEGETACIONyTERRENO
        self.selecciona2(event)  # llama a la funcion selecciona para seleccionar la nube de puntos
        filename = rutapdal2 + "acb_pdal6.json"
        acb_pdal = {}
        acb_pdal["pipeline"] = listanubes2

        acb_pdal["pipeline"].append({"type": "filters.merge"})
        acb_pdal["pipeline"].append({"type": "writers.las", "compression": "true", "minor_version": "2","dataformat_id": "3", "filename": "../ACB-CAPAS/ACB_NUBES/" + self.qlelidar.text()})
        acb_pdal["pipeline"].append({"filename": "../ACB-CAPAS/ACB_DSM_PDAL/" + self.qleraster2.text(), "gdaldriver": "GTiff","resolution": malla, "radius": radio, "output_type": tipo_salida, "type": "writers.gdal"})
        with open('acb_pdal6.json', 'w') as file:
            json.dump(acb_pdal, file, indent=4)
        pdalconsola6 = f'pdal pipeline acb_pdal6.json'  # Orden en consola para ejecutar el archivo json con pdal
        subprocess.run(pdalconsola6, cwd=rutapdal2, shell=True)  # ejecuta cambio directorio y el pdalconsola4

    def cambialetra(self,tipoletra,colorletra,tamaño):
        # Cambiando el tamaño de la fuente y el color del QLabel lbproceso3
        font = QFont(tipoletra, tamaño)  # Estableciendo la fuente y tamaño
        color = QColor(colorletra)  # Estableciendo el color del texto
        self.lbproceso3.setFont(font)
        self.lbproceso3.setStyleSheet("color: {}".format(color.name()))  # Aplicando el color