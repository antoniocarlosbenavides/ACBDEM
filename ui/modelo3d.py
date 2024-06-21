# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog
from qgis.PyQt import uic

import os
import subprocess
from PyQt5.QtCore import QUrl
import webbrowser
from qgis.core import QgsProject


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "modelo3d.ui"))
class modelo3dclass(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(modelo3dclass, self).__init__(parent)
        self.setupUi(self)
        self.pbCierra.mousePressEvent = self.cierra
        self.pbabrecarpeta.clicked.connect(self.abrefolder3d)
        self.pbweb2.clicked.connect(self.viewergltf)

    def cierra(self, event):
        self.close()

    def viewergltf(self,event):

        #abre url con esta direccion y abre la carpeta para lanzar el modelo a la web
        #https://gltf-viewer.donmccurdy.com/
        self.abrevisorgltf(event)
        self.abrefolder3d(event)

    def abrefolder3d(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutamodelo3d = (os.path.join(rutactual, 'ACB-MODELO3D/'))
        os.startfile(rutamodelo3d)  # abre la carpeta
    def abrevisorgltf(self,event):
        #self.abrefolder3d(event) #abre la carpeta de destino de archivos en windows
        urldireccion = 'https://gltf-viewer.donmccurdy.com/'  # direccion url del visor 3d gltf
        webbrowser.open(urldireccion,new=0,autoraise=True,) #intentará abrir la aplicación web




