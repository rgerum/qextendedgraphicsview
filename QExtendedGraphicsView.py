import sys
try:
    from PyQt5 import QtGui, QtCore
    from PyQt5.QtWidgets import QGraphicsView, QGraphicsPathItem, QGraphicsPixmapItem, QGraphicsScene
    qt_version = '5'
except ImportError:
    from PyQt4 import QtGui, QtCore
    from PyQt4.QtGui import QGraphicsView, QGraphicsPathItem, QGraphicsPixmapItem, QGraphicsScene
    qt_version = '4'
import numpy as np

def PosToArray(pos):
    return np.array([pos.x(), pos.y()])

class QExtendedGraphicsView(QGraphicsView):
    def __init__(self):
        QGraphicsView.__init__(self)

        self.scene = QGraphicsScene(self)
        self.scene_pan = np.array([250,250])
        self.scene_panning = False
        self.last_pos = [0, 0]
        self.scene_zoom = 1.

        self.setScene(self.scene)
        self.scene.setBackgroundBrush(QtCore.Qt.black)

        self.scaler = QGraphicsPathItem()
        self.scene.addItem(self.scaler)
        self.origin = QGraphicsPixmapItem(QtGui.QPixmap(), self.scaler)

        self.hud = QGraphicsPathItem()
        self.scene.addItem(self.hud)

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.setTransform(QtGui.QTransform())
        self.initialized = False

    def paintEvent(self, QPaintEvent):
        if not self.initialized:
            self.initialized = True
            self.fitInView()
        super(QExtendedGraphicsView, self).paintEvent(QPaintEvent)

    def resizeEvent(self, event):
        super(QExtendedGraphicsView, self).resizeEvent(event)
        self.fitInView()

    def fitInView(self):
        rect = self.origin.childrenBoundingRect()
        self.origin.setTransform(QtGui.QTransform())#self.origin.setMatrix(QtGui.QMatrix(1,0,0,1,0,0))
        scaleX = self.size().width()/rect.width()
        scaleY = self.size().height()/rect.height()
        scale = min((scaleX, scaleY))
        self.scaler.setTransform(QtGui.QTransform(scale, 0, 0, scale, 0, 0))#self.scaler.setMatrix(QtGui.QMatrix(scale, 0, 0, scale, 0, 0))
        xoff = self.size().width()-rect.width()*scale
        yoff = self.size().height()-rect.height()*scale
        self.origin.setTransform(QtGui.QTransform(1, 0, 0, 1, xoff*0.5/scale,  yoff*0.5/scale))#self.setTransform(QtGui.QTransform())#self.origin.translate( xoff*0.5/scale,  yoff*0.5/scale)
        self.panEvent(xoff, yoff)
        self.zoomEvent(scale, QtCore.QPoint(0,0))

    def translateOrigin(self, x, y):
        self.origin.setTransform(QtGui.QTransform(1, 0, 0, 1, x, y))
        self.panEvent(x, y)

    def scaleOrigin(self, scale, pos):
        pos = self.mapToScene(pos)
        x, y = (pos.x(), pos.y())
        s0 = self.scaler.transform().m11()
        self.origin.setTransform(QtGui.QTransform(1, 0, 0, 1, -x/s0, -y/s0), combine=True)
        self.scaler.setTransform(QtGui.QTransform(scale, 0, 0, scale, 0, 0), combine=True)
        s0 = self.scaler.transform().m11()
        self.origin.setTransform(QtGui.QTransform(1, 0, 0, 1, +x/s0, +y/s0), combine=True)
        self.zoomEvent(scale, pos)

    def getOriginScale(self):
        return self.scaler.transform().m11()

    def mapSceneToOrigin(self, pos):
        pos = self.mapToScene(pos)
        return QtCore.QPoint(pos.x()/self.scaler.transform().m11()-self.origin.transform().dx(),
                             pos.y()/self.scaler.transform().m22()-self.origin.transform().dy())

    def mapToOrigin(self, pos):
        pos = self.mapToScene(pos)
        return QtCore.QPoint(pos.x()/self.scaler.transform().m11()-self.origin.transform().dx(),
                             pos.y()/self.scaler.transform().m22()-self.origin.transform().dy())

    def mousePressEvent(self, event):
        if event.button() == 2:
            self.last_pos = PosToArray(self.mapToScene(event.pos()))
            self.scene_panning = True
        super(QExtendedGraphicsView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.scene_panning:
            new_pos = PosToArray(self.mapToScene(event.pos()))
            delta = new_pos-self.last_pos
            self.origin.setTransform(QtGui.QTransform(1, 0, 0, 1, *delta/self.scaler.transform().m11()), combine=True)
            #self.origin.translate(*delta/self.scaler.transform().m11())
            self.last_pos = new_pos
        super(QExtendedGraphicsView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == 2:
            self.scene_panning = False
        super(QExtendedGraphicsView, self).mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if qt_version == '5':
            angle = event.angleDelta().y()
        else:
            angle = event.delta()
        if angle > 0:
            self.scaleOrigin(1.1, event.pos())
        else:
            self.scaleOrigin(0.9, event.pos())

    def zoomEvent(self, scale, pos):
        pass

    def panEvent(self, x, y):
        pass

    def keyPressEvent(self, event):
        event.setAccepted(False)
        return

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    view = QExtendedGraphicsView()
    view.show()
    sys.exit(app.exec_())
