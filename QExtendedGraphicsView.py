from __future__ import division
import sys

from qtpy import QtGui, QtCore, QtWidgets

import numpy as np


def PosToArray(pos):
    return np.array([pos.x(), pos.y()])


class MyScene(QtWidgets.QGraphicsScene):
    def __init__(self, parent, dropTarget=None):
        QtWidgets.QGraphicsScene.__init__(self, parent)
        if dropTarget is None:
            self.setAcceptDrops(False)
        self.dropTarget = dropTarget

    def dragEnterEvent(self, e):
        if self.dropTarget:
            return self.dropTarget.dragEnterEvent(e)

        e.acceptProposedAction()

    def dragMoveEvent(self, e):
        if self.dropTarget:
            return self.dropTarget.dragMoveEvent(e)
        e.acceptProposedAction()

    def dropEvent(self, e):
        if self.dropTarget:
            return self.dropTarget.dropEvent(e)
        self.parent()
        e.accept()

class QExtendedGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, dropTarget=None):
        QtWidgets.QGraphicsView.__init__(self)

        if dropTarget:
            self.scene = MyScene(self, dropTarget)
        else:
            self.scene = QtWidgets.QGraphicsScene(self)
        self.scene_pan = np.array([250, 250])
        self.scene_panning = False
        self.last_pos = [0, 0]
        self.scene_zoom = 1.

        self.setScene(self.scene)
        self.scene.setBackgroundBrush(QtCore.Qt.black)

        self.scaler = QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap())
        self.scene.addItem(self.scaler)
        self.translater = QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap(), self.scaler)

        self.rotater1 = QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap(), self.translater)
        self.rotater2 = QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap(), self.rotater1)
        self.origin = QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap(), self.rotater2)
        self.origin.angle = 0

        self.hud = QtWidgets.QGraphicsPathItem()
        self.scene.addItem(self.hud)
        self.hud_lowerRight = QtWidgets.QGraphicsPathItem()
        self.scene.addItem(self.hud_lowerRight)
        self.hud_lowerRight.setTransform(QtGui.QTransform(1, 0, 0, 1, self.size().width(), self.size().height()))

        self.hud_upperRight = QtWidgets.QGraphicsPathItem()
        self.scene.addItem(self.hud_upperRight)
        self.hud_upperRight.setTransform(QtGui.QTransform(1, 0, 0, 1, self.size().width(), 0))

        self.hud_lowerLeft = QtWidgets.QGraphicsPathItem()
        self.scene.addItem(self.hud_lowerLeft)
        self.hud_lowerLeft.setTransform(QtGui.QTransform(1, 0, 0, 1, 0, self.size().height()))

        self.hud_lowerCenter = QtWidgets.QGraphicsPathItem()
        self.scene.addItem(self.hud_lowerCenter)
        self.hud_lowerCenter.setTransform(QtGui.QTransform(1, 0, 0, 1, self.size().width() * 0.5, self.size().height()))

        self.hud_upperCenter = QtWidgets.QGraphicsPathItem()
        self.scene.addItem(self.hud_upperCenter)
        self.hud_upperCenter.setTransform(QtGui.QTransform(1, 0, 0, 1, self.size().width() * 0.5, 0))

        self.hud_leftCenter = QtWidgets.QGraphicsPathItem()
        self.scene.addItem(self.hud_leftCenter)
        self.hud_leftCenter.setTransform(QtGui.QTransform(1, 0, 0, 1, 0, self.size().height() * 0.5))

        self.hud_rightCenter = QtWidgets.QGraphicsPathItem()
        self.scene.addItem(self.hud_rightCenter)
        self.hud_rightCenter.setTransform(QtGui.QTransform(1, 0, 0, 1, self.size().width(), self.size().height() * 0.5))

        self.hud_center = QtWidgets.QGraphicsPathItem()
        self.scene.addItem(self.hud_center)
        self.hud_center.setTransform(
            QtGui.QTransform(1, 0, 0, 1, self.size().width() * 0.5, self.size().height() * 0.5))

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.setTransform(QtGui.QTransform())
        self.initialized = False
        self.painted = False
        self.view_rect = [1, 1]
        self.fitted = 1
        self.rotation = 0
        self.setStyleSheet("border-width: 0px; border-style: outset;")
        # self.setContentsMargins(0, 0, 0, 0)

    def setExtend(self, width, height):
        do_fit_to_view = (self.fitted and self.view_rect != [width, height])
        self.rotater1.resetTransform()
        self.origin.resetTransform()
        self.view_rect = [width, height]
        self.rotater1.setTransform(QtGui.QTransform(1, 0, 0, 1, width / 2, height / 2))
        self.origin.setTransform(QtGui.QTransform(1, 0, 0, 1, -width / 2, -height / 2))
        if do_fit_to_view:
            self.fitInView()

    def GetExtend(self, with_transform=False):
        scale = self.scaler.transform().m11()
        start_x = -self.translater.transform().dx()
        start_y = -self.translater.transform().dy()
        end_x = self.size().width() / scale + start_x
        end_y = self.size().height() / scale + start_y
        if with_transform:
            t = self.origin.transform() * self.rotater2.transform() * self.rotater1.transform()
            c = np.cos(self.origin.angle * np.pi / 180)
            s = np.sin(self.origin.angle * np.pi / 180)
            dx, dy = t.dx() * c + t.dy() * s, -t.dx() * s + t.dy() * c
            points = np.array([(pos[0] * c + pos[1] * s - dx, -pos[0] * s + pos[1] * c - dy) for pos in
                               [(start_x, start_y), (end_x, start_y), (start_x, end_y), (end_x, end_y)]])
            start_x, end_x = min(points[:, 0]), max(points[:, 0])
            start_y, end_y = min(points[:, 1]), max(points[:, 1])
        return [start_x, start_y, end_x, end_y]

    def paintEvent(self, QPaintEvent):
        if not self.initialized:
            self.initialized = True
            self.fitInView()
        super(QExtendedGraphicsView, self).paintEvent(QPaintEvent)
        self.painted = True

    def resizeEvent(self, event):
        super(QExtendedGraphicsView, self).resizeEvent(event)
        if self.fitted:
            self.fitInView()
        self.hud_lowerRight.setTransform(QtGui.QTransform(1, 0, 0, 1, self.size().width(), self.size().height()))
        self.hud_upperRight.setTransform(QtGui.QTransform(1, 0, 0, 1, self.size().width(), 0))
        self.hud_lowerLeft.setTransform(QtGui.QTransform(1, 0, 0, 1, 0, self.size().height()))

        self.hud_lowerCenter.setTransform(QtGui.QTransform(1, 0, 0, 1, self.size().width() * 0.5, self.size().height()))
        self.hud_upperCenter.setTransform(QtGui.QTransform(1, 0, 0, 1, self.size().width() * 0.5, 0))
        self.hud_leftCenter.setTransform(QtGui.QTransform(1, 0, 0, 1, 0, self.size().height() * 0.5))
        self.hud_rightCenter.setTransform(QtGui.QTransform(1, 0, 0, 1, self.size().width(), self.size().height() * 0.5))

        self.hud_center.setTransform(
            QtGui.QTransform(1, 0, 0, 1, self.size().width() * 0.5, self.size().height() * 0.5))
        self.setSceneRect(0, 0, self.size().width(), self.size().height())

    def rotate(self, angle):
        self.rotation = (self.rotation + angle) % 360
        self.origin.angle += angle
        self.rotater2.setRotation(self.origin.angle)
        if self.fitted:
            self.fitInView()

    def fitInView(self):
        # Reset View
        width, height = self.view_rect
        scale = min((self.size().width() / width, self.size().height() / height))
        if self.rotation == 90 or self.rotation == 270:
            scale = min((self.size().width() / height, self.size().height() / width))
        self.scaler.setTransform(QtGui.QTransform(scale, 0, 0, scale, 0, 0))
        xoff = self.size().width() - width * scale
        yoff = self.size().height() - height * scale
        self.translater.setTransform(QtGui.QTransform(1, 0, 0, 1, xoff * 0.5 / scale, yoff * 0.5 / scale))
        self.panEvent(xoff, yoff)
        self.zoomEvent(scale, QtCore.QPoint(0, 0))
        self.fitted = 1

    def translateOrigin(self, x, y):
        # TODO do we still use this function or can we remove it?
        self.translater.setTransform(QtGui.QTransform(1, 0, 0, 1, x, y))
        self.panEvent(x, y)

    def scaleOrigin(self, scale, pos):
        pos = self.mapToScene(pos)
        x, y = (pos.x(), pos.y())
        s0 = self.scaler.transform().m11()
        self.translater.setTransform(QtGui.QTransform(1, 0, 0, 1, -x / s0, -y / s0), combine=True)
        self.scaler.setTransform(QtGui.QTransform(scale, 0, 0, scale, 0, 0), combine=True)
        s0 = self.scaler.transform().m11()
        self.translater.setTransform(QtGui.QTransform(1, 0, 0, 1, +x / s0, +y / s0), combine=True)
        self.zoomEvent(self.scaler.transform().m11(), pos)
        self.fitted = 0

    def getOriginScale(self):
        return self.scaler.transform().m11()

    def mapSceneToOrigin(self, pos):
        pos = self.mapToScene(pos)
        return QtCore.QPoint(pos.x() / self.scaler.transform().m11() - self.translater.transform().dx(),
                             pos.y() / self.scaler.transform().m22() - self.translater.transform().dy())

    def mapToOrigin(self, pos):
        pos = self.mapToScene(pos)
        return QtCore.QPoint(pos.x() / self.scaler.transform().m11() - self.translater.transform().dx(),
                             pos.y() / self.scaler.transform().m22() - self.translater.transform().dy())

    def mapFromOrigin(self, x, y=None):
        try:
            x = x.x()
            y = y.y()
        except:
            pass
        # pos = self.mapToScene(pos)
        pos = QtCore.QPoint((x + self.translater.transform().dx()) * self.scaler.transform().m11(),
                            (y + self.translater.transform().dy()) * self.scaler.transform().m22())
        return self.mapFromScene(pos)

    def mousePressEvent(self, event):
        if event.button() == 2:
            self.last_pos = PosToArray(self.mapToScene(event.pos()))
            self.scene_panning = True
        super(QExtendedGraphicsView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.scene_panning:
            new_pos = PosToArray(self.mapToScene(event.pos()))
            delta = new_pos - self.last_pos
            self.translater.setTransform(QtGui.QTransform(1, 0, 0, 1, *delta / self.scaler.transform().m11()),
                                         combine=True)
            self.last_pos = new_pos
            self.fitted = 0
        super(QExtendedGraphicsView, self).mouseMoveEvent(event)

    def DoTranslateOrigin(self, delta):
        self.translater.setTransform(QtGui.QTransform(1, 0, 0, 1, *delta), combine=True)

    def mouseReleaseEvent(self, event):
        if event.button() == 2:
            self.scene_panning = False
        super(QExtendedGraphicsView, self).mouseReleaseEvent(event)

    def wheelEvent(self, event):
        event.ignore()
        super(QExtendedGraphicsView, self).wheelEvent(event)
        if event.isAccepted():
            return

        # if qt_version == '5':
        try:  # PyQt 5
            angle = event.angleDelta().y()
        except AttributeError:  # PyQt 4
            angle = event.delta()
        if angle > 0:
            self.scaleOrigin(1.1, event.pos())
        else:
            self.scaleOrigin(0.9, event.pos())
        event.accept()

    def zoomEvent(self, scale, pos):
        pass

    def panEvent(self, x, y):
        pass

    def keyPressEvent(self, event):
        event.setAccepted(False)
        return


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    view = QExtendedGraphicsView()
    view.show()
    sys.exit(app.exec_())
