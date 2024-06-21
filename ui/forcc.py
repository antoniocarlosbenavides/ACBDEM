# -*- coding: utf-8 -*-
#las librerias se importan a python en la consola osgeo4w shell
#teclenado python3 -m pip install pdal o cualquier otra libreria

#    forcc.py     CLOUDCOMPARE MODELO DIGITAL DE SUPERFICIES
# Ayuda de CloudCompare: https://www.cloudcompare.org/doc/wiki/index.php/Command_line_mode

from PyQt5.QtWidgets import QDialog
from qgis.PyQt import uic
from PyQt5.QtGui import QFont, QColor
import os
import processing
import subprocess
from qgis.utils import iface
from qgis.core import QgsProject,QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem,QgsExpressionContextUtils
from qgis.PyQt.QtWidgets import QMessageBox

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "forcc.ui"))

'''
Ayuda Consola CloudCompare
https://www.cloudcompare.org/doc/wiki/index.php/Command_line_mode
MODELO DIGITAL DE SUPERFICIE CLOUDCOMPARE forcc.py
'''
class FormularioCloudComp(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(FormularioCloudComp, self).__init__(parent)
        self.setupUi(self)
        self.btnccomp.mousePressEvent = self.scriptarchivo
        self.pbcierra.clicked.connect(self.cierraformulario)
        self.btnccomp.show() #muestra el boton pbpdal
        self.pbcierra.hide() #oculta el boton cierra
        self.pbrutacc.mousePressEvent = self.localizacc
        global malla,radio, pdalconsola,ejecutable,rutacloudcompare,crs
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
        radio=max(50,malla*2)
        self.qleradio.setText(str(radio))
        self.qlelidar.setText("NUBE_CC.laz")
        self.qleraster.setText("DSM_CC.tif")
        crs = QgsProject.instance().crs()
        self.qlecrs.setText(format(crs.postgisSrid()))
        self.qlecrs5.setText(format(crs.description()))
        self.qlemalla.textChanged.connect(self.actualiza)   #cuando el texto de malla cambie se actualiza el formulario



    def actualiza(self,event):
        radio=max(50,float(self.qlemalla.text())*2) #toma el valor flotante del texto en label qlemalla y multiplica por 2
        self.qleradio.setText(str(radio)) #actualiza el valor del radio
        self.repaint() #repinta
    def scriptarchivo(self,event):
        self.elimina(event)     #elimina previamente todos los archivos previos
        # Rutas
        global rutactual, rutapdal, rutamascara, rutaraster, rutalidar, rutarasterdelimitado, rutarasterfill, rutahillshade, rutarasterRGB, rutanube
        rutactual = QgsProject.instance().homePath() #ruta actual
        rutanube=(os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES'))
        rutapdal = (os.path.join(rutactual, 'ACB-DATOS'))                                       #ruta del json
        rutamascara = (os.path.join(rutactual, 'ACB-CAPAS', "MASCARA.gpkg"))                    #ruta de la máscara
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', "DSM_CC_FILLCC.tif"))  # ruta del raster relleno
        rutahillshade = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', "DSM_CC_HILLSHADECC.tif"))  # ruta del raster hillshade
        rutarasterdelimitado = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', "DSM_CC_RECORCC.tif"))  #ruta del raster recortado
        rutaraster = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', str(self.qleraster.text())))
        rutarasterRGB = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', 'RGB'+str(self.qleraster.text())))
        rutalidar = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', str(self.qlelidar.text())))
        rutanube=(os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES'))
        os.chdir(rutapdal) #cambia de directorio en la consola para crear el archivo bat

        malla=float(self.qlemalla.text())
        radio=float(self.qleradio.text())

        # Ayuda de CloudCompare: https://www.cloudcompare.org/doc/wiki/index.php/Command_line_mode
        # Clasificacion 1 es no clasificado
        # Clasificacion 2 es terreno
        # Clasificacion 3 a 5 es vegetacion 3baja 1m   4media 1-3m   5alta 3-100m
        # Clasificacion 6 es edificio
        # Clasificacion 7 es punto bajo casi siempre ruido
        # Clasificacion 9 es agua de mar
        # Clasificacion 10 es Ferrocarril
        # Clasificacion 11 es Carretera
        # Clasificacion 12 puntos de solape
        # Clasificacion 13 y 14 son puntos de cable
        # Clasificacion 15 es una torre de transmisión
        # Clasificacion 17 puentes
        # Clasificacion 18 es ruido

        #Calcula la extensión de la capa máscara
        capas_corte= QgsProject.instance().mapLayersByName("MASCARA")
        if capas_corte:
            capa_corte=capas_corte[0]
        extension = capa_corte.extent()
        #COORDENADAS DE EXTENSIÓN DE LA CAPA
        x1 = extension.xMinimum()
        y1 = extension.yMinimum()
        x2 = extension.xMaximum()
        y2= extension.yMaximum()

        # Establecer la variable de entorno PATH
        global  rutafilecc,ejecutable
        os.environ["PATH"] = self.lerutacc.text() + ";" + os.environ["PATH"] #Posicionado en la ruta de CloudCompare
        rutafilecc=self.filecc.filePath() #ruta seleccionada en QgsFileWidget incluso archivo y extensión
        ejecutable=os.path.basename(rutafilecc) #solo nombre del ejecutable CloudCompare.exe

        # Comando de CloudCompare une nubes y recorta contra máscara
        comandocc = [
            ejecutable, # Ejecuta cloudcompare aunque no lo abre
            "-LOG_FILE ../ACB-CAPAS/ACB_NUBES/infoproceso.txt",  # registra los procesos en un archivo
            "-AUTO_SAVE OFF", # Neutraliza que adopte el nombre del resultado automatico
        ]
        # Agregar cada archivo LAZ al comando denominado comandocc
        comandocc.extend(["-O",
                          "-GLOBAL_SHIFT AUTO",
                          "../ACB-CAPAS/ACB_NUBES/NUBE.laz"])  # -O esto es open, abre el archivo en AUTO solo el primero es AUTO

        # Resto del comando de CloudCompare se añade una lista dentro de otra lista con extend
        comandocc.extend([
            "-NO_TIMESTAMP",# Evita marcas de tiempo en el nombre del archivo de salida
            "-RASTERIZE", #crea el raster MDT
            "-GRID_STEP "+str(malla), #rejilla de resolución del raster producto
            "-PROJ MAX",#Se computa la altura de celda como minimo media y maximo MIN/AVG/MAX
            "-MAX_EDGE_LENGTH 100.0", #Lado del triangulo máximo para interpolar
            "-EMPTY_FILL INTERP",
            "-VERT_DIR 2", #Especifica dimension z (2)
            "-OUTPUT_RASTER_Z", #salida como geotiff raster de elevación
            "-OUTPUT_CLOUD",
            "-C_EXPORT_FMT LAS -EXT LAZ",  # cambia el formato para exportar nube a laz
            "-SAVE_CLOUDS FILE ../ACB-CAPAS/ACB_NUBES/NUBEDSM_CC",  # exporta la nube DSM a laz
        ])
        # MODELO DE ELEVACIONES
        if self.rb_a.isChecked():
            self.ventanamensaje("Segoe Print", 12, "Modelo Elevaciones","Opcion A\n Filtro No Terreno CSF")
            # MODELO DE ELEVACIONES SIN TERRENO FILTRO CSF
            comandocc.extend([
                # Cloth Simulation Filter (CSF) plugin SEPARA NO TERRENO
                "-CSF -SCENES SLOPE", # a elegir SLOPE(pendiente pronunciada)  RELIEF(relieve)   FLAT(plano)
                "-PROC_SLOPE", #se aplica solo si la pendiente es pronunciada SLOPE
                "-CLOTH_RESOLUTION "+str(malla), #Algo menor 1/3 del espacio entre puntos 0,5 o incluso menos
                "-MAX_ITERATION 500", #de 500 a 1000 no mejora mucho así que 500 está bien
                "-CLASS_THRESHOLD 0.5", #umbral clasificación terreno 0.5 es válido usualmente
                "-EXPORT_OFFGROUND",  # genera nube de NO Terreno
                "-CLEAR", #Cierra todas las entidades cargadas
            ])
        else:
            self.ventanamensaje("Segoe Print", 12, "Modelo Elevaciones", "Opcion B\n Clasificación LIDAR excluye 0  1  y  2")
            #MODELO DE ELEVACIONES SIN TERRENO UNICAMENTE CLASIFICACION
            comandocc.extend([
                "-CLEAR", #Cierra todas las entidades cargadas
                "-LOG_FILE ../ACB-CAPAS/ACB_NUBES/InfoNoTerreno.txt",  # registra los procesos en un archivo
                "-AUTO_SAVE OFF",
                "-O", "-GLOBAL_SHIFT FIRST",
                "../ACB-CAPAS/ACB_NUBES/NUBE.laz",
                "-SET_ACTIVE_SF Classification",
                "-FILTER_SF 3 11",  # filtra no terreno
                "-RASTERIZE",
                "-GRID_STEP " + str(malla),  # rejilla de resolución del raster producto
                "-PROJ MAX",  # Se computa la altura de celda como minimo media y maximo MIN/AVG/MAX
                "-MAX_EDGE_LENGTH 100.0",  # Lado del triangulo máximo para interpolar
                "-EMPTY_FILL INTERP",  # Delaunay triangulacion para interpolación del terreno
                "-VERT_DIR 2",  # Especifica dimension z (2)
                "-AUTO_SAVE OFF",
                "-C_EXPORT_FMT LAS -EXT LAZ",  # cambia el formato para exportar nube a laz
                "-SAVE_CLOUDS FILE ../ACB-CAPAS/ACB_NUBES/OFF_CC.laz",
                "-SAVE_CLOUDS FILE ../ACB-CAPAS/ACB_NUBES/NUBEDSM_CC_NOTERRENO.laz",
                "-CLEAR",  # Cierra todas las entidades cargadas
            ])

        # Segmentación por TERRENO clasificacion 2
        comandocc.extend([
            "-LOG_FILE ../ACB-CAPAS/ACB_NUBES/InfoTerreno.txt",  # registra los procesos en un archivo
            "-AUTO_SAVE OFF",
            "-O", "-GLOBAL_SHIFT FIRST",
            "../ACB-CAPAS/ACB_NUBES/NUBE.laz",
            "-SET_ACTIVE_SF Classification",
            "-FILTER_SF 2 2",  # filtra por terreno
            "-RASTERIZE",  # crea el raster MDT
            "-GRID_STEP " + str(malla),  # rejilla de resolución del raster producto
            "-PROJ MAX",  # Se computa la altura de celda como minimo media y maximo MIN/AVG/MAX
            "-MAX_EDGE_LENGTH 100.0", #Lado del triangulo máximo para interpolar
            "-EMPTY_FILL INTERP", #Delaunay triangulacion para interpolación del terreno
            "-VERT_DIR 2",  # Especifica dimension z (2)
            "-AUTO_SAVE OFF",
            "-C_EXPORT_FMT LAS -EXT LAZ",  # cambia el formato para exportar nube a laz
            "-SAVE_CLOUDS FILE ../ACB-CAPAS/ACB_NUBES/TERRENO_CC.laz",
            "-CLEAR",  # Cierra todas las entidades cargadas

            #Segmentación por edificios 6
            "-LOG_FILE ../ACB-CAPAS/ACB_NUBES/InfosegmentaEdificios.txt",  # registra los procesos en un archivo
            "-AUTO_SAVE OFF",
            "-O", "-GLOBAL_SHIFT FIRST",
            #"../ACB-CAPAS/ACB_NUBES/NUBE.laz",
            "../ACB-CAPAS/ACB_NUBES/NUBEDSM_CC.las",
            "-SET_ACTIVE_SF Classification",
            "-AUTO_SAVE OFF",
            "-C_EXPORT_FMT LAS -EXT LAZ",  # cambia el formato para exportar nube a laz
            "-FILTER_SF 6 6",  # filtra por campos escalar Classification 6 es edificacion
            "-SAVE_CLOUDS FILE ../ACB-CAPAS/ACB_NUBES/EDIFICIOS_CC.laz",
            "-CLEAR",  # Cierra todas las entidades cargadas

            # Segmentación por vegetación 3 a 5
            "-LOG_FILE ../ACB-CAPAS/ACB_NUBES/InfosegmentaVegetacion.txt",  # registra los procesos en un archivo
            "-AUTO_SAVE OFF",
            "-O", "-GLOBAL_SHIFT FIRST",
            #"../ACB-CAPAS/ACB_NUBES/NUBE.laz",
            "../ACB-CAPAS/ACB_NUBES/NUBEDSM_CC.las",
            "-SET_ACTIVE_SF Classification",
            "-AUTO_SAVE OFF",
            "-C_EXPORT_FMT LAS -EXT LAZ",  # cambia el formato para exportar nube a laz
            "-FILTER_SF 3 5",  # filtra por campos escalar Classification 6 es edificacion
            "-SAVE_CLOUDS FILE ../ACB-CAPAS/ACB_NUBES/VEGETACION_CC.laz",
            "-CLEAR"  # Cierra todas las entidades cargadas
        ])
        subprocess.run(" ".join(comandocc), shell=True)
        self.muevearchivos(event) # llamada a la funcion que mueve todos los archivos generados a ACBDATOS
        self.recortaraster(event)  # llamada a la funcion que recorta contra la máscara asumiendo que ya están rellenas las celdas
        self.rellenaraster(event)    # llamada a la funcion rellena el raster elimina valores nulos
        self.cargaraster(event)      # llamada a la funcion que carga el raster
        self.hillshade(event)  # llamada a la funcion que creará y cargará un hillshade
        #self.cargalidar(event)       # llamada a la funcion que carga el lidar
        self.ventanamensaje("Segoe Print", 12, "Proceso CloudCompare DSM LIDAR Terminado", "NUBE y Ráster DSM " + str(malla) + "x" + str(malla) + "\n Procesa Curvas de Nivel y Mallas\n si procede")
        self.btnccomp.hide()
        self.pbcierra.show()
        self.close()
        self.renombra(event) #esta función renombrará los archivos para pasar despues a DEM

    def muevearchivos(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutanubes = (os.path.join(rutactual, 'ACB-DATOS/NUBEPUNTOS'))  # Ruta de la carpeta con todas las nubes de puntos
        rutanubes2 = (os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES'))
        rutadatos = (os.path.join(rutactual, 'ACB-DATOS'))
        rutademccop = (os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES/', 'DEM_CC_TERRENO.laz'))
        rutademccop2 = (os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES/', 'OFF_CC.laz'))
        rutaraster = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', str(self.qleraster.text())))
        rutavegeta = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/VEGETACION_', str(self.qleraster.text())))
        rutaedificios = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/EDIFICIOS_', str(self.qleraster.text())))

        for archivo2 in os.listdir(rutanubes2):
            rutademcc = os.path.join(rutanubes2, archivo2)
            if "TERRENO_CC" in archivo2:  # Verifica si el archivo tiene la cadena TERRENO_CC
                os.replace(rutademcc, rutademccop)  #lo mueve a otra carpeta
            if "offground_points" in archivo2:  # Verifica si el archivo tiene la cadena NUBEDSM_CC_offground_points.LAZ
                os.replace(rutademcc, rutademccop2)  #lo mueve a otra carpeta

        for archivo in os.listdir(rutanubes):
            rutaentrada = os.path.join(rutanubes, archivo)
            if "VEGETACION_CC" in archivo and "RASTER_Z" in archivo: # Verifica si el archivo tiene la cadena
                os.replace(rutaentrada, rutavegeta)

        for archivo in os.listdir(rutanubes):
            rutaentrada = os.path.join(rutanubes, archivo)
            if "EDIFICIOS_CC" in archivo and "RASTER_Z" in archivo: # Verifica si el archivo tiene la cadena
                os.replace(rutaentrada, rutaedificios)

        for archivo in os.listdir(rutanubes):
            rutaentrada = os.path.join(rutanubes, archivo)
            if "RASTER_Z" in archivo: # Verifica si el archivo tiene la cadena
                try:
                    os.replace(rutaentrada, rutaraster)
                except:
                    pass

        for archivo in os.listdir(rutanubes2):
            rutaentrada = os.path.join(rutanubes2, archivo)
            if "RASTER_Z" in archivo: # Verifica si el archivo tiene la cadena
                try:
                    os.replace(rutaentrada, rutaraster)
                except:
                    pass
        for archivo in os.listdir(rutanubes2):
            if ".las" in archivo: # Verifica si el archivo tiene la cadena
                try:
                    os.remove(os.path.join(rutanubes2, archivo))
                except FileNotFoundError:
                    pass
        for archivo in os.listdir(rutanubes2):
            if "OFF_CC" in archivo: # Verifica si el archivo tiene la cadena
                try:
                    os.remove(os.path.join(rutanubes2, archivo))
                except FileNotFoundError:
                    pass

    def recortaraster(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutaraster = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', str(self.qleraster.text()))) # DSM_CC.tif
        rutamascara = (os.path.join(rutactual, 'ACB-CAPAS', "MASCARA.gpkg"))
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', "DSM_CC_FILLCC.tif"))  # ruta del raster relleno
        processing.run("gdal:cliprasterbymasklayer",
                       {'INPUT': rutaraster, 'MASK': rutamascara,
                        'SOURCE_CRS': crs, 'TARGET_CRS': crs,
                        'TARGET_EXTENT': None, 'NODATA': 255,
                        'ALPHA_BAND': False, 'CROP_TO_CUTLINE': True, 'KEEP_RESOLUTION': True, 'SET_RESOLUTION': False,
                        'X_RESOLUTION': None, 'Y_RESOLUTION': None, 'MULTITHREADING': False, 'OPTIONS': '',
                        'DATA_TYPE': 0,
                        'EXTRA': '',
                        'OUTPUT': rutarasterfill})
        #NODATA:255 las celdas sin datos pasa a 255 en principio no deberían verse

    def rellenaraster(self,event): #Está siendo ignorado porque ya se aplicó kriging en Cloudcompare
        distancia=radio
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutaraster = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', str(self.qleraster.text())))
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', "DSM_CC_FILLCC.tif"))  # ruta del raster relleno
        processing.run("gdal:fillnodata", {
            'INPUT': rutarasterfill,
            'BAND': 1, 'DISTANCE': distancia, 'ITERATIONS': 0, 'NO_MASK': False, 'MASK_LAYER': None, 'OPTIONS': '',
            'EXTRA':crs.postgisSrid(),#atención asigna extra crs
            'OUTPUT': rutarasterfill})
    def cargaraster(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutarasterfill = (os.path.join(rutactual, 'ACB-CAPAS/ACB_DSM_CCOMP/', "DSM_CC_FILLCC.tif"))  # ruta del raster relleno
        # Agrega la capa rutarasterfill ya recorado y rellenada celdas sin valor
        caparaster=QgsRasterLayer(rutarasterfill,self.qleraster.text())
        QgsProject.instance().addMapLayer(caparaster,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('DSM_CCOMP')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, caparaster)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas

    def hillshade(self,event):
        processing.run("gdal:hillshade", {
            'INPUT': rutarasterfill,
            'BAND': 1, 'Z_FACTOR': 2, 'SCALE': 1, 'AZIMUTH': 225, 'ALTITUDE': 45, 'COMPUTE_EDGES': False,
            'ZEVENBERGEN': True, 'COMBINED': False, 'MULTIDIRECTIONAL': True,
            'OPTIONS': 'COMPRESS=DEFLATE|PREDICTOR=2|ZLEVEL=9',
            'EXTRA': QgsCoordinateReferenceSystem(crs),#atención asigna extra crs
            'OUTPUT': rutahillshade})
        # Agrega la capa rutahillshade
        caparaster=QgsRasterLayer(rutahillshade,'DSM_CCOMP_HILLSHADE.tif')
        QgsProject.instance().addMapLayer(caparaster,False) #aguanta la carga del raster
        root = QgsProject.instance().layerTreeRoot()    #se prepara el árbol de capas
        grupomapa=root.findGroup('DSM_CCOMP')           #localiza el grupo en el árbol
        grupomapa.insertLayer(-1, caparaster)               #inserta la capa raster al final del grupo
        iface.mapCanvas().refresh()                     # Refresca canvas

    def cargalidar(self,event):
        # Agrega la capa de puntos LAZ
        capapuntos = QgsVectorLayer(rutalidar, self.qlelidar.text())
        capapuntos.setCrs(crs)  #asigna el src a la capa
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

    def renombra(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutanubedtm = os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES/' + "DEM_CC_TERRENO.laz")
        rutanubedtmno = os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES/' + "DEM_NO_TERRENO.laz")
        rutanube = os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES/')

        for archivo in os.listdir(rutanube):
            rutaentrada = os.path.join(rutanube, archivo)
            if "offground" in archivo: # Verifica si el archivo tiene la cadena offground
                try:
                    os.rename(rutaentrada, rutanubedtmno)
                except:
                    pass

            if "ground" in archivo: # Verifica si el archivo tiene la cadena ground
                try:
                    os.rename(rutaentrada, rutanubedtm)
                except:
                    pass

    def elimina(self,event):
        proyecto = QgsProject.instance()
        nombre_subgrupo = "DSM_CCOMP"
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

    def ventanamensaje(self,letra,tam,titulo,cuerpo):
        mensaje = QMessageBox()
        font = QFont(letra, tam)  # Aquí puedes cambiar la fuente y el tamaño
        font.setBold(True)
        mensaje.setFont(font) #asigna la fuente de letra
        mensaje.setIcon(QMessageBox.Information) #de tipo informativo
        mensaje.setWindowTitle(titulo)
        mensaje.setText(cuerpo)
        mensaje.setStandardButtons(QMessageBox.Ok)
        resultado = mensaje.exec_()
