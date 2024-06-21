# -*- coding: utf-8 -*-
#las librerias se importan a python en la consola osgeo4w shell
#teclenado python3 -m pip install pdal o cualquier otra libreria

#    forcc4.py     CLOUDCOMPARE MODELO DIGITAL DE VEGETACION
# Ayuda de CloudCompare: https://www.cloudcompare.org/doc/wiki/index.php/Command_line_mode

import pathlib
from pathlib import Path, PureWindowsPath, PurePath
from PyQt5.QtWidgets import QDialog,QLabel, QApplication
from qgis.PyQt import uic
import os
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
import processing
import subprocess
from qgis.utils import iface
from qgis.core import QgsProject, QgsRasterLayer, QgsCoordinateReferenceSystem,QgsExpressionContextUtils
from qgis.PyQt.QtWidgets import QMessageBox


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "forcc4.ui"))

class FormularioCloudComp4(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(FormularioCloudComp4, self).__init__(parent)
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

        crs = QgsProject.instance().crs()
        malla=2
        self.qlemalla.setText(str(malla))
        radio=malla+4
        self.qleradio.setText(str(radio))
        tipo_salida="INTERP"
        self.cmbcalculo.currentText=tipo_salida
        self.qlelidar.setText("TERyVEG_CC.laz")
        self.qleraster2.setText("VegetacionyTerreno.tif")
        self.qlecrs.setText(str(crs.postgisSrid()))
        self.qlemalla.textChanged.connect(self.actualiza)   #cuando el texto de malla cambie se actualiza el formulario

        # Muestra el mensaje
        QMessageBox.information(None,"Aviso","Se precisa paso previo por DSM CLOUD COMPARE")
        titulo = "\nEn proceso \nCreación archivos  RASTER .tif y Nube .laz"
        cuerpo1 = "Fusión de nubes laz, Clasificación\nEliminación de Ruido, Creación Ráster"
        cuerpo2 = "Archivo " + self.qlelidar.text() + " " + self.qleraster2.text()
        self.lbproceso.setText(titulo)
        self.lbproceso1.setText(cuerpo1)
        self.lbproceso2.setText(cuerpo2)

    def actualiza(self,event):
        radio=float(self.qlemalla.text())+4 #toma el valor flotante del texto en label qlemalla y añade 1
        self.qleradio.setText(str(radio)) #actualiza el valor del radio
        self.repaint() #repinta

    def eliminasuperados(self,event):
        try:
            os.remove(rutaraster)
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
        os.chdir(rutapdal) #cambia de directorio en la consola para crear el archivo bat
        malla=float(self.qlemalla.text())
        radio=float(self.qleradio.text())
        tipo_salida=self.cmbcalculo.currentText

        self.elimina(event)  # elimina previamente todos los archivos previos EN VEGETACION

        # Establecer la variable de entorno PATH
        os.environ["PATH"] = self.lerutacc.text() + ";" + os.environ["PATH"] #Posicionado en la ruta de CloudCompare
        rutafilecc=self.filecc.filePath() #ruta seleccionada en QgsFileWidget incluso archivo y extensión
        ejecutable=os.path.basename(rutafilecc) #solo nombre del ejecutable CloudCompare.exe

        # Comando de CloudCompare2
        comandocc = [
            ejecutable, # Ejecuta cloudcompare aunque no lo abre

            # Segmentación por Vegetacion 3 a 5 fundido con terreno
            "-CLEAR",  # Cierra todas las entidades cargadas
            "-AUTO_SAVE OFF",
            "-O", "-GLOBAL_SHIFT AUTO",
            "../ACB-CAPAS/ACB_NUBES/VEGETACION_CC.laz",
            "-C_EXPORT_FMT LAS -EXT LAZ",  # cambia el formato para exportar nube a laz
            "-SAVE_CLOUDS FILE ../ACB-CAPAS/ACB_NUBES/SOLOVEG_CC.laz",

            #UNE LAS NUBES VEGETACION
            "-CLEAR",  # Cierra todas las entidades cargadas
            "-AUTO_SAVE OFF",
            "-O", "-GLOBAL_SHIFT AUTO",
            "../ACB-CAPAS/ACB_NUBES/DEM_CC_TERRENO.laz",
            "-O", "-GLOBAL_SHIFT FIRST",
            "../ACB-CAPAS/ACB_NUBES/VEGETACION_CC.laz",
            "-MERGE_CLOUDS",  # une todas las nubes
            "-C_EXPORT_FMT LAS -EXT LAZ",  # cambia el formato para exportar nube a laz
            "-SAVE_CLOUDS FILE ../ACB-CAPAS/ACB_NUBES/TERRENO_VEG_CC.laz",

            #RASTERIZA VEGETACION Y TERRENO
            "-CLEAR",  # Cierra todas las entidades cargadas
            "-AUTO_SAVE OFF",
            "-O", "-GLOBAL_SHIFT AUTO",
            "../ACB-CAPAS/ACB_NUBES/TERRENO_VEG_CC.laz",
            "-NO_TIMESTAMP",  # Evita marcas de tiempo en el nombre del archivo de salida
            "-RASTERIZE",  # crea el raster 
            "-GRID_STEP " + str(malla),  # rejilla de resolución del raster producto
            "-VERT_DIR 2",  # Especifica dimension z (2)
            "-PROJ MAX",  # Se computa la altura de celda como minimo media y maximo MIN/AVG/MAX
            #"-EMPTY_FILL KRIGING", # celdas vacias se rellenan por interpolacion MIN_H/MAX_H/CUSTOM_H/INTERP/KRIGING
            #"-KRIGING_KNN 8", #Número de vecinos a considerar en la interpolación de KRIGING
            "-MAX_EDGE_LENGTH 100.0",  # Lado del triangulo máximo para interpolar
            "-OUTPUT_RASTER_Z",  # salida como geotiff raster de elevación
            "-CLEAR",  # Cierra todas las entidades cargadas

            #RASTERIZA SOLO VEGETACION
            "-AUTO_SAVE OFF",
            "-O", "-GLOBAL_SHIFT AUTO",
            "../ACB-CAPAS/ACB_NUBES/SOLOVEG_CC.laz",
            "-NO_TIMESTAMP",  # Evita marcas de tiempo en el nombre del archivo de salida
            "-RASTERIZE",  # crea el raster MDT
            "-GRID_STEP " + str(malla),  # rejilla de resolución del raster producto
            "-VERT_DIR 2",  # Especifica dimension z (2)
            "-PROJ MAX",  # Se computa la altura de celda como minimo media y maximo MIN/AVG/MAX
            #"-EMPTY_FILL " + tipo_salida,  # celdas vacias se rellenan por interpolacion MIN_H/MAX_H/CUSTOM_H/INTERP
            "-MAX_EDGE_LENGTH 1",  # Lado del triangulo máximo para interpolar
            "-OUTPUT_RASTER_Z",  # salida como geotiff raster de elevación
            "-CLEAR",  # Cierra todas las entidades cargadas
        ]
        subprocess.run(" ".join(comandocc), shell=True) #ejecuta cambio directorio y el comando

        self.muevearchivos2(event) # llamada a la funcion que mueve todos los archivos generados a ACBDATOS
        self.recortaraster(event)
        self.rellenaraster(event)  # llamada a la funcion que recorta contra la máscara asumiendo que ya están rellenas las celdas con kriging
        self.recortaraster2(event)
        self.rellenaraster2(event)    # llamada a la funcion rellena el raster elimina valores nulos
        self.cargaraster(event)      # llamada a la funcion que carga el raster
        self.cargaraster2(event)
        self.calculaveg(event) # función que clasifica edificios por altura con la calculadora raster
        self.eliminasuperados(event) # llamada a la funcion que borra los archivos intermedios raster

        self.btnccomp.hide()
        self.pbcierra.show()
        self.close()
    def muevearchivos2(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutanube = os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES/')
        rutaraster = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', str(self.qleraster2.text()))) #"VegetacionyTerreno.tif"
        rutaraster2 = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/',"TERRAyVEG_CC_FILL.tif"))
        rutaraster3 = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', "VEGETA_CC.tif"))

        for archivo in os.listdir(rutanube):
            rutaentrada = os.path.join(rutanube, archivo)
            if "RASTER_Z" and "TERRENO_VEG_CC" in archivo: # Verifica si el archivo tiene la cadena 
                try:
                    os.replace(rutaentrada, rutaraster2)
                except:
                     pass
            elif "RASTER_Z" and "SOLOVEG_CC" in archivo: # Verifica si el archivo tiene la cadena 
                try:
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

    def recortaraster(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutaraster = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/',"TERRAyVEG_CC_FILL.tif"))
        rutamascara = (os.path.join(rutactual, 'ACB-CAPAS', "MASCARA.gpkg"))
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', "TERyVEG_CC_FILL.tif"))  # ruta del raster relleno
        processing.run("gdal:cliprasterbymasklayer",
                       {'INPUT': rutaraster, 'MASK': rutamascara,
                        'SOURCE_CRS': crs, 'TARGET_CRS': crs, 'TARGET_EXTENT': None, 'NODATA': 255,
                        'ALPHA_BAND': False, 'CROP_TO_CUTLINE': True, 'KEEP_RESOLUTION': False, 'SET_RESOLUTION': False,
                        'X_RESOLUTION': None, 'Y_RESOLUTION': None, 'MULTITHREADING': False, 'OPTIONS': '',
                        'DATA_TYPE': 0,
                        'EXTRA': '',
                        'OUTPUT': rutarasterfill})

        # NODATA:255 las celdas sin datos pasa a 255 en principio no deberían verse
    def rellenaraster(self,event):
        distancia=radio
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutaraster = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/',"TERRAyVEG_CC_FILL.tif"))
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', "TERyVEG_CC_FILL.tif"))  # ruta del raster relleno
        processing.run("gdal:fillnodata", {
            'INPUT': rutarasterfill,
            'BAND': 1, 'DISTANCE': distancia, 'ITERATIONS': 0, 'MASK_LAYER': None, 'OPTIONS': '',
            'EXTRA': crs.postgisSrid(),#atención asigna extra crs
            'OUTPUT': rutarasterfill})
    def recortaraster2(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutaraster2 = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/',"VEGETA_CC.tif"))
        rutamascara = (os.path.join(rutactual, 'ACB-CAPAS', "MASCARA.gpkg"))
        rutarasterfill2 = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', "VEG_CC.tif"))  # ruta del raster relleno
        processing.run("gdal:cliprasterbymasklayer",
                       {'INPUT': rutaraster2, 'MASK': rutamascara,
                        'SOURCE_CRS': crs, 'TARGET_CRS': crs, 'TARGET_EXTENT': None, 'NODATA': 255,
                        'ALPHA_BAND': False, 'CROP_TO_CUTLINE': True, 'KEEP_RESOLUTION': False, 'SET_RESOLUTION': False,
                        'X_RESOLUTION': None, 'Y_RESOLUTION': None, 'MULTITHREADING': False, 'OPTIONS': '',
                        'DATA_TYPE': 0,
                        'EXTRA': '',
                        'OUTPUT': rutarasterfill2})
    def rellenaraster2(self,event):
        distancia=radio
        rutactual2 = QgsProject.instance().homePath()  # ruta actual
        rutaraster2 = (os.path.join(rutactual2, 'ACB-CAPAS/ACB_DSM_CCOMP/',"VEGETA_CC.tif"))
        rutarasterfill2 = (os.path.join(rutactual2, 'ACB-CAPAS/ACB_DSM_CCOMP/', "VEG_CC.tif"))  # ruta del raster relleno
        processing.run("gdal:fillnodata", {
            'INPUT': rutarasterfill2,
            'BAND': 1, 'DISTANCE': distancia, 'ITERATIONS': 0, 'MASK_LAYER': None, 'OPTIONS': '',
            'EXTRA': crs.postgisSrid(),#atención asigna extra crs
            'OUTPUT': rutarasterfill2})
    def cargaraster(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/',"TERyVEG_CC_FILL.tif"))  # ruta del raster relleno
        caparaster=QgsRasterLayer(rutarasterfill,self.qleraster2.text())#"VegetacionyTerreno.tif"S
        processing.run("gdal:assignprojection",{'INPUT': rutarasterfill,'CRS': QgsCoordinateReferenceSystem('EPSG:' + str(crs.postgisSrid()))})
        QgsProject.instance().addMapLayer(caparaster,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('VEGETACION')           #localiza el grupo en el árbol
        grupomapa.insertLayer(0, caparaster)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas

    def cargaraster2(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutarasterfill2 = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/',"VEG_CC.tif"))  # ruta del raster relleno
        caparaster=QgsRasterLayer(rutarasterfill2,"VEGETACION_CC")
        processing.run("gdal:assignprojection",{'INPUT': rutarasterfill2,'CRS': QgsCoordinateReferenceSystem('EPSG:' + str(crs.postgisSrid()))})  # atención asigna extra crs
        QgsProject.instance().addMapLayer(caparaster,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('VEGETACION')           #localiza el grupo en el árbol
        grupomapa.insertLayer(0, caparaster)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas
    def eliminasuperados(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutaraster2 = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/',"TERyVEG_CC.tif"))
        try:
            os.remove(rutaraster2)
        except FileNotFoundError:
            pass

    def elimina(self,event):
        proyecto = QgsProject.instance()
        nombre_subgrupo = "VEGETACION"
        subgrupo = proyecto.layerTreeRoot().findGroup(nombre_subgrupo)
        try:
            if subgrupo is not None: #si el grupo existe
                capas_subgrupo = subgrupo.children()            # Obtener una lista de todas las capas dentro del subgrupo
                for capa in capas_subgrupo:            # Eliminar cada capa del subgrupo
                    proyecto.removeMapLayer(capa.layer())
        except:
            pass
    def calculaveg(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutaA = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/',"TERyVEG_CC_FILL.tif"))# ruta del raster VEGETACION Y TERRENO
        rutaB = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DEM_CCOMP/',"DEM_CC_FILL.tif"))  # ruta del raster TERRENO
        
        rutaC = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/',"VEGbyALTURA_CC.tif"))
        capaC = QgsRasterLayer(rutaC, "VEGbyALTURA_CC")
        rutaD = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', "VEG_0a1_CC.tif"))
        capaD = QgsRasterLayer(rutaD, "VEG_0a1_CC")
        rutaE = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', "VEG_1a4_CC.tif"))
        capaE = QgsRasterLayer(rutaE, "VEG_1a4_CC")
        rutaF = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', "VEG_4a20_CC.tif"))
        capaF = QgsRasterLayer(rutaF, "VEG_4a20_CC")
        rutaG = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', "VEG_MAS20_CC.tif"))
        capaG = QgsRasterLayer(rutaG, "VEG_MAS20_CC")


        entradas=[]
        capa1 = QgsRasterLayer(rutaA,"VegetacionyTerreno.tif@1")
        capa2 = QgsRasterLayer(rutaB,"DEM_CC.tif@1")

        rutas = [capaC,capaD,capaE,capaF,capaG]

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
            try:
                #carga el raster resultado en el mapa ya clasificado por alturas contra terreno
                QgsProject.instance().addMapLayer(ruta,False) #aguanta la carga del raster
                root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
                grupomapa=root.findGroup('VEGETACION')           #localiza el grupo en el árbol
                grupomapa.insertLayer(-1, ruta)               #inserta la capa raster al final del grupo
                iface.mapCanvas().refresh()                     # Refresca canvas
            except:
                QMessageBox.information(None,'Generada No Cargada',f"Trata de cargar a mano la capa\n {ruta}")