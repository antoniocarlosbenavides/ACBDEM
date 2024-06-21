# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog
from qgis.PyQt import uic
import os
import webbrowser

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "veninicio.ui"))


class VentanaInicio(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(VentanaInicio, self).__init__(parent)
        self.setupUi(self)

        #boton pbManual
        self.LB_MUNDO.mousePressEvent = self.cierra

    def cierra(self,event):
        self.close()