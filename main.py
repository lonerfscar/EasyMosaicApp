import sys
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QMenu,
                             QAction, QFileDialog, QSizeGrip)
from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtGui import QPixmap, QPainter, QColor, QIcon, QTransform


class EasyMosaicApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initVariables()
        self.initUI()
        self.loadPresets()

    def initVariables(self):
        self.dragging = False
        self.drag_position = QPoint()
        self.always_on_top = True
        self.fill_mode = "mosaic"
        self.custom_image = None
        self.presets = {}
        self.mosaic_opacity = 1.0
        self.mirror_horizontal = False
        self.mirror_vertical = False
        self.setWindowTitle("EasyMosaicApp")
        self.preset_dir = "present"
        if not os.path.exists(self.preset_dir):
            os.makedirs(self.preset_dir)

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(200, 150)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.updateContent()
        self.size_grip = QSizeGrip(self)
        self.size_grip.setFixedSize(15, 15)
        self.setGeometry(100, 100, 400, 300)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        if os.path.exists("app_icon.ico"):
            self.setWindowIcon(QIcon("app_icon.ico"))

    def resizeEvent(self, event):
        self.label.resize(self.size())
        self.size_grip.move(self.width() - 15, self.height() - 15)
        self.updateContent()
        super().resizeEvent(event)

    def updateContent(self):
        if self.fill_mode == "mosaic":
            self.showMosaic()
        elif self.fill_mode == "image" and self.custom_image:
            self.showCustomImage()
        else:
            self.label.clear()
            self.label.setStyleSheet("background-color: transparent;")

    def showMosaic(self):
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setOpacity(self.mosaic_opacity)
        block_size = 20
        for y in range(0, self.height(), block_size):
            for x in range(0, self.width(), block_size):
                color = QColor(200, 200, 200) if (x // block_size + y // block_size) % 2 == 0 else QColor(150, 150, 150)
                painter.fillRect(x, y, block_size, block_size, color)
        painter.end()
        self.label.setPixmap(pixmap)

    def showCustomImage(self):
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        transformed = self.custom_image
        if self.mirror_horizontal:
            transformed = transformed.transformed(QTransform().scale(-1, 1))
        if self.mirror_vertical:
            transformed = transformed.transformed(QTransform().scale(1, -1))
        scaled = transformed.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()
        self.label.setPixmap(pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.RightButton:
            self.showContextMenu(event.pos())

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def closeEvent(self, event):
        super().closeEvent(event)
        QApplication.quit()

    def loadPresets(self):
        self.presets = {}
        for filename in os.listdir(self.preset_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                filepath = os.path.join(self.preset_dir, filename)
                self.presets[filename] = QPixmap(filepath)

    def showContextMenu(self, position):
        menu = QMenu(self)
        fill_menu = menu.addMenu("填充内容")
        mosaic_action = fill_menu.addAction("马赛克")
        mosaic_action.triggered.connect(lambda: self.setFillMode("mosaic"))
        image_action = fill_menu.addAction("选择图片")
        image_action.triggered.connect(self.selectImage)
        if self.presets:
            preset_menu = fill_menu.addMenu("预设图片")
            for name, pixmap in self.presets.items():
                preset_action = preset_menu.addAction(name)
                preset_action.triggered.connect(
                    lambda checked, p=pixmap: self.setPresetImage(p)
                )
        opacity_menu = menu.addMenu("马赛克不透明度")
        opacity_values = [("100%", 1.0), ("90%", 0.9), ("80%", 0.8),
                          ("70%", 0.7), ("60%", 0.6), ("50%", 0.5)]
        for text, value in opacity_values:
            action = opacity_menu.addAction(text)
            action.triggered.connect(
                lambda checked, v=value: self.setMosaicOpacity(v)
            )
        mirror_menu = menu.addMenu("镜像")
        mirror_h_action = mirror_menu.addAction("左右镜像")
        mirror_h_action.setCheckable(True)
        mirror_h_action.setChecked(self.mirror_horizontal)
        mirror_h_action.triggered.connect(lambda: self.toggleMirror(horizontal=True))
        mirror_v_action = mirror_menu.addAction("上下镜像")
        mirror_v_action.setCheckable(True)
        mirror_v_action.setChecked(self.mirror_vertical)
        mirror_v_action.triggered.connect(lambda: self.toggleMirror(vertical=True))
        settings_menu = menu.addMenu("设置")
        top_action = settings_menu.addAction("窗口置顶", self.toggleAlwaysOnTop)
        top_action.setCheckable(True)
        top_action.setChecked(self.always_on_top)
        new_window_action = menu.addAction("新建窗口")
        new_window_action.triggered.connect(self.openNewWindow)
        exit_action = menu.addAction("退出")
        exit_action.triggered.connect(self.quitApplication)
        menu.exec_(self.mapToGlobal(position))

    def openNewWindow(self):
        """启动新进程打开应用，不显示控制台窗口"""
        script_path = os.path.abspath(sys.argv[0])

        if sys.platform == "win32":
            # Windows系统 - 使用隐藏窗口的方式
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # 0表示隐藏窗口

            subprocess.Popen(
                [sys.executable, script_path],
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            # macOS和Linux系统 - 正常打开
            subprocess.Popen([sys.executable, script_path])

    def toggleMirror(self, horizontal=False, vertical=False):
        if horizontal:
            self.mirror_horizontal = not self.mirror_horizontal
        if vertical:
            self.mirror_vertical = not self.mirror_vertical
        if self.fill_mode == "image" and self.custom_image:
            self.updateContent()

    def quitApplication(self):
        self.close()
        QApplication.quit()

    def setFillMode(self, mode):
        self.fill_mode = mode
        self.updateContent()

    def setPresetImage(self, pixmap):
        self.custom_image = pixmap
        self.setFillMode("image")

    def setMosaicOpacity(self, opacity):
        self.mosaic_opacity = opacity
        if self.fill_mode == "mosaic":
            self.updateContent()

    def selectImage(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.custom_image = QPixmap(file_path)
            filename = os.path.basename(file_path)
            save_path = os.path.join(self.preset_dir, filename)
            counter = 1
            base, ext = os.path.splitext(filename)
            while os.path.exists(save_path):
                filename = f"{base}_{counter}{ext}"
                save_path = os.path.join(self.preset_dir, filename)
                counter += 1
            self.custom_image.save(save_path)
            self.loadPresets()
            self.setFillMode("image")

    def toggleAlwaysOnTop(self):
        self.always_on_top = not self.always_on_top
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.always_on_top)
        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EasyMosaicApp()
    window.show()
    sys.exit(app.exec_())
