# -*- coding: utf-8 -*-


from PyQt5.QtWidgets import QDialog

from qgis.PyQt import uic
import os
import webbrowser
from qgis.core import QgsProject

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "sketch.ui"))
class sketchfab(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(sketchfab, self).__init__(parent)
        self.setupUi(self)
        self.pbCierra.mousePressEvent = self.cierra
        self.pbabrecarpeta.clicked.connect(self.abre3d)
        self.pbweb3.clicked.connect(self.sketch)
        self.pbweb32.clicked.connect(self.sketch2)
        self.pbweb33.clicked.connect(self.sketch3)

    def cierra(self, event):
        self.close()
    def sketch(self,event):
        self.abrevisor(event)
        self.abre3d(event)

    def sketch2(self,event):
        self.abrevisor2(event)

    def sketch3(self,event):
        self.abrevisor3(event)

    def abre3d(self,event):
        rutactual = QgsProject.instance().homePath()  # ruta actual
        rutamodelo3d = (os.path.join(rutactual, 'ACB-MODELO3D/'))
        os.startfile(rutamodelo3d)  # abre la carpeta
    def abrevisor(self,event):
        self.abre3d(event)
        urldireccion = 'https://sketchfab.com/feed/'  # direccion url
        webbrowser.open(urldireccion,new=0,autoraise=True,) #intentará abrir la aplicación web

    def abrevisor2(self,event):
        urldireccion = 'https://labs.sketchfab.com/experiments/screenshots/'  # direccion url
        webbrowser.open(urldireccion,new=0,autoraise=True,) #intentará abrir la aplicación web

    def abrevisor3(self,event):
        urldireccion = 'https://labs.sketchfab.com/experiments/gif-export/'  # direccion url
        webbrowser.open(urldireccion,new=0,autoraise=True,) #intentará abrir la aplicación web




