# -*- coding: utf-8 -*-

from qgis.PyQt import QtCore, QtGui, QtWidgets
from qgis.core import QgsProject


class Ui_TestPluginDialog(object):
    def setupUi(self, TestPluginDialog):
        TestPluginDialog.setObjectName("TestPluginDialog")
        TestPluginDialog.resize(450, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(TestPluginDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        
        # Группа выбора точек
        self.groupBox_points = QtWidgets.QGroupBox(TestPluginDialog)
        self.groupBox_points.setObjectName("groupBox_points")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox_points)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.comboBox_points = QtWidgets.QComboBox(self.groupBox_points)
        self.comboBox_points.setObjectName("comboBox_points")
        self.verticalLayout_2.addWidget(self.comboBox_points)
        self.verticalLayout.addWidget(self.groupBox_points)
        
        # Группа выбора изолиний
        self.groupBox_isolines = QtWidgets.QGroupBox(TestPluginDialog)
        self.groupBox_isolines.setObjectName("groupBox_isolines")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox_isolines)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.comboBox_isolines = QtWidgets.QComboBox(self.groupBox_isolines)
        self.comboBox_isolines.setObjectName("comboBox_isolines")
        self.verticalLayout_3.addWidget(self.comboBox_isolines)
        self.verticalLayout.addWidget(self.groupBox_isolines)
        
        # Группа выбора населения
        self.groupBox_citizens = QtWidgets.QGroupBox(TestPluginDialog)
        self.groupBox_citizens.setObjectName("groupBox_citizens")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.groupBox_citizens)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.comboBox_citizens = QtWidgets.QComboBox(self.groupBox_citizens)
        self.comboBox_citizens.setObjectName("comboBox_citizens")
        self.verticalLayout_4.addWidget(self.comboBox_citizens)
        self.verticalLayout.addWidget(self.groupBox_citizens)
        
        # Группа ID точек
        self.groupBox_ids = QtWidgets.QGroupBox(TestPluginDialog)
        self.groupBox_ids.setObjectName("groupBox_ids")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.groupBox_ids)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.lineEdit_ids = QtWidgets.QLineEdit(self.groupBox_ids)
        self.lineEdit_ids.setObjectName("lineEdit_ids")
        self.lineEdit_ids.setPlaceholderText("251, 250, 252, 869 (через запятую)")
        self.verticalLayout_5.addWidget(self.lineEdit_ids)
        self.verticalLayout.addWidget(self.groupBox_ids)
        
        # Группа радиуса
        self.groupBox_radius = QtWidgets.QGroupBox(TestPluginDialog)
        self.groupBox_radius.setObjectName("groupBox_radius")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.groupBox_radius)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEdit_radius = QtWidgets.QLineEdit(self.groupBox_radius)
        self.lineEdit_radius.setObjectName("lineEdit_radius")
        self.lineEdit_radius.setText("1000")
        self.horizontalLayout.addWidget(self.lineEdit_radius)
        self.label_radius = QtWidgets.QLabel(self.groupBox_radius)
        self.label_radius.setObjectName("label_radius")
        self.label_radius.setText("метров")
        self.horizontalLayout.addWidget(self.label_radius)
        self.verticalLayout.addWidget(self.groupBox_radius)
        
        # Кнопки
        self.buttonBox = QtWidgets.QDialogButtonBox(TestPluginDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(TestPluginDialog)
        self.buttonBox.accepted.connect(TestPluginDialog.accept)
        self.buttonBox.rejected.connect(TestPluginDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(TestPluginDialog)

    def retranslateUi(self, TestPluginDialog):
        _translate = QtCore.QCoreApplication.translate
        TestPluginDialog.setWindowTitle(_translate("TestPluginDialog", "Pedestrian Accessibility"))
        self.groupBox_points.setTitle(_translate("TestPluginDialog", "Точки (остановки)"))
        self.groupBox_isolines.setTitle(_translate("TestPluginDialog", "Изолинии (высоты)"))
        self.groupBox_citizens.setTitle(_translate("TestPluginDialog", "Население (дома)"))
        self.groupBox_ids.setTitle(_translate("TestPluginDialog", "ID точек для обработки"))
        self.groupBox_radius.setTitle(_translate("TestPluginDialog", "Радиус доступности"))


class TestPluginDialog(QtWidgets.QDialog, Ui_TestPluginDialog):
    def __init__(self, parent=None):
        super(TestPluginDialog, self).__init__(parent)
        self.setupUi(self)
        # Заполняем комбобоксы слоями ПРИ СОЗДАНИИ диалога
        self.load_layers()
    
    def load_layers(self):
        """Заполняет комбобоксы доступными векторными слоями из проекта"""
        layers = QgsProject.instance().mapLayers().values()
        
        # Очищаем комбобоксы
        self.comboBox_points.clear()
        self.comboBox_isolines.clear()
        self.comboBox_citizens.clear()
        
        # Добавляем только векторные слои
        for layer in layers:
            if layer.type() == 0:  # 0 = векторный слой
                layer_name = layer.name()
                self.comboBox_points.addItem(layer_name, layer)
                self.comboBox_isolines.addItem(layer_name, layer)
                self.comboBox_citizens.addItem(layer_name, layer)