# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog
from qgis.PyQt import uic
import os
import webbrowser

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "ayuda.ui"))


class AyudaCombina(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(AyudaCombina, self).__init__(parent)
        self.setupUi(self)
        #boton pbManual
        self.pbManual.mousePressEvent = self.userManual
        self.pbCierra.mousePressEvent = self.cierra

    def userManual(self, event):
     #   pdf = os.path.join(os.path.dirname(os.path.dirname(__file__)), "usermanual_es.pdf")
        rutamanual=(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons', "MANUAL_USUARIO.pdf"))#ruta del manual en el plugin
        webbrowser.open(rutamanual)

    def cierra(self, event):
        self.close()

