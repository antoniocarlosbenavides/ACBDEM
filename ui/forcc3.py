# -*- coding: utf-8 -*-
#las librerias se importan a python en la consola osgeo4w shell
#teclenado python3 -m pip install pdal o cualquier otra libreria
#apoyo para calculadora raster en python
#https://gis.stackexchange.com/questions/385016/qgis-python-raster-calculator

#    forcc3.py     CLOUDCOMPARE MODELO DIGITAL DE EDIFICIOS

import pathlib
from pathlib import Path, PureWindowsPath, PurePath

from PyQt5.QtWidgets import QDialog,QLabel, QApplication
from qgis.PyQt import uic
import os
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
import processing
import subprocess

from qgis.utils import iface
from qgis.core import Qgis,QgsProject,QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem,QgsExpressionContextUtils, QgsHillshadeRenderer
from qgis.PyQt.QtWidgets import QMessageBox


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "forcc3.ui"))

class FormularioCloudComp3(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(FormularioCloudComp3, self).__init__(parent)
        self.setupUi(self)

        self.btnccomp.mousePressEvent = self.malladtm

        self.pbcierra.clicked.connect(self.cierraformulario)
        self.btnccomp.show() #muestra el boton pbpdal
        self.pbcierra.hide() #oculta el boton cierra
        self.pbrutacc.mousePressEvent = self.localizacc
        global malla,radio,tipo_salida, pdalconsola,ejecutable,rutacloudcompare,rutanube,crs

        crs = QgsProject.instance().crs()
        self.qlecrs.setText(format(crs.postgisSrid()))
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
        radio=malla+4
        self.qleradio.setText(str(radio))
        tipo_salida="INTERP"
        self.cmbcalculo.currentText=tipo_salida
        self.qlelidar.setText("TERRENO_EDIFICIOS.laz")
        self.qleraster2.setText("TERRENO_EDIFICIOS.tif")
        self.qlecrs.setText("25830")
        self.qlemalla.textChanged.connect(self.actualiza)   #cuando el texto de malla cambie se actualiza el formulario

        # Muestra el mensaje
        QMessageBox.information(None,"Aviso","Se precisa paso previo por DSM CLOUD COMPARE")
        titulo = "\nEn proceso pocos minutos\nCreación archivos  DEM y LAZ"
        cuerpo1 = "Fusión de nubes laz, Clasificación\nEliminación de Ruido, Creación Ráster DEM\n Creación de Malla"
        cuerpo2 = "Archivo " + self.qlelidar.text() + " " + self.qleraster2.text()
        self.lbproceso.setText(titulo)
        self.lbproceso1.setText(cuerpo1)
        self.lbproceso2.setText(cuerpo2)


    def actualiza(self,event):
        radio=float(self.qlemalla.text())+1 #toma el valor flotante del texto en label qlemalla y añade 1
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

        rutanube2 =rutanube+"/EDFNUBEUNIDA.laz"
        rutanube3 =rutanube+"/EDFNUBEUNIDAREC.laz"

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
        grupomapa=root.findGroup('EDIFICIOS_CCOMP')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, capapuntos)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas

    def eliminasuperados(self,event):
        try:
            os.remove(rutaraster)
        except FileNotFoundError:
            pass
        try:
            os.remove(rutarasterdelimitado)
        except FileNotFoundError:
            pass


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

        tipo_salida=self.cmbcalculo.currentText

        # Ayuda de CloudCompare: https://www.cloudcompare.org/doc/wiki/index.php/Command_line_mode
        self.elimina(event)  # elimina previamente todos los archivos previos EN EDIFICIOS
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutanubedtm=os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES/' + "DEM_CC_TERRENO.laz")

        # Establecer la variable de entorno PATH
        os.environ["PATH"] = self.lerutacc.text() + ";" + os.environ["PATH"] #Posicionado en la ruta de CloudCompare
        rutafilecc=self.filecc.filePath() #ruta seleccionada en QgsFileWidget incluso archivo y extensión
        ejecutable=os.path.basename(rutafilecc) #solo nombre del ejecutable CloudCompare.exe

        # Comando de CloudCompare2
        comandocc = [
            ejecutable, # Ejecuta cloudcompare aunque no lo abre

            # Segmentación por edificios 6 fundido con terreno
            "-CLEAR",  # Cierra todas las entidades cargadas
            "-AUTO_SAVE OFF",
            "-O", "-GLOBAL_SHIFT AUTO",
            "../ACB-CAPAS/ACB_NUBES/EDIFICIOS_CC.laz",
            "-C_EXPORT_FMT LAS -EXT LAZ",  # cambia el formato para exportar nube a laz
            "-SAVE_CLOUDS FILE ../ACB-CAPAS/ACB_NUBES/SOLOEDIF_CC.laz",

            #UNE LAS NUBES TERRENO Y EDIFICIOS
            "-CLEAR",  # Cierra todas las entidades cargadas
            "-AUTO_SAVE OFF",
            "-O", "-GLOBAL_SHIFT AUTO",
            "../ACB-CAPAS/ACB_NUBES/DEM_CC_TERRENO.laz",
            "-O", "-GLOBAL_SHIFT FIRST",
            "../ACB-CAPAS/ACB_NUBES/EDIFICIOS_CC.laz",
            "-MERGE_CLOUDS",  # une todas las nubes
            "-C_EXPORT_FMT LAS -EXT LAZ",  # cambia el formato para exportar nube a laz
            "-SAVE_CLOUDS FILE ../ACB-CAPAS/ACB_NUBES/TERRENO_EDIF_CC.laz",

            #RASTERIZA TERRENOS Y EDIFICIOS
            "-CLEAR",  # Cierra todas las entidades cargadas
            "-AUTO_SAVE OFF",
            "-O", "-GLOBAL_SHIFT AUTO",
            "../ACB-CAPAS/ACB_NUBES/TERRENO_EDIF_CC.laz",
            "-NO_TIMESTAMP",  # Evita marcas de tiempo en el nombre del archivo de salida
            "-RASTERIZE",  # crea el raster MDT
            "-GRID_STEP " + str(malla),  # rejilla de resolución del raster producto
            "-VERT_DIR 2",  # Especifica dimension z (2)
            "-PROJ MAX",  # Se computa la altura de celda como minimo media y maximo MIN/AVG/MAX
            #"-EMPTY_FILL " + tipo_salida,  # celdas vacias se rellenan por interpolacion MIN_H/MAX_H/CUSTOM_H/INTERP
            #"-MAX_EDGE_LENGTH 500.0",  # Lado del triangulo máximo para interpolar
            "-OUTPUT_RASTER_Z",  # salida como geotiff raster de elevación
            "-CLEAR",  # Cierra todas las entidades cargadas

            #RASTERIZA SOLO EDIFICIOS
            "-AUTO_SAVE OFF",
            "-O", "-GLOBAL_SHIFT AUTO",
            "../ACB-CAPAS/ACB_NUBES/EDIFICIOS_CC.laz",
            "-NO_TIMESTAMP",  # Evita marcas de tiempo en el nombre del archivo de salida
            "-RASTERIZE",  # crea el raster MDT
            "-GRID_STEP " + str(malla),  # rejilla de resolución del raster producto
            "-VERT_DIR 2",  # Especifica dimension z (2)
            "-PROJ MIN",  # Se computa la altura de celda como minimo media y maximo MIN/AVG/MAX
            #"-EMPTY_FILL " + tipo_salida,  # celdas vacias se rellenan por interpolacion MIN_H/MAX_H/CUSTOM_H/INTERP
            #"-MAX_EDGE_LENGTH 50",  # Lado del triangulo máximo para interpolar
            "-OUTPUT_RASTER_Z",  # salida como geotiff raster de elevación
            "-CLEAR",  # Cierra todas las entidades cargadas
        ]
        subprocess.run(" ".join(comandocc), shell=True) #ejecuta cambio directorio y el comando

        self.muevearchivos2(event) # llamada a la funcion que mueve todos los archivos generados a ACBDATOS
        self.recortaraster2(event)
        self.rellenaraster2(event)    # llamada a la funcion rellena el raster elimina valores nulos
        self.cargaraster2(event)      # llamada a la funcion que carga el raster
        self.calculaedif(event) # función que clasifica edificios por altura con la calculadora raster
        self.cargaraster3(event)
        self.hillshade2(event)  # llamada a la funcion que creará y cargará un hillshade
        self.btnccomp.hide()
        self.pbcierra.show()
        self.close()
    def muevearchivos2(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutanube = os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES/')
        rutadatos = (os.path.join(rutactual, 'ACB-DATOS'))
        rutaraster = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/', str(self.qleraster2.text())))
        rutaraster2 = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/',"TERRENO_EDIFICIOS.tif"))
        rutaraster3 = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/', "EDIFICIOS.tif"))

        for archivo in os.listdir(rutanube):
            rutaentrada = os.path.join(rutanube, archivo)
            if "RASTER_Z" and "TERRENO_EDIF_CC" in archivo: # Verifica si el archivo tiene la cadena EDIFICIOS Y RASTER_Z
                try:
                    if "TERRENO_EDIF_CC.laz" in archivo:
                        pass
                    else:
                        os.replace(rutaentrada, rutaraster2)
                except:
                     pass

            elif "RASTER_Z" and "EDIFICIOS_CC" in archivo: # Verifica si el archivo tiene la cadena EDIFICIOS Y RASTER_Z
                try:
                    if "EDIFICIOS_CC.laz" in archivo:
                        pass
                    else:
                        os.replace(rutaentrada, rutaraster3)
                except:
                     pass
            elif "RASTER_Z" in archivo: # Verifica si el archivo tiene la cadena MERGED_RASTER
                try:
                    os.replace(rutaentrada, rutaraster)
                except:
                    pass
            else:
                pass
    def recortaraster2(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutaraster = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/', str(self.qleraster2.text())))
        rutamascara = (os.path.join(rutactual, 'ACB-CAPAS', "MASCARA.gpkg"))
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/', "TERRE_EDF_CC_FILL.tif"))  # ruta del raster relleno
        processing.run("gdal:cliprasterbymasklayer",
                       {'INPUT': rutaraster, 'MASK': rutamascara,
                        'SOURCE_CRS': crs, 'TARGET_CRS': crs, 'TARGET_EXTENT': None, 'NODATA': 255,
                        'ALPHA_BAND': False, 'CROP_TO_CUTLINE': True, 'KEEP_RESOLUTION': True, 'SET_RESOLUTION': False,
                        'X_RESOLUTION': None, 'Y_RESOLUTION': None, 'MULTITHREADING': False, 'OPTIONS': '',
                        'DATA_TYPE': 0,
                        'EXTRA': '',
                        'OUTPUT': rutarasterfill})
        #NODATA:255 las celdas sin datos pasa a 255 en principio no deberían verse
    def rellenaraster2(self,event):
        distancia=radio
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutaraster = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/', str(self.qleraster2.text())))
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/', "TERRE_EDF_CC_FILL.tif"))  # ruta del raster relleno
        processing.run("gdal:fillnodata", {
            'INPUT': rutarasterfill,
            'BAND': 1, 'DISTANCE': distancia, 'ITERATIONS': 3, 'MASK_LAYER': None, 'OPTIONS': '',
            'EXTRA': crs.postgisSrid(),  # atención asigna extra crs
            'OUTPUT': rutarasterfill})
    def cargaraster2(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/',"TERRE_EDF_CC_FILL.tif"))  # ruta del raster relleno
        caparaster=QgsRasterLayer(rutarasterfill,self.qleraster2.text())
        QgsProject.instance().addMapLayer(caparaster,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('EDIFICIOS')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, caparaster)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas

    def cargaraster3(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/',"EDIFICIOS.tif"))  # ruta del raster relleno
        caparaster=QgsRasterLayer(rutarasterfill,"EDIFICIOS_CC")
        QgsProject.instance().addMapLayer(caparaster,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('EDIFICIOS')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, caparaster)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas
    def hillshade2(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/',"TERRE_EDF_CC_FILL.tif"))  # ruta del raster relleno
        rutahillshade = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/', "TERRENO_EDF_CC_HILLSHADE.tif"))  # ruta del raster hillshade
        processing.run("gdal:hillshade", {
            'INPUT': rutarasterfill,
            'BAND': 1, 'Z_FACTOR': 2, 'SCALE': 1, 'AZIMUTH': 315, 'ALTITUDE': 45, 'COMPUTE_EDGES': True,
            'ZEVENBERGEN': True, 'COMBINED': False, 'MULTIDIRECTIONAL': True,
            'OPTIONS': 'COMPRESS=NONE|BIGTIFF=IF_NEEDED',
            #'EXTRA': crs.postgisSrid(),
            'OUTPUT': rutahillshade})

        # Agrega la capa rutahillshade
        caparaster=QgsRasterLayer(rutahillshade,'TERRENO_EDF_CC_HILLSHADE.tif')
        QgsProject.instance().addMapLayer(caparaster,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('EDIFICIOS')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, caparaster)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas
    def elimina(self,event):
        proyecto = QgsProject.instance()
        nombre_subgrupo = "EDIFICIOS"
        subgrupo = proyecto.layerTreeRoot().findGroup(nombre_subgrupo)
        try:
            if subgrupo is not None: #si el grupo existe
                capas_subgrupo = subgrupo.children()            # Obtener una lista de todas las capas dentro del subgrupo
                for capa in capas_subgrupo:            # Eliminar cada capa del subgrupo
                    proyecto.removeMapLayer(capa.layer())
        except:
            pass

    def calculaedif(self,event):
        #https://gis.stackexchange.com/questions/385016/qgis-python-raster-calculator
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutaA = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/',"TERRE_EDF_CC_FILL.tif"))# ruta del raster TERRENO Y EDIFICIOS
        rutaB = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/',"DEM_CC_FILL.tif"))  # ruta del raster TERRENO
        rutaC = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/',"EDIFICIOSbyALTURA_CC.tif"))

        entradas=[]
        capa1 = QgsRasterLayer(rutaA,"TERRENO_EDIFICIOS.tif@1")
        capa2 = QgsRasterLayer(rutaB,"DEM_CC.tif@1")
        capa3 = QgsRasterLayer(rutaC,"EDIFICIOSbyALTURA_CC")

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

        calc=QgsRasterCalculator(f"({ras1} - {ras2} > 0) * ({ras1} - {ras2}) ", rutaC,'GTiff', capa1.extent(), capa1.width(), capa1.height(), entradas)
        #con esta expresión se calcula la diferencia de altura solo cuando sea mayor que 0
        calc.processCalculation()

        #carga el raster resultado EDIFICIOSbyALTURA en el mapa ya clasificado por alturas contra terreno
        QgsProject.instance().addMapLayer(capa3,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('EDIFICIOS')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, capa3)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas

