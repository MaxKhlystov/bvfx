# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Pedestrian Accessibility Plugin
                                 A QGIS plugin
 Builds anisotropic pedestrian isochrones considering elevation changes
 ***************************************************************************/
"""

import os
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis
from .test_plugin_dialog import TestPluginDialog


class TestPlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = 'Pedestrian Accessibility'
        self.first_start = True

    def initGui(self):
        """Create the menu entries and toolbar icons."""
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        
        self.action = QAction(
            QIcon(icon_path),
            "Pedestrian Accessibility",
            self.iface.mainWindow()
        )
        self.action.triggered.connect(self.run)
        
        self.iface.addPluginToMenu(self.menu, self.action)
        self.iface.addToolBarIcon(self.action)
        self.actions.append(self.action)

    def unload(self):
        """Remove the plugin menu item and icon."""
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """Run method that performs all the real work."""
        if self.first_start:
            self.first_start = False
            self.dlg = TestPluginDialog()
        
        # Показать диалог
        self.dlg.show()
        result = self.dlg.exec_()
        
        if result:
            self.process_data()

    def process_data(self):
        try:
            from qgis.core import QgsVectorLayer
            import tempfile
            import geopandas as gpd
            import numpy as np
            from shapely.geometry import Point, LineString, Polygon
            
            # Получаем данные из диалога - ИСПРАВЛЕНО!
            points_layer = self.dlg.comboBox_points.currentData()
            isolines_layer = self.dlg.comboBox_isolines.currentData()
            citizens_layer = self.dlg.comboBox_citizens.currentData()
            
            if not all([points_layer, isolines_layer, citizens_layer]):
                QMessageBox.warning(self.dlg, "Ошибка", "Выберите все три слоя!")
                return
            
            # Получаем остальные параметры - если они есть в вашем UI
            try:
                # Эти элементы должны быть в вашем .ui файле
                ids_str = self.dlg.lineEdit_ids.text()
                radius_text = self.dlg.lineEdit_radius.text()
            except AttributeError:
                # Если элементов нет, используем значения по умолчанию
                ids_str = "251, 250, 252, 869"
                radius_text = "1000"
            
            # Продолжаем обработку...
            temp_dir = tempfile.gettempdir()
            
            points_path = os.path.join(temp_dir, "points.shp")
            isolines_path = os.path.join(temp_dir, "isolines.shp")
            citizens_path = os.path.join(temp_dir, "citizens.shp")
            
            # Сохраняем слои во временные файлы
            self.save_layer_to_shapefile(points_layer, points_path)
            self.save_layer_to_shapefile(isolines_layer, isolines_path)
            self.save_layer_to_shapefile(citizens_layer, citizens_path)
            
            # Получаем радиус
            base_radius = float(radius_text)
            
            # Читаем данные
            points = gpd.read_file(points_path)
            isolines = gpd.read_file(isolines_path)
            citizens = gpd.read_file(citizens_path)
            
            # Приводим к одной CRS
            points = points.to_crs(isolines.crs)
            citizens = citizens.to_crs(isolines.crs)
            
            # Получаем ID точек для обработки
            if ids_str:
                ids_to_process = [int(x.strip()) for x in ids_str.split(',')]
            else:
                # Если не указаны, берем все
                id_field = "NO"  # По умолчанию
                ids_to_process = points[id_field].tolist() if id_field in points.columns else []
            
            # Параметры
            angle_step = 20
            penalty_per_5m = 25.0
            unit_factor = penalty_per_5m / 5.0
            min_radius_factor = 0.1
            
            all_polygons = []
            all_ids = []
            all_citizens = []
            
            # Функция для пересечений
            def intersections_along_ray(ray, isolines_gdf, origin):
                inter = isolines_gdf.intersection(ray)
                inter = inter[~inter.is_empty]
                results = []
                for idx, geom in inter.items():
                    pts = []
                    if geom.geom_type == "Point":
                        pts = [geom]
                    else:
                        try:
                            pts = [g for g in geom.geoms if g.geom_type == "Point"]
                        except Exception:
                            pts = []
                    for p in pts:
                        dist = origin.distance(p)
                        height = isolines_gdf.loc[idx, "VALUE"]
                        results.append((dist, float(height)))
                results.sort(key=lambda x: x[0])
                return results
            
            # Обработка каждой точки
            for point_id in ids_to_process:
                row = points[points["NO"] == point_id]
                if row.empty:
                    continue
                target = row.geometry.iloc[0]
                
                result_points = []
                max_ray_length = base_radius * 3
                
                for angle in range(0, 360, angle_step):
                    rad = np.radians(angle)
                    dx = np.cos(rad)
                    dy = np.sin(rad)
                    
                    far_pt = Point(target.x + dx * max_ray_length, target.y + dy * max_ray_length)
                    ray = LineString([target, far_pt])
                    
                    hits = intersections_along_ray(ray, isolines, target)
                    
                    if not hits:
                        final_r = base_radius
                    else:
                        heights = [h for (_, h) in hits]
                        if len(heights) == 1:
                            total_reduction = 0.0
                        else:
                            total_reduction = 0.0
                            for j in range(1, len(heights)):
                                dh = abs(heights[j] - heights[j - 1])
                                total_reduction += dh * unit_factor
                        final_r = max(base_radius - total_reduction, base_radius * min_radius_factor)
                    
                    end_pt = Point(target.x + dx * final_r, target.y + dy * final_r)
                    result_points.append(end_pt)
                
                anisotropic_polygon = Polygon([[p.x, p.y] for p in result_points])
                all_polygons.append(anisotropic_polygon)
                all_ids.append(point_id)
                
                houses_inside = citizens[citizens.intersects(anisotropic_polygon)]
                population_sum = houses_inside["Насел"].sum() if "Насел" in houses_inside.columns else 0
                all_citizens.append(int(population_sum))
            
            # Сохраняем результат
            output_dir = temp_dir  # или задайте другую папку
            output_path = os.path.join(output_dir, "anisotropic_polygon.shp")
            
            buffers_gdf = gpd.GeoDataFrame(
                {"id": all_ids, "citizens": all_citizens},
                geometry=all_polygons,
                crs=isolines.crs
            )
            buffers_gdf.to_file(output_path)
            
            # Добавляем слой в QGIS
            layer = QgsVectorLayer(output_path, "Pedestrian Accessibility", "ogr")
            QgsProject.instance().addMapLayer(layer)
            
            # Пересечения
            intersection_polygons = []
            pair_ids = []
            pair_citizens = []
            
            n = len(all_polygons)
            for i in range(n):
                for j in range(i + 1, n):
                    poly1 = all_polygons[i]
                    poly2 = all_polygons[j]
                    if not poly1.intersects(poly2):
                        continue
                    inter = poly1.intersection(poly2)
                    if inter.is_empty or inter.area == 0:
                        continue
                    pair_label = f"{all_ids[i]}_{all_ids[j]}"
                    
                    houses_in_inter = citizens[citizens.intersects(inter)]
                    pop_inter = houses_in_inter["Насел"].sum() if "Насел" in houses_in_inter.columns else 0
                    
                    intersection_polygons.append(inter)
                    pair_ids.append(pair_label)
                    pair_citizens.append(int(pop_inter))
            
            if intersection_polygons:
                inter_path = os.path.join(output_dir, "anisotropic_polygon_intersections.shp")
                inter_gdf = gpd.GeoDataFrame(
                    {"pair": pair_ids, "citizens": pair_citizens},
                    geometry=intersection_polygons,
                    crs=isolines.crs
                )
                inter_gdf.to_file(inter_path)
                
                # Добавляем слой пересечений
                inter_layer = QgsVectorLayer(inter_path, "Accessibility Intersections", "ogr")
                QgsProject.instance().addMapLayer(inter_layer)
            
            QMessageBox.information(self.dlg, "Готово", 
                                  f"Обработка завершена!\n"
                                  f"Создано полигонов: {len(all_polygons)}\n"
                                  f"Результат сохранен в: {output_path}")
            
        except Exception as e:
            QMessageBox.critical(self.dlg, "Ошибка", f"Ошибка обработки:\n{str(e)}")
            import traceback
            QgsMessageLog.logMessage(f"Ошибка: {str(e)}\n{traceback.format_exc()}", "Pedestrian Accessibility", Qgis.Critical)

    def save_layer_to_shapefile(self, layer, path):
        """Сохраняет слой QGIS в shapefile"""
        from qgis.core import QgsVectorFileWriter
        
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "ESRI Shapefile"
        options.fileEncoding = "UTF-8"
        
        error = QgsVectorFileWriter.writeAsVectorFormatV2(
            layer,
            path,
            QgsProject.instance().transformContext(),
            options
        )
        
        if error[0] != QgsVectorFileWriter.NoError:
            raise Exception(f"Ошибка сохранения слоя: {error[1]}")