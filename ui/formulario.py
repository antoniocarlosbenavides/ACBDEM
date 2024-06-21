# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog
from qgis.PyQt import uic
import os
import webbrowser

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "formulario.ui"))
class FormularioBase(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(FormularioBase, self).__init__(parent)
        self.setupUi(self)

        self.pbCierra.mousePressEvent = self.cierra

    def cierra(self, event):
        self.close()


