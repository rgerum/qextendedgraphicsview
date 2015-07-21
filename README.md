# QExtendedGraphicsView #

QExtendedGraphicsView extends the QGraphicsView to feature panning (right mouse button) and zooming (mouse wheel) and extends it to feature HUD elements which are not affected by these transformations.

### Interface ###

Important variables of the class

* `scene` the QGraphicsScene object
* `origin` a QGraphicsItem object which serves as the parent for all objects which should be affected by zoom and pan
* `hud` a QGraphicsItem object which serves as parent for all objects whcih should *not* be affected by zoom and pan

Important functions of the class

* `fitInView()` adjust the zoom and pan to show everything which is child of `origin`
* `getOriginScale()` returns the scale of the zooming
* `mapSceneToOrigin(pos)` maps the point `pos` from scene coordinates to the coordinate system of `origin`
* `mapToOrigin(pos)` maps the point `pos` from view coordinates to the coordinate system of `origin`

Overloadable events

* `zoomEvent(self, scale, pos)` is called when the zoom is changed
* `panEvent(self, x, y)` is called when the pan is changed

### Usage ###

Import with `from QExtendedGraphicsView import QExtendedGraphicsView`
and create the view with `QExtendedGraphicsView()`