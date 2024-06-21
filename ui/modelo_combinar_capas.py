from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterMultipleLayers
from qgis.core import QgsCoordinateReferenceSystem
import processing


class modelo_combinar(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterMultipleLayers('entradas_de_capas', 'Entradas de capas', layerType=QgsProcessing.TypeVectorPoint, defaultValue=None))

    def combinarcapas(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        # Combinar capas vectoriales
        alg_params = {
            'CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'LAYERS': parameters['entradas_de_capas'],
            'OUTPUT': 'ogr:dbname=\'C:/ACBQGIS/QGIS_GUAD1/ACB-CAPAS/ACB-CAPAS_BASE/COMBINADO2306JUNIO.gpkg\' table="Combinado" (geom)',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CombinarCapasVectoriales'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Cargar capa en el proyecto
        alg_params = {
            'INPUT': outputs['CombinarCapasVectoriales']['OUTPUT'],
            'NAME': 'salidacombinada'
        }
        outputs['CargarCapaEnElProyecto'] = processing.run('native:loadlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'MODELO_COMBINAR'

    def displayName(self):
        return 'MODELO_COMBINAR'

    def group(self):
        return 'GRUPO_CAPAS'

    def groupId(self):
        return 'GRUPO_CAPAS'

    def createInstance(self):
        return Modelo_combinar()
