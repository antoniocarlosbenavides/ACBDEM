# -*- coding: utf-8 -*-
#las librerias se importan a python en la consola osgeo4w shell
#teclenado python3 -m pip install pdal o cualquier otra libreria
#    forpdal3.py     PDAL MODELO DIGITAL DE EDIFICIOS

from PyQt5.QtWidgets import QDialog,QMessageBox
from qgis.PyQt import uic
import os
from PyQt5.QtGui import QFont, QColor
import processing
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
import json
import subprocess
import time
from qgis.utils import iface
from qgis.core import QgsProject, QgsRasterLayer, QgsCoordinateReferenceSystem,QgsExpressionContextUtils


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "forpdal3.ui"))

class FormularioPdal3(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(FormularioPdal3, self).__init__(parent)
        self.setupUi(self)
        self.pbpdal3.mousePressEvent = self.jsonarchivo3
        self.pbcierra.clicked.connect(self.cierraformulario)
        self.pbpdal3.show() #muestra el boton pbpdal3
        self.pbcierra.hide() #oculta el boton cierra
        self.lbproceso2.hide()

        # inicializa el directorio del plugin
        self.plugin_dir = os.path.dirname(__file__)

        global malla,radio,tipo_salida, pdalconsola3,pdalconsola4, contador, ejecutable

        malla=2
        self.qlemalla.setText(str(malla))
        radio=malla+1
        self.qleradio.setText(str(radio))
        tipo_salida="idw"
        self.cmbcalculo.currentText=tipo_salida
        self.qlelidar.setText("NUBE_PDAL_EDF.laz")
        self.qleraster2.setText("EDIFICIOS_PDAL.tif")
        self.qlecrs.setText("25830")

        # Muestra el mensaje
        titulo = "Ejecución archivo json y Creación archivos tif y laz"
        cuerpo1 = "Fusión de nubes laz, Clasificación \nEliminación de Ruido, Creación Ráster "
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
    def jsonarchivo3(self,event):
        #barraprogreso
        self.barra.show=True;contador=0
        self.barraprogreso(15, 0, "☻ Declaración de rutas")
        self.elimina(event)     #elimina previamente todos los archivos previos
        # Rutas
        global rutactual2, rutapdal2, rutaraster2,rutarasterfill2,crs
        rutactual2 = QgsProject.instance().homePath() #ruta actual
        rutapdal2 = (os.path.join(rutactual2, 'ACB-DATOS'))                               #ruta del json
        rutaraster2 = (os.path.join(rutactual2, 'ACB-CAPAS/ACB_DSM_PDAL/', str(self.qleraster2.text())))   #self.qleraster2.setText("EDIFICIOS_PDAL.tif")
        rutarasterfill2 = (os.path.join(rutactual2, 'ACB-CAPAS/ACB_DSM_PDAL/', "EDFyTER_PDAL.tif"))  # ruta del raster relleno
        rutacloud = (os.path.join(rutactual2, 'ACB-CAPAS/ACB_NUBES/',str(self.qlelidar.text())))

        self.barraprogreso(30, 15, "☺ Creación del archivo json")#barraprogreso
        os.chdir(rutapdal2) #cambia de directorio en la consola para crear el json en rutapdal2

        crs = QgsProject.instance().crs()
        malla=float(self.qlemalla.text())
        radio=malla+1
        tipo_salida=self.cmbcalculo.currentText

        self.edifpdal(event) #ejecuta pdal solo la nube de puntos EDIFICIOS
        self.barraprogreso(60, 30, "☺ Genera ráster y archivo.laz EDF_PDAL")
        self.barraprogreso(70, 60, "☻ Ejecución en consola del archivo json")
        self.edyte(event) #ejecuta pdal para unir terreno y edificios
        self.barraprogreso(80, 70, "☻ Rellena huecos del ráster DEM")
        self.barraprogreso(90, 80, "☺ Carga el ráster en Qgis")
        self.cargaraster(event)      # llamada a la funcion que carga el raster
        self.barraprogreso(98, 90, "☻ Genera el ráster de fondo Hillshade")
        self.barraprogreso(101, 98, "☺ Crea Nube de puntos solo Edificios")
        self.calculaedif(event)  # función que clasifica edificios por altura con la calculadora raster
        self.lbproceso1.setText("Fin PDAL")
        self.lbproceso.setText("Proceso pdal EDF LIDAR Terminado")
        self.lbproceso1.setText("NUBE LIDAR y Ráster EDF "+str(malla)+"x"+str(malla)+tipo_salida+"\n Rectificado y Recortado")
        self.pbpdal3.hide()
        self.pbcierra.show()
        self.lbproceso3.setText(
            "Proceso pdal EDF LIDAR Terminado\n Se abrirá CloudCompare con la Nube\n Apply All  Yes All")
        self.cambialetra("Arial Black", "blue",
                         10)  # llama a la funcionpara cambiar tipo letra, color y tamaño del QLabel
        QMessageBox.information(None, "Fin del Proceso Pdal",
                                "Se genera en todas las nubes un escalar Coord Z\nSe abrirá CloudCompare con \nTodas las Nubes disponibles\n Clickea Apply All\n  Yes All")
        self.close()
    def cierraformulario(self,event):
        self.close()
    def cargaraster(self,event):
        caparaster=QgsRasterLayer(rutarasterfill2,"EDFyTER_PDAL.tif")
        #src = QgsCoordinateReferenceSystem(int(self.qlecrs.text()), QgsCoordinateReferenceSystem.EpsgCrsId) #define el src
        #caparaster.setCrs(src)  #asigna el src a la capa
        QgsProject.instance().addMapLayer(caparaster,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('EDIFICIOS')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, caparaster)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas

    def selecciona(self,event):
        # CREA LA LISTA CON LA RUTA RELATIVA ./NUBEPUNTOS/NOMBRE DE LA NUBE.laz o las
        global listanubes
        rutanube = "../ACB-CAPAS/ACB_NUBES/NUBE.laz"
        listanubes=[]    # Lista para almacenar los nombres de archivos de puntos
        listanubes.append(rutanube)

    def selecciona2(self,event):
        # CREA LA LISTA CON LA RUTA RELATIVA ./NUBEPUNTOS/NOMBRE DE LA NUBE.laz o las
        global listanubes2
        ruta1= "../ACB-CAPAS/ACB_NUBES/NUBE_PDAL_DEM.laz"
        ruta2 = "../ACB-CAPAS/ACB_NUBES/EDIF_PDAL.laz"
        listanubes2=[]    # Lista para almacenar los nombres de archivos de puntos
        listanubes2.append(ruta1)
        listanubes2.append(ruta2)
    def barraprogreso(self,tope,contador,mensaje):
        self.lbproceso1.setText(mensaje)
        while contador <= tope:
            time.sleep(0.2)
            self.barra.setValue(contador);contador += 1

    def elimina(self,event):
        nombre_subgrupo = "EDIFICIOS"
        proyecto = QgsProject.instance()
        subgrupo = proyecto.layerTreeRoot().findGroup(nombre_subgrupo)
        if subgrupo is not None: #si el grupo existe
            capas_subgrupo = subgrupo.children()            # Obtener una lista de todas las capas dentro del subgrupo
            for capa in capas_subgrupo:            # Eliminar cada capa del subgrupo
                proyecto.removeMapLayer(capa.layer())
        else:
            pass

    def edifpdal(self,event):
        # EDIFICIOS
        self.selecciona(event)
        filename = rutapdal2 + "acb_pdal3.json"
        acb_pdal = {}
        acb_pdal["pipeline"]=listanubes
        acb_pdal["pipeline"].append({"type": "filters.outlier"}) #filtro de valores atípicos pasando a 7 ruido
        acb_pdal["pipeline"].append({"type": "filters.elm"}) #puntos bajos pasan a clasificación 7 ruido
        acb_pdal["pipeline"].append({"type": "filters.range","limits": "Z[0:8850]","limits": "Classification[6:6]"})
        acb_pdal["pipeline"].append({"type": "writers.las", "compression": "true", "minor_version": "2", "dataformat_id": "3","filename": "../ACB-CAPAS/ACB_NUBES/EDIF_PDAL.laz"})
        acb_pdal["pipeline"].append({"filename": "../ACB-CAPAS/ACB_DSM_PDAL/EDIF_PDAL.tif", "gdaldriver": "GTiff", "resolution": malla,"radius": radio, "output_type": tipo_salida, "type": "writers.gdal"})
        with open('acb_pdal3.json','w') as file:
            json.dump(acb_pdal,file,indent=4)
        pdalconsola3=f'pdal pipeline acb_pdal3.json'        # Orden en consola para ejecutar el archivo json con pdal
        subprocess.run(pdalconsola3, cwd=rutapdal2, shell=True) #ejecuta cambio directorio y el pdalconsola3

    def calculaedif(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutaA = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_PDAL/',"EDFyTER_PDAL.tif"))  # ruta del raster TERRENO Y EDIFICIOS
        rutaB = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_PDAL/',"DEM_PDAL_FILL.tif"))  # ruta del raster TERRENO
        rutaC = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_PDAL/',"EDIFICIOSbyALTURA_PDAL.tif"))

        entradas=[]
        capa1 = QgsRasterLayer(rutaA, "EDFyTER_PDAL.tif@1")
        capa2 = QgsRasterLayer(rutaB,"DEM_PDAL.tif@1")
        capa3 = QgsRasterLayer(rutaC,"EDIFICIOSbyALTURA_PDAL")
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

        calc=QgsRasterCalculator(f"({ras1} - {ras2} > 1) * ({ras1} - {ras2}) ", rutaC,'GTiff', capa1.extent(), capa1.width(), capa1.height(), entradas)
        #con esta expresión se calcula la diferencia de altura solo cuando sea mayor que 1m
        calc.processCalculation()

        #carga el raster resultado EDIFICIOSbyALTURA en el mapa ya clasificado por alturas contra terreno
        QgsProject.instance().addMapLayer(capa3,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('EDIFICIOS')           #localiza el grupo en el árbol
        grupomapa.insertLayer(0, capa3)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas


    def edyte(self,event):
        # EDIFICIOSyTERRENO
        self.selecciona2(event)  # llama a la funcion selecciona para seleccionar la nube de puntos
        filename = rutapdal2 + "acb_pdal4.json"
        acb_pdal = {}
        acb_pdal["pipeline"] = listanubes2
        acb_pdal["pipeline"].append({"type": "filters.merge"})
        acb_pdal["pipeline"].append({"type": "writers.las", "compression": "true", "minor_version": "2","dataformat_id": "3", "filename": "../ACB-CAPAS/ACB_NUBES/" + self.qlelidar.text()})
        acb_pdal["pipeline"].append({"filename": "../ACB-CAPAS/ACB_DSM_PDAL/" + self.qleraster2.text(), "gdaldriver": "GTiff","resolution": malla, "radius": radio, "output_type": tipo_salida, "type": "writers.gdal"})
        with open('acb_pdal4.json', 'w') as file:
            json.dump(acb_pdal, file, indent=4)
        pdalconsola4 = f'pdal pipeline acb_pdal4.json'  # Orden en consola para ejecutar el archivo json con pdal
        subprocess.run(pdalconsola4, cwd=rutapdal2, shell=True)  # ejecuta cambio directorio y el pdalconsola4

    def cambialetra(self,tipoletra,colorletra,tamaño):
        # Cambiando el tamaño de la fuente y el color del QLabel lbproceso3
        font = QFont(tipoletra, tamaño)  # Estableciendo la fuente y tamaño
        color = QColor(colorletra)  # Estableciendo el color del texto
        self.lbproceso3.setFont(font)
        self.lbproceso3.setStyleSheet("color: {}".format(color.name()))  # Aplicando el color