# -*- coding: utf-8 -*-
#las librerias se importan a python en la consola osgeo4w shell
#teclenado python3 -m pip install pdal o cualquier otra libreria
# Ayuda de CloudCompare: https://www.cloudcompare.org/doc/wiki/index.php/Command_line_mode

from PyQt5.QtWidgets import QDialog
from qgis.PyQt import uic
import os

import subprocess

from qgis.core import QgsProject,QgsExpressionContextUtils
from qgis.PyQt.QtWidgets import QMessageBox

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "malla.ui"))

class FormularioMalla(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(FormularioMalla, self).__init__(parent)
        self.setupUi(self)
        self.btnccomp.mousePressEvent = self.scriptarchivo
        self.pbcierra.clicked.connect(self.cierraformulario)
        self.btnccomp.show() #muestra el boton pbpdal
        self.pbcierra.hide() #oculta el boton cierra
        self.pbrutacc.mousePressEvent = self.localizacc

        global malla,tipo_salida, ejecutable,rutacloudcompare,listanubes,rutanubes

        self.project = QgsProject.instance() #llamada a todas las variables del proyecto
        proj_variables = QgsExpressionContextUtils.projectScope(self.project)  # llamada a todas las variables del proyecto
        rutacloudcompare = str(proj_variables.variable('acbrutacc'))#llamada a la variable 'acbrutacc' en formato cadena
        self.lerutacc.setText(rutacloudcompare)
        ejecutable = str(proj_variables.variable('acbejecutable'))  # llamada a la variable 'acbejecutable' en formato cadena
        self.filecc.setFilePath(ejecutable) #asigna al QgsFileWidget la ruta de la variable ejecutable
        filtro = "Archivos ejecutables (*.exe);;Todos los archivos (*)"
        self.filecc.setFilter(filtro) #aplica el filtro para la ruta de cloudcompare solo exe
        self.pbactlista.clicked.connect(self.selecciona)  #llama a la funcion selecciona para cargar las nubes disponibles en la lista
        self.qlw_lista.clicked.connect(self.cogida)


    def scriptarchivo(self,event):
        # Rutas
        rutactual = QgsProject.instance().homePath() #ruta actual
        rutanube=(os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES'))
        rutapdal = (os.path.join(rutactual, 'ACB-DATOS'))                                       #ruta del json

        os.chdir(rutapdal) #cambia de directorio en la consola para crear el archivo bat

        #CloudCompare salida malla por extensión elegida
        if self.rbply.isChecked():#formato PLY
            exten="PLY"
        if self.rbbin.isChecked():#formato BIN
            exten="BIN"
        if self.rbstl.isChecked():#formato STL
            exten="STL"
        if self.rbobj.isChecked():#formato OBJ
            exten="OBJ"
        if self.rbvtk.isChecked():#formato VTK
            exten="VTK"
        if self.rbdxf.isChecked():#formato DXF
            exten="DXF"
        if self.rbfbx.isChecked():#formato FBX
            exten="FBX"
        if self.rboff.isChecked():#formato OFF
            exten="OFF"


        # Ayuda de CloudCompare: https://www.cloudcompare.org/doc/wiki/index.php/Command_line_mode


        # Establecer la variable de entorno PATH
        global  rutafilecc,ejecutable
        nube = str(self.qlw_lista.currentItem().text())
        os.environ["PATH"] = self.lerutacc.text() + ";" + os.environ["PATH"] #Posicionado en la ruta de CloudCompare
        rutafilecc=self.filecc.filePath() #ruta seleccionada en QgsFileWidget incluso archivo y extensión
        ejecutable=os.path.basename(rutafilecc) #solo nombre del ejecutable CloudCompare.exe

        #rasteriza NUBEUNIDA
        comandocc = [
            ejecutable,
            "-AUTO_SAVE OFF",
            "-O",
            "-GLOBAL_SHIFT AUTO",
            nube,
            # MALLA DELAUNAY MESH NUBEUNIDA PASA A DSM_MALLA
            "-DELAUNAY -AA",  # Triangulación de Delaunay en plano XY
            "-MAX_EDGE_LENGTH 50.0",  # Lado del triangulo máximo para interpolar
            "-M_EXPORT_FMT " + exten + " -EXT " + exten,
            # cambia el formato para exportar la malla BIN, OBJ, PLY, STL, VTK, MA, FBX.
            "-SAVE_MESHES FILE ../ACB-CAPAS/ACB_MALLAS/" + self.qlelidar.text() + "." + exten,  # exporta la malla
        ]
        subprocess.run(" ".join(comandocc), shell=True)

        QMessageBox.information(None, 'Proceso Malla Terminado',
                                'Malla Generada')
        self.btnccomp.hide()
        self.pbcierra.show()
        self.close()
        #ABRE LA CARPETA MALLAS
        rutactual5 = QgsProject.instance().homePath()  # ruta actual
        rutafolder5 = (os.path.join(rutactual5, 'ACB-CAPAS/ACB_MALLAS/'))
        os.startfile(rutafolder5)  # abre la carpeta
        self.abreccomparemalla(event)  # abre la función para iniciar cloudcompare y abrir todas las mallas


    def selecciona(self,event):
        # CREA LA LISTA CON LA RUTA RELATIVA ./NUBEPUNTOS/NOMBRE DE LA NUBE.laz o las
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutanubes = (os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES'))   # Ruta de la carpeta con todas las nubes de puntos
        listanubes=[]    # Lista para almacenar los nombres de archivos de puntos
        lista_archivos = os.listdir(rutanubes)   # la lista de archivos en la carpeta

        self.qlw_lista.clear()  # borra el contenido de la lista
        # Itera sobre la lista de archivos y filtra los que terminan en ".las" o ".laz"
        for archivo in lista_archivos:
            if archivo.endswith(".las") or archivo.endswith(".laz") or archivo.endswith(".LAZ") or archivo.endswith(".LAS"):
                listanubes.append(os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES/' + archivo))
        self.qlw_lista.addItems(listanubes)  # añade el contenido de la lista al combo

        self.repaint()
    def cogida(self,event):
        nube=str(self.qlw_lista.currentItem().text())
        self.qlseleccionada.setText(nube) #pon en el label la seleccion

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

    def abreccomparemalla(self,event):
        rutactual2 = QgsProject.instance().homePath()  # ruta actual
        rutacarpeta2 = (os.path.join(rutactual2, 'ACB-CAPAS/ACB_MALLAS/'))
        # Lista para almacenar las rutas completas de los archivos
        command = [ejecutable]
        # Iterar sobre los archivos en la carpeta
        try:
            for nombre_archivo in os.listdir(rutacarpeta2):
                ruta_completa = os.path.join(rutacarpeta2, nombre_archivo)# Obtener la ruta completa del archivo
                if ".laz" or ".bin" or ".stl" or ".obj" or ".vtk" or ".dxf" or ".fbx" or ".off" in nombre_archivo:# Verificar si es un archivo (no un directorio)
                    command.append(ruta_completa)# Agregar la ruta completa a la lista
                else: pass
            subprocess.Popen(command)
        except: pass