# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog
from qgis.PyQt import uic
import os
import webbrowser

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "about.ui"))


class Acercade(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(Acercade, self).__init__(parent)
        self.setupUi(self)
        #solo dos botones de enlace a url y a un pdf
        self.lbusal.mousePressEvent = self.linkUsal
        self.pbManual.mousePressEvent = self.userManual
        self.pbCierra.mousePressEvent = self.cierra

    def linkUsal(self, event):
        url="https://www.usal.es/master-geotecnologias-cartograficas-en-ingenieria-y-arquitectura"
        webbrowser.open(url)

    def userManual(self, event):
     #   pdf = os.path.join(os.path.dirname(os.path.dirname(__file__)), "usermanual_es.pdf")
        rutamanual=(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons', "MANUAL_USUARIO.pdf"))#ruta del manual en el plugin
        webbrowser.open(rutamanual)

    def cierra(self, event):
        self.close()

