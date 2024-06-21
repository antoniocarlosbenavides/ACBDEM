# -*- coding: utf-8 -*-
#las librerias se importan a python en la consola osgeo4w shell
#teclenado python3 -m pip install pdal o cualquier otra libreria

from PyQt5.QtWidgets import QDialog, QMessageBox, QApplication
from qgis.PyQt import uic
from PyQt5.QtGui import QFont, QColor, QPixmap
import os
import time
import subprocess
from qgis.core import QgsProject,QgsExpressionContextUtils

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "estad.ui"))


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

class FormularioEstadistica(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(FormularioEstadistica, self).__init__(parent)
        self.setupUi(self)
        self.pbcalcula.mousePressEvent = self.previo
        self.pbCierra.mousePressEvent = self.cierra

        global rutafilecc, ejecutable, rutacloudcompare, rutactual, rutapdal, rutamascara, rutanube, rutacloud, rutacloud1, rutafoto
        self.project = QgsProject.instance() #llamada a todas las variables del proyecto
        proj_variables = QgsExpressionContextUtils.projectScope(self.project)  # llamada a todas las variables del proyecto
        rutacloudcompare = str(proj_variables.variable('acbrutacc'))#llamada a la variable 'acbrutacc' en formato cadena
        self.lerutacc.setText(rutacloudcompare)
        ejecutable = str(proj_variables.variable('acbejecutable'))  # llamada a la variable 'acbejecutable' en formato cadena
        self.filecc.setFilePath(ejecutable) #asigna al QgsFileWidget la ruta de la variable ejecutable
        filtro = "Archivos ejecutables (*.exe);;Todos los archivos (*)"
        self.filecc.setFilter(filtro) #aplica el filtro para la ruta de cloudcompare solo exe

        rutactual = QgsProject.instance().homePath() #ruta actual
        rutanube=(os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES'))
        rutapdal = (os.path.join(rutactual, 'ACB-DATOS'))                                       #ruta del json
        rutamascara = (os.path.join(rutactual, 'ACB-CAPAS', "MASCARA.gpkg"))                    #ruta de la máscara
        rutanube=(os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES'))
        rutacloud = (os.path.join(rutactual, 'ACB-CAPAS/ACB_NUBES/NUBE.laz'))

        os.chdir(rutapdal) #cambia de directorio en la consola para crear el archivo bat


    def previo(self, event):
        self.selecciona(event)  # llama a la funcion selecciona para seleccionar la nube de puntos
        #barra de progreso
        self.barra.show = True
        self.cambialetra("Arial","black",8) #llama a la funcionpara cambiar tipo letra, color y tamaño del QLabel
        self.barraprogreso(5, 0, "☻ Declaración de rutas")
        self.barraprogreso(15,5, "☺ Vamos a dar un Paseo por las Nubes \nExtensión de la capa MASCARA")

        # Calcula la extensión de la capa máscara
        capas_corte = QgsProject.instance().mapLayersByName("MASCARA")
        if capas_corte:
            capa_corte = capas_corte[0]
        extension = capa_corte.extent()
        # COORDENADAS DE EXTENSIÓN DE LA CAPA
        x1 = extension.xMinimum()-50
        y1 = extension.yMinimum()-50
        x2 = extension.xMaximum()+50
        y2 = extension.yMaximum()+50

        self.barraprogreso(25, 15, "☻ Posicionando el ejecutable en la ruta de Cloud Compare")

        # Establecer la variable de entorno PATH
        os.environ["PATH"] = self.lerutacc.text() + ";" + os.environ["PATH"]  # Posicionado en la ruta de CloudCompare
        rutafilecc = self.filecc.filePath()  # ruta seleccionada en QgsFileWidget incluso archivo y extensión
        ejecutable = os.path.basename(rutafilecc)  # solo nombre del ejecutable CloudCompare.exe

        # Información delos procesos del siguiente bloque Unión Filtros y Selección 2 a 11
        self.cambialetra("Arial Black", "green", 10)
        self.lbproceso3.setText("Un paseo por las Nubes")
        self.barraprogreso(30, 25, "☺ Cargando el archivo ejecutable comandocc")
        rutafoto = 'snow.png'; self.imagen(rutafoto)  # aparece la nube azul snow.png
        self.barraprogreso(45, 30, "☻ Uniendo las nubes operación Merge")
        rutafoto = 'snow2.png'; self.imagen(rutafoto) #aparece la nube gris snow2.png
        self.barraprogreso(50, 45, "☺ Eliminando Puntos Concentrados SOR 15 1")
        rutafoto = 'snow.png'; self.imagen(rutafoto)  # aparece la nube azul snow.png
        self.barraprogreso(55, 50, "☻ Eliminando puntos no clasificados 0 a 1")
        rutafoto = 'snow2.png'; self.imagen(rutafoto)  # aparece la nube gris snow2.png
        self.barraprogreso(65, 55, "☺ Eliminando Puntos de solape clasificados 12 en adelante")
        rutafoto = 'snow.png'; self.imagen(rutafoto)  # aparece la nube azul snow.png

        # Comando de CloudCompare une nubes
        comandocc = [
            ejecutable,  # Ejecuta cloudcompare aunque no lo abre
            "-SILENT",
            "-LOG_FILE ../ACB-CAPAS/ACB_NUBES/infoproceso.txt",  # registra los procesos en un archivo
            "-AUTO_SAVE OFF",  # Neutraliza que adopte el nombre del resultado automatico
        ]
        # Agregar cada archivo LAZ al comando denominado comandocc
        conta = 0
        for archivo_laz in listanubes:
            conta += 1
            if conta == 1:
                comandocc.extend(["-O", "-GLOBAL_SHIFT AUTO",
                                  f'"{archivo_laz}"'])  # -O esto es open, abre el archivo en AUTO solo el primero es AUTO
            else:
                comandocc.extend(["-O", "-GLOBAL_SHIFT FIRST",
                                  f'"{archivo_laz}"'])  # -O esto es open, abre el archivo en FIRST siguiendo al primero
        # Union de nubes MERGE
        comandocc.extend([
            "-NO_TIMESTAMP",  # Evita marcas de tiempo en el nombre del archivo de salida
            "-SOR 15 4", # Filtro elimina puntos si menos de 15 están a la distancia media 4m ponderado 1xdesv tipica
            "-MERGE_CLOUDS",  # une todas las nubes
            "-SET_ACTIVE_SF Classification",
            "-FILTER_SF 2 11",# filtra por campos escalar Classification no deseable ruido 7 y 18 solapes 12
            "-C_EXPORT_FMT LAS -EXT LAZ",  # cambia el formato para exportar nube a laz
            "-SAVE_CLOUDS FILE ../ACB-CAPAS/ACB_NUBES/NUBE.laz"])   # exporta la nube DSM a laz

        # Informacion
        rutafoto = 'snow2.png';self.imagen(rutafoto)  # aparece la nube gris snow2.png
        self.cambialetra("Arial Black", "blue",10)  # llama a la funcionpara cambiar tipo letra, color y tamaño del QLabel
        self.barraprogreso(85, 65, "☻ Recorta la Nube contra MASCARA")

        # Recorta la union de nubes de puntos contra la MASCARA y lo llama NUBE.laz
        comandocc.extend([
            "-CLEAR",
            "-AUTO_SAVE OFF",
            "-O", "-GLOBAL_SHIFT 0 0 0 ../ACB-CAPAS/ACB_NUBES/NUBE.laz", #Abre con origen coord 0 0 0
            "-SET_GLOBAL_SHIFT 0 0 0", # nubes posteriores entrarían con 0 0 0
            "-KEEP_ORIG_FIXED",
            #Recorta con CROP2D usando los vértices de un cuadrado envolvente de la máscara
            "-CROP2D Z 4 "+str(x1) + ' ' + str(y1) + ' ' + str(x2) + ' ' + str(y1) + ' ' + str(x2) + ' ' + str(y2) + ' ' + str(x1) + ' ' + str(y2),
            "-C_EXPORT_FMT LAS -EXT LAZ",  # cambia el formato para exportar nube a laz
            "-SAVE_CLOUDS FILE ../ACB-CAPAS/ACB_NUBES/NUBE.laz"])  # exporta la nube DSM a laz

        rutafoto = 'snow.png'; self.imagen(rutafoto)  # aparece la nube azul snow.png
        self.barraprogreso(90, 85, "☺ Crea el Campo Escalar Z en la nube")
        rutafoto = 'snow2.png'; self.imagen(rutafoto)  # aparece la nube gris snow2.png
        self.barraprogreso(98, 90, "☻ Genera el Escalar Coord. Z Para Histograma Campana Gauss")

        # CREA EL CAMPO ESCALAR Z y Guarda la NUBE.laz
        comandocc.extend([
            "-CLEAR",
            "-AUTO_SAVE OFF",
            "-O", "-GLOBAL_SHIFT AUTO ../ACB-CAPAS/ACB_NUBES/NUBE.laz",
            #"-RDP 0.25",  # Elimina puntos a menos de 25cm de distancia
            "-COORD_TO_SF Z", #Exporta cota Z a un campo escalar (SF) Coord. Z
            "-SAVE_CLOUDS FILE ../ACB-CAPAS/ACB_NUBES/NUBE.laz",
            #"-DELAUNAY", # Malla Delaunay triangulación
            #"-MAX_EDGE_LENGTH 50",
            #"-SAVE_CLOUDS FILE ../ACB-CAPAS/ACB_NUBES/DELAUNAY.laz",
            "-STAT_TEST GAUSS"

            "-CLEAR"
        ])

        # Ejecuta la consola llamando a CloudCompare con el archivo json comandocc
        subprocess.run(" ".join(comandocc), shell=True)

        #Informacion
        rutafoto = 'snow.png'; self.imagen(rutafoto)  # aparece la nube azul snow.png
        self.barraprogreso(101, 98, "☺ Guardando Nube")
        self.lbproceso1.setText("                          ☺ Proceso Previo Finalizado ☻")

        # Abre CloudCompare
        rutafoto = 'snow2.png'; self.imagen(rutafoto)  # aparece la nube gris snow2.png
        self.abreccompare(rutacloud) #abre la función para iniciar cloudcompare y abrir el archivo de la nube
        self.cambialetra("Arial Black","blue",12) #llama a la funcionpara cambiar tipo letra, color y tamaño del QLabel
        QMessageBox.information(None,"Fin Creación Nube",f"Se abrirá CloudCompare con la nube\n {rutacloud}\n Apply all\n Yes to all \n Si da error se abre cloudcompare a mano")
        self.lbproceso3.setText(f"Abrir CloudCompare con la nube\n {rutacloud}\n Apply all\n Yes to all \n Sigue el video ☺")
        self.cambialetra("Arial Black", "red", 10)
        self.repaint()

        #Tiempo para lectura de 5segundos y cierre
        time.sleep(5)
        self.close()


    def selecciona(self,event):
        # CREA LA LISTA CON LA RUTA RELATIVA ./NUBEPUNTOS/NOMBRE DE LA NUBE.laz o las
        global listanubes, rutanubes
        rutanubes = (os.path.join(rutactual, 'ACB-DATOS/NUBEPUNTOS'))   # Ruta de la carpeta con todas las nubes de puntos
        listanubes=[]    # Lista para almacenar los nombres de archivos de puntos
        lista_archivos = os.listdir(rutanubes)   # directorio con todos los archivos en rutanubes
        # Itera sobre la lista de archivos y filtra los que terminan en ".las" o ".laz"

        for archivo in lista_archivos: #para cada archivo contenido en la carpeta
            if archivo.endswith(".las") or archivo.endswith(".laz") or archivo.endswith(".LAZ") or archivo.endswith(".LAS") or archivo.endswith(".bin"):
                listanubes.append(os.path.join(rutactual, 'ACB-DATOS/NUBEPUNTOS/' + archivo))
                self.lbproceso3.setText("\n".join(listanubes))#actualiza lbproceso con la lista

        self.repaint()



    def cierra(self, event):
        self.close()

    def barraprogreso(self,tope,contador,mensaje):
        self.lbproceso1.setText(mensaje)
        while contador <= tope:
            time.sleep(0.2)
            self.barra.setValue(contador);contador += 1

    def abreccompare(self,nubeabrir):
        rutafilecc = self.filecc.filePath()
        try:
            command = [rutafilecc, nubeabrir]
            subprocess.Popen(command)
        except:
            pass

    def cambialetra(self,tipoletra,colorletra,tamaño):
        # Cambiando el tamaño de la fuente y el color del QLabel lbproceso3
        font = QFont(tipoletra, tamaño)  # Estableciendo la fuente y tamaño
        color = QColor(colorletra)  # Estableciendo el color del texto
        self.lbproceso3.setFont(font)
        self.lbproceso3.setStyleSheet("color: {}".format(color.name()))  # Aplicando el color

    def cambialetra(self,tipoletra,colorletra,tamaño):
        # Cambiando el tamaño de la fuente y el color del QLabel lbproceso3
        font = QFont(tipoletra, tamaño)  # Estableciendo la fuente y tamaño
        color = QColor(colorletra)  # Estableciendo el color del texto
        self.lbproceso3.setFont(font)
        self.lbproceso3.setStyleSheet("color: {}".format(color.name()))  # Aplicando el color

    def imagen(self,rutafoto):
        rutafoto2=(os.path.join(os.path.dirname(__file__), rutafoto))
        pixmap=QPixmap(rutafoto2)
        self.lbproceso3.setPixmap(pixmap)
        self.lbproceso3.repaint()
        self.repaint()
