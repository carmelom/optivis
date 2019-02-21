from __future__ import unicode_literals, division
from __future__ import print_function

from builtins import str
from builtins import range
from builtins import object
import os
import os.path
import sys

import abc
import math
import weakref

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy import QtSvg

import optivis.view
import optivis.view.svg
import optivis.layout
import optivis.bench.components
import optivis.bench.links
import optivis.geometry
from future.utils import with_metaclass

class AbstractCanvas(with_metaclass(abc.ABCMeta, optivis.view.AbstractView)):
    qApplication = None
    qMainWindow = None
    qScene = None
    qView = None

    def __init__(self, *args, **kwargs):
        super(AbstractCanvas, self).__init__(*args, **kwargs)

        # create empty lists for canvas stuff
        self.canvasLinks = []
        self.canvasComponents = []
        self.canvasLabels = []

        # create and initialise GUI
        self.create()
        self.initialise()

    def create(self):
        # create application
        self.qApplication = QtWidgets.QApplication(sys.argv)
        self.qMainWindow = MainWindow()

        # set close behaviour to prevent zombie processes
        self.qMainWindow.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        # create drawing area
        self.qScene = GraphicsScene()

        # create view
        self.qView = GraphicsView(self.qScene, self.qMainWindow)

        # set window title
        self.qMainWindow.setWindowTitle('Optivis - {0}'.format(self.scene.title))

        ### add menu and menu items
        self.menuBar = self.qMainWindow.menuBar()
        self.fileMenu = self.menuBar.addMenu('&File')

        exportAction = QtWidgets.QAction('Export', self.qMainWindow)
        exportAction.setShortcut('Ctrl+E')
        exportAction.triggered.connect(self.export)

        self.fileMenu.addAction(exportAction)

        exitAction = QtWidgets.QAction('Exit', self.qMainWindow)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.qApplication.quit)

        self.fileMenu.addAction(exitAction)

    def initialise(self):
        # set view antialiasing
        self.qView.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing | QtGui.QPainter.SmoothPixmapTransform | QtGui.QPainter.HighQualityAntialiasing)

    def calibrateView(self):
        """
        Sets the view box and other rendering gubbins.
        """

        # Set view rectangle to be equal to the rectangle enclosing the items in the scene.
        #
        # This is necessary because QGraphicsView uses QGraphicsScene's sceneRect() method to obtain the size of the scene,
        # and this is always set to the LARGEST scene rectangle EVER present on the scene since its creation. Since we don't
        # want to recreate the scene object, we just have to instead do the following.
        #
        # see http://permalink.gmane.org/gmane.comp.lib.qt.user/2150
        self.qView.setSceneRect(self.qScene.itemsBoundingRect())

        # set zoom
        self.qView.setScale(self.zoom)

    def draw(self):
        # draw links
        for canvasLink in self.canvasLinks:
            canvasLink.draw(self.qScene, startMarkerRadius=self.startMarkerRadius, endMarkerRadius=self.endMarkerRadius, startMarkerColor=self.startMarkerColor, endMarkerColor=self.endMarkerColor)

            if self.showFlags & AbstractCanvas.SHOW_LINKS:
                # set visibility
                canvasLink.graphicsItem.setVisible(True)
            else:
                canvasLink.graphicsItem.setVisible(False)

            # show start and end markers?
            startMarker = self.showFlags & AbstractCanvas.SHOW_START_MARKERS
            endMarker = self.showFlags & AbstractCanvas.SHOW_END_MARKERS

            canvasLink.startMarker.setVisible(startMarker)
            canvasLink.endMarker.setVisible(endMarker)

        # draw components
        for canvasComponent in self.canvasComponents:
            canvasComponent.draw(self.qScene)

            if self.showFlags & AbstractCanvas.SHOW_COMPONENTS:
                canvasComponent.graphicsItem.setVisible(True)
            else:
                canvasComponent.graphicsItem.setVisible(False)

        # draw labels
        for canvasLabel in self.canvasLabels:
            canvasLabel.draw(self.qScene, self.labelFlags)

            if self.showFlags & AbstractCanvas.SHOW_LABELS:
                canvasLabel.graphicsItem.setVisible(True)
            else:
                canvasLabel.graphicsItem.setVisible(False)

    def redraw(self, *args, **kwargs):
        # update links
        for canvasLink in self.canvasLinks:
            if self.showFlags & AbstractCanvas.SHOW_LINKS:
                canvasLink.redraw(startMarkerRadius=self.startMarkerRadius, endMarkerRadius=self.endMarkerRadius, startMarkerColor=self.startMarkerColor, endMarkerColor=self.endMarkerColor)

                # set visibility
                canvasLink.graphicsItem.setVisible(True)
            else:
                canvasLink.graphicsItem.setVisible(False)

            # show start and end markers?
            startMarker = self.showFlags & AbstractCanvas.SHOW_START_MARKERS
            endMarker = self.showFlags & AbstractCanvas.SHOW_END_MARKERS

            canvasLink.startMarker.setVisible(startMarker)
            canvasLink.endMarker.setVisible(endMarker)

        # update components
        for canvasComponent in self.canvasComponents:
            if self.showFlags & AbstractCanvas.SHOW_COMPONENTS:
                canvasComponent.redraw()
                canvasComponent.graphicsItem.setVisible(True)
            else:
                canvasComponent.graphicsItem.setVisible(False)

        # update labels
        for canvasLabel in self.canvasLabels:
            if self.showFlags & AbstractCanvas.SHOW_LABELS:
                canvasLabel.redraw(self.labelFlags)
                canvasLabel.graphicsItem.setVisible(True)
            else:
                canvasLabel.graphicsItem.setVisible(False)

    def layout(self):
        # instantiate layout manager and arrange objects
        layout = self.layoutManager(self.scene)
        layout.arrange()

    def show(self):
        # layout scene
        self.layout()

        # create canvas items
        self.createCanvasLinks()
        self.createCanvasComponents()
        self.createCanvasLabels()

        # draw scene
        self.draw()

        # draw GUI
        self.initialise()

        # show on screen
        self.qMainWindow.show()

        # if IPython is being used, don't block the terminal
        try:
            if __IPYTHON__:
                from IPython.lib.inputhook import enable_gui
                app = enable_gui('qt4')
            else:
                raise ImportError
        except (ImportError, NameError):
            sys.exit(self.qApplication.exec_())

    def createCanvasLinks(self):
        self.canvasLinks = []

        for link in self.scene.links:
            # Add link to list of canvas links.
            self.canvasLinks.append(CanvasLink(link))

    def createCanvasComponents(self):
        self.canvasComponents = []

        for component in self.scene.getComponents():
            # Add component to list of canvas components.
            self.canvasComponents.append(CanvasComponent(component))

    def createCanvasLabels(self):
        self.canvasLabels = []

        for canvasLink in self.canvasLinks:
            if canvasLink.item.labels is not None:
                # Add labels to list of canvas labels.
                for label in canvasLink.item.labels:
                    self.canvasLabels.append(CanvasLabel(label))

        for canvasComponent in self.canvasComponents:
            if canvasComponent.item.labels is not None:
                # Add labels to list of canvas labels.
                for label in canvasComponent.item.labels:
                    self.canvasLabels.append(CanvasLabel(label))

    def setZoom(self, zoom):
        self.zoom = zoom

        self.qView.setScale(self.zoom)

    def export(self):
        # generate file path
        directory = os.path.join(os.path.expanduser('~'), 'export.svg')

        # default path and file format
        path = None
        fileFormat = None

        # get path to file to export to
        while True:
            dialog = QtCore.Qt.QFileDialog(parent=self.qMainWindow, caption='Export SVG', directory=directory, filter=';;'.join(optivis.view.svg.Svg._Svg__filters))
            dialog.setAcceptMode(QtCore.Qt.QFileDialog.AcceptSave)
            dialog.setFileMode(QtCore.Qt.QFileDialog.AnyFile)

            # show dialog
            dialog.exec_()

            if len(dialog.selectedFiles()) is 0:
                # no filename specified
                return

            # get file path and format
            path, extension = os.path.splitext(str(dialog.selectedFiles()[0]))

            try:
                # check if we can write to the path
                open(path, 'w').close()
                os.unlink(path)

                # get valid format
                fileFormat = extension[1:]

                if extension not in optivis.view.svg.Svg._Svg__extensions:
                    QtCore.Qt.QMessageBox.critical(self.qMainWindow, 'File extension invalid', 'The specified file extension, \'{0}\', is invalid'.format(extension))

                    continue

                break
            except OSError:
                QtCore.Qt.QMessageBox.critical(self.qMainWindow, 'Filename invalid', 'The specified filename is invalid')
            except IOError:
                QtCore.Qt.QMessageBox.critical(self.qMainWindow, 'Permission denied', 'You do not have permission to save the file to the specified location.')

        # export
        return self.exportSvg(path=path + extension, fileFormat=fileFormat)

    def exportSvg(self, *args, **kwargs):
        svgView = optivis.view.svg.Svg(self.scene, layoutManager=self.layoutManager)
        svgView.export(*args, **kwargs)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

class GraphicsScene(QtWidgets.QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super(GraphicsScene, self).__init__(*args, **kwargs)

class GraphicsView(QtWidgets.QGraphicsView):
    wheel = QtCore.Signal(QtGui.QWheelEvent)

    def __init__(self, *args, **kwargs):
        # initialise this as a QObject (QGraphicsView is not a descendent of QObject and so can't send signals by default)
        QtCore.QObject.__init__(self)

        # now initialise as normal
        super(GraphicsView, self).__init__(*args, **kwargs)

    def wheelEvent(self, event):
        # accept the event
        event.accept()

        # emit event as a signal
        self.wheel.emit(event)

    def setScale(self, scale):
        """
        Set scale of graphics view.

        There is no native setScale() method for a QGraphicsView, so this must be achieved via setTransform().
        """

        transform = QtGui.QTransform()
        transform.scale(scale, scale)

        self.setTransform(transform)

class Simple(AbstractCanvas):
    def __init__(self, *args, **kwargs):
        super(Simple, self).__init__(*args, **kwargs)

    def initialise(self):
        super(Simple, self).initialise()

        # set central widget to be the view
        self.qMainWindow.setCentralWidget(self.qView)

        # resize main window to fit content
        self.qMainWindow.setFixedSize(self.size.x, self.size.y)

        # set view box, etc.
        self.calibrateView()

        return

class Full(AbstractCanvas):
    zoomRange = (0.1, 10)
    zoomStep = 0.1

    def __init__(self, *args, **kwargs):
        super(Full, self).__init__(*args, **kwargs)

    def create(self, *args, **kwargs):
        super(Full, self).create(*args, **kwargs)

        # Add label menu.
        self.labelMenu = self.menuBar.addMenu('&Labels')

    def draw(self, *args, **kwargs):
        super(Full, self).draw(*args, **kwargs)

        # attach link click signals to handlers
        for canvasLink in self.canvasLinks:
            canvasLink.graphicsItem.comms.mouseReleased.connect(self.canvasLinkMouseReleasedHandler)

        # attach component click signals to handlers
        for canvasComponent in self.canvasComponents:
            canvasComponent.graphicsItem.mouseReleased.connect(self.canvasComponentMouseReleasedHandler)

        # attach link click signals to handlers
        for canvasLabel in self.canvasLabels:
            canvasLabel.graphicsItem.comms.mousePressed.connect(self.canvasLabelMousePressedHandler)
            canvasLabel.graphicsItem.comms.mouseMoved.connect(self.canvasLabelMouseMovedHandler)
            canvasLabel.graphicsItem.comms.mouseReleased.connect(self.canvasLabelMouseReleasedHandler)

    def redraw(self, refreshLabelMenu=True, *args, **kwargs):
        # Refresh label flags
        for canvasLabel in self.canvasLabels:
            if canvasLabel.item.content is not None:
                for kv in list(canvasLabel.item.content.items()):
                    if kv[0] not in list(self.labelFlags.keys()):
                        # add label to list of labels, but set it off by default
                        self.labelFlags[kv[0]] = False

        if refreshLabelMenu:
            # Now that all labels have been created the dictionary of
            # label content options should be available.
            self.labelMenu.clear()

            for kv in list(self.labelFlags.items()):
                a = QtWidgets.QAction(kv[0], self.qMainWindow, checkable=True)

                # set widget data to the label key
                a.data = kv[0]

                # set toggled status
                a.setChecked(kv[1])

                # connect signal to handler
                a.toggled.connect(self.toggleLabelContent)

                # add to menu
                self.labelMenu.addAction(a)

            self.labelMenu.addSeparator()
            self.labelMenu.addAction(QtWidgets.QAction("Clear all...", self.qMainWindow))

        # call parent redraw
        super(Full, self).redraw(*args, **kwargs)

        # update scene to avoid graphical artifacts
        self.qScene.update()

    def initialise(self):
        super(Full, self).initialise()

        ### create controls

        # add control widgets
        self.controls = ControlPanel(self)
        self.controls.setFixedWidth(300)

        ### create container for view + layer buttons and controls
        self.container = QtWidgets.QWidget()

        ### create container for view + layer buttons
        self.viewWidget = QtWidgets.QWidget()
        self.viewWidgetVBox = QtWidgets.QVBoxLayout()

        # add checkbox panel to view widget
        self.viewWidgetVBox.addWidget(ViewCheckboxPanel(self))

        # add graphics view to view widget
        self.viewWidgetVBox.addWidget(self.qView)

        # set layout of view widget to the layout manager
        self.viewWidget.setLayout(self.viewWidgetVBox)

        ### create and populate layout
        self.hBox = QtWidgets.QHBoxLayout()

        # add qView to layout
        self.hBox.addWidget(self.viewWidget, stretch=3)

        # add controls to layout
        self.hBox.addWidget(self.controls, stretch=1)

        ### set up signal handling

        # set mouse wheel listener for view scrolling
        self.qView.wheel.connect(self.wheelHandler)

        ### finish up

        # set container's layout
        self.container.setLayout(self.hBox)

        # add container to main window and set as central element
        self.qMainWindow.setCentralWidget(self.container)

        # set fixed size for view
        self.qView.setMinimumSize(self.size.x, self.size.y)

        # set transformation anchor to reference the mouse position, for mouse zooming
        self.qView.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

        # set view box, etc.
        self.calibrateView()

    def setZoom(self, zoom):
        # calculate rounded zoom level
        zoom = round(zoom / Full.zoomStep) * Full.zoomStep

        # clamp zoom level to bounds
        if zoom < Full.zoomRange[0]:
            zoom = Full.zoomRange[0]
        elif zoom > Full.zoomRange[1]:
            zoom = Full.zoomRange[1]

        # call parent
        super(Full, self).setZoom(zoom)

        # update zoom slider
        self.controls.zoomSlider.setSliderPosition(self.zoom / Full.zoomStep)

        # update zoom spin box
        self.controls.zoomSpinBox.setValue(self.zoom)

    def canvasLinkMouseReleasedHandler(self, event):
        # Get clicked canvas link.
        canvasLink = self.qMainWindow.sender().data

        # open edit controls
        self.controls.openEditControls(canvasLink)

    def canvasComponentMouseReleasedHandler(self, event):
        # Get clicked canvas component.
        canvasComponent = self.qMainWindow.sender().data

        # open edit controls
        self.controls.openEditControls(canvasComponent)

    def canvasLabelMousePressedHandler(self, event):
        # Get clicked canvas label.
        canvasLabel = self.qMainWindow.sender().data

        # Set position of mouse, in case this press becomes a drag
        self.canvasLabelMousePosition = self.qView.mapFromScene(event.scenePos())

    def canvasLabelMouseMovedHandler(self, event):
        canvasItem = self.qMainWindow.sender()

        # Get moved canvas label.
        canvasLabel = canvasItem.data

        # event position
        eventPos = self.qView.mapFromScene(event.scenePos())

        # difference
        difference = eventPos - self.canvasLabelMousePosition

        # set canvas label position to original position plus the difference
        projection = optivis.geometry.Coordinates(difference.x(), 0).rotate(canvasLabel.item.azimuth)

        # set label offset
        canvasLabel.item.offset = canvasLabel.item.offset + projection

        # redraw scene
        self.redraw()

        # update mouse position
        self.canvasLabelMousePosition = eventPos

    def canvasLabelMouseReleasedHandler(self, event):
        # Get clicked canvas label.
        canvasLabel = self.qMainWindow.sender().data

        # open edit controls
        self.controls.openEditControls(canvasLabel)

    def toggleLabelContent(self, checked):
        sender = self.qMainWindow.sender()
        label = sender.data
        self.labelFlags[label] = checked
        self.redraw(refreshLabelMenu=False)

    def wheelHandler(self, event):
        # get wheel delta, dividing by 120 (to represent 15 degrees of rotation -
        # see http://qt-project.org/doc/qt-4.8/qwheelevent.html#delta)
        delta = event.delta() / 120

        # calculate new zoom level
        zoom = self.zoom + delta * self.zoomStep

        # set zoom
        self.setZoom(zoom)

class ViewCheckboxPanel(QtWidgets.QGroupBox):
    def __init__(self, canvas, *args, **kwargs):
        super(ViewCheckboxPanel, self).__init__(*args, **kwargs)

        self.canvas = canvas

        self.setTitle('Layers')

        # create horizontal layout
        self.hBox = QtWidgets.QHBoxLayout()

        # create buttons
        self.button1 = QtWidgets.QCheckBox("Components")
        self.button1.setChecked(self.canvas.showFlags & AbstractCanvas.SHOW_COMPONENTS)
        self.button1.stateChanged.connect(self.showCheckBoxChanged)
        self.button2 = QtWidgets.QCheckBox("Links")
        self.button2.setChecked(self.canvas.showFlags & AbstractCanvas.SHOW_LINKS)
        self.button2.stateChanged.connect(self.showCheckBoxChanged)
        self.button3 = QtWidgets.QCheckBox("Labels")
        self.button3.setChecked(self.canvas.showFlags & AbstractCanvas.SHOW_LABELS)
        self.button3.stateChanged.connect(self.showCheckBoxChanged)
        self.button4 = QtWidgets.QCheckBox("Start Markers")
        self.button4.setChecked(self.canvas.showFlags & AbstractCanvas.SHOW_START_MARKERS)
        self.button4.stateChanged.connect(self.showCheckBoxChanged)
        self.button5 = QtWidgets.QCheckBox("End Markers")
        self.button5.setChecked(self.canvas.showFlags & AbstractCanvas.SHOW_END_MARKERS)
        self.button5.stateChanged.connect(self.showCheckBoxChanged)

        # add buttons to layout
        self.hBox.addWidget(self.button1)
        self.hBox.addWidget(self.button2)
        self.hBox.addWidget(self.button3)
        self.hBox.addWidget(self.button4)
        self.hBox.addWidget(self.button5)

        # set layout of widget
        self.setLayout(self.hBox)

    def showCheckBoxChanged(self, *args, **kwargs):
        # just rebuild the show bitfield using all checkboxes
        self.canvas.showFlags = (self.button1.isChecked() << 0) | (self.button2.isChecked() << 1) | (self.button3.isChecked() << 2) | (self.button4.isChecked() << 3) | (self.button5.isChecked() << 4)

        # redraw canvas
        self.canvas.redraw()

    @property
    def canvas(self):
        return self.__canvas

    @canvas.setter
    def canvas(self, canvas):
        self.__canvas = canvas

class ControlPanel(QtWidgets.QWidget):
    def __init__(self, canvas, *args, **kwargs):
        super(ControlPanel, self).__init__(*args, **kwargs)

        self.canvas = canvas

        self.addControls()

    def openEditControls(self, canvasItem):
        self.itemEditPanel.setContentFromCanvasItem(canvasItem)

    @property
    def canvas(self):
        return self.__canvas

    @canvas.setter
    def canvas(self, canvas):
        self.__canvas = canvas

    def addControls(self):
        ### master layout
        controlLayout = QtWidgets.QVBoxLayout()

        ### scene controls group (layout and reference component)
        sceneControlsGroupBox = QtWidgets.QGroupBox(title="Scene")
        sceneControlsGroupBox.setFixedHeight(100)

        sceneControlsGroupBoxLayout = QtWidgets.QVBoxLayout()

        ## layout controls

        # create a container for this edit widget
        layoutContainer = QtWidgets.QWidget()
        layoutContainerLayout = QtWidgets.QHBoxLayout()

        # remove padding between widgets
        layoutContainerLayout.setContentsMargins(0, 0, 0, 0)

        layoutLabel = QtWidgets.QLabel("Manager")
        self.layoutComboBox = QtWidgets.QComboBox()

        # populate combo box
        layoutManagerClasses = self.canvas.getLayoutManagerClasses()

        for i in range(0, len(layoutManagerClasses)):
            # instantiate layout manager correctly
            layoutManager = layoutManagerClasses[i](self.canvas.scene)

            # add this layout to the combobox, setting the userData to the class name of this layout
            self.layoutComboBox.addItem(layoutManager.title, i)

        # set selected layout
        self.layoutComboBox.setCurrentIndex(self.layoutComboBox.findText(self.canvas.layoutManager.title))

        # connect signal to slot to listen for changes
        self.layoutComboBox.currentIndexChanged[int].connect(self.layoutComboBoxChangeHandler)

        # create layout edit button
        layoutEditButton = QtWidgets.QPushButton("Edit")
        layoutEditButton.clicked.connect(self.layoutEditButtonClickHandler)

        # add combo box to group box
        layoutContainerLayout.addWidget(layoutLabel, 1)
        layoutContainerLayout.addWidget(self.layoutComboBox, 4)
        layoutContainerLayout.addWidget(layoutEditButton, 1)

        # set layout container layout
        layoutContainer.setLayout(layoutContainerLayout)

        # add container to scene controls group
        sceneControlsGroupBoxLayout.addWidget(layoutContainer)

        ## scene reference controls

        # create a container for this edit widget
        referenceContainer = QtWidgets.QWidget()
        referenceContainerLayout = QtWidgets.QHBoxLayout()

        # remove padding between widgets
        referenceContainerLayout.setContentsMargins(0, 0, 0, 0)

        # reference label combo box
        referenceLabel = QtWidgets.QLabel("Reference")
        self.referenceComboBox = QtWidgets.QComboBox()

        # populate combo box
        canvasComponents = self.canvas.canvasComponents

        # add 'Default'
        self.referenceComboBox.addItem('Default', 0)

        for i in range(0, len(canvasComponents)):
            canvasComponent = canvasComponents[i]

            # add this layout to the combobox, setting the userData to the class name of this layout
            self.referenceComboBox.addItem(str(canvasComponent.item), i)

        # set selected layout
        if self.canvas.scene.reference is None:
            # default value
            self.referenceComboBox.setCurrentIndex(0)
        else:
            self.referenceComboBox.setCurrentIndex(self.referenceComboBox.findText(str(self.canvas.scene.reference)))

        # connect signal to slot to listen for changes
        self.referenceComboBox.currentIndexChanged[int].connect(self.referenceComboBoxChangeHandler)

        # add combo box to group box
        referenceContainerLayout.addWidget(referenceLabel, 1)
        referenceContainerLayout.addWidget(self.referenceComboBox, 2)

        referenceContainer.setLayout(referenceContainerLayout)

        sceneControlsGroupBoxLayout.addWidget(referenceContainer)

        # set scene controls layout
        sceneControlsGroupBox.setLayout(sceneControlsGroupBoxLayout)

        # add all to control box
        controlLayout.addWidget(sceneControlsGroupBox)

        ### zoom controls

        # group box for slider
        zoomSliderGroupBox = QtWidgets.QGroupBox(title="Zoom")
        zoomSliderGroupBox.setFixedHeight(100)

        # zoom slider
        self.zoomSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.zoomSlider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.zoomSlider.setRange(self.canvas.zoomRange[0] / self.canvas.zoomStep, self.canvas.zoomRange[1] / self.canvas.zoomStep)
        self.zoomSlider.setSingleStep(1)
        self.zoomSlider.setSliderPosition(self.canvas.zoom / self.canvas.zoomStep)
        self.zoomSlider.valueChanged[int].connect(self.zoomSliderChanged)

        # zoom spin box
        self.zoomSpinBox = QtWidgets.QDoubleSpinBox()
        self.zoomSpinBox.setDecimals(1)
        self.zoomSpinBox.setRange(*self.canvas.zoomRange)
        self.zoomSpinBox.setSingleStep(self.canvas.zoomStep)
        self.zoomSpinBox.setValue(self.canvas.zoom) # TODO: check this is a valid step
        self.zoomSpinBox.valueChanged[float].connect(self.zoomSpinBoxChanged)

        # add zoom controls to zoom group box
        sliderLayout = QtWidgets.QHBoxLayout()

        sliderLayout.addWidget(self.zoomSlider)
        sliderLayout.addWidget(self.zoomSpinBox)

        zoomSliderGroupBox.setLayout(sliderLayout)

        # add zoom group box to control box layout
        controlLayout.addWidget(zoomSliderGroupBox)

        ### item edit controls

        # group box for item edit controls
        self.itemEditGroupBox = QtWidgets.QGroupBox(title="Attributes")

        # edit panel within scroll area within group box
        self.itemEditScrollArea = QtWidgets.QScrollArea()
        self.itemEditPanel = OptivisItemEditPanel()
        self.itemEditPanel.parameterEdited.connect(self.parameterEditedHandler)
        self.itemEditScrollArea.setWidget(self.itemEditPanel)
        self.itemEditScrollArea.setWidgetResizable(True)
        itemEditGroupBoxLayout = QtWidgets.QVBoxLayout()
        itemEditGroupBoxLayout.addWidget(self.itemEditScrollArea)
        self.itemEditGroupBox.setLayout(itemEditGroupBoxLayout)

        # add group box to control box layout
        controlLayout.addWidget(self.itemEditGroupBox)

        ### add layout to control widget
        self.setLayout(controlLayout)

    def parameterEditedHandler(self):
        """
        Handles signals from edit panel showing that a parameter has been edited.
        """

        # an edited parameter might have changed the look of the view, so lay it out again and redraw
        self.canvas.layout()
        self.canvas.redraw()

    def layoutComboBoxChangeHandler(self):
        # get combo box
        layoutComboBox = self.sender()

        # get layout manager classes
        layoutManagerClasses = self.canvas.getLayoutManagerClasses()

        # get selected item's data (which is the index of the selected layout in layoutManagerClasses)
        # The toInt() returns a tuple with the data in first position and a 'status' in the second. We don't need the second one.
        layoutIndex, ok = layoutComboBox.itemData(layoutComboBox.currentIndex()).toInt()

        # update canvas layout
        self.canvas.layoutManager = layoutManagerClasses[layoutIndex]

        # re-layout
        self.canvas.layout()

        # redraw
        self.canvas.redraw()

        # reset view
        self.canvas.calibrateView()

    def layoutEditButtonClickHandler(self):
        print(self.canvas.layoutManager.title)
        layoutEditWindow = CanvasScaleFunctionEditor(self.canvas.qMainWindow, self.canvas.layoutManager)
        layoutEditWindow.show()

    def referenceComboBoxChangeHandler(self):
        # get combo box
        referenceComboBox = self.sender()

        # get components
        canvasComponents = self.canvas.canvasComponents

        # get selected item's data (which is the index of the selected component in canvasComponents)
        # The toInt() returns a tuple with the data in first position and a 'status' in the second. We don't need the second one.
        componentIndex, ok = referenceComboBox.itemData(referenceComboBox.currentIndex()).toInt()

        # update scene reference
        if componentIndex == 0:
            # 'None'
            self.canvas.scene.reference = None
        else:
            self.canvas.scene.reference = canvasComponents[componentIndex].item

        # re-layout
        self.canvas.layout()

        # redraw
        self.canvas.redraw()

        # reset view
        self.canvas.calibrateView()

    def zoomSliderChanged(self, value):
        # scale value by zoom step (sliders only support int increments)
        self.canvas.setZoom(float(value * self.canvas.zoomStep))

    def zoomSpinBoxChanged(self, value):
        self.canvas.setZoom(float(value))

class OptivisItemEditPanel(QtWidgets.QWidget):
    # signal to emit when item parameters are edited in the GUI
    parameterEdited = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super(OptivisItemEditPanel, self).__init__(*args, **kwargs)

        # create layout to use for edit controls (empty by default)
        self.vBox = QtWidgets.QVBoxLayout()
        self.vBox.setAlignment(QtCore.Qt.AlignTop)

        # set layout
        self.setLayout(self.vBox)

    def paramEditWidgetChanged(self, *args, **kwargs):
        # get widget that sent the signal
        sender = self.sender()

        # get parameter data associated with this widget
        paramName, paramType, target = self.extractParamEditWidgetPayload(sender)

        # get param value
        paramValue = OptivisCanvasItemDataType.getCanvasWidgetValue(sender, paramType)

        ### send new value to associated bench item
        self.setParamOnTarget(target, paramName, paramValue, sender)

        # emit signal
        self.parameterEdited.emit()

    def extractParamEditWidgetPayload(self, sender):
        # get parameters from sender
        paramName, paramType, target = sender.data

        # get the canvas item associated with this edit widget
        if hasattr(target, "__call__"):
            # reference the weakref by calling it like a function
            target = target()

        return (paramName, paramType, target)

    def setParamOnTarget(self, target, paramName, paramValue, widget):
        try:
            setattr(target, paramName, paramValue)

            self.setEditWidgetValidity(widget, True)
        except AttributeError as e:
            self.setEditWidgetValidity(widget, False)
            raise Exception('Error setting attribute {0} on {1}: {2}'.format(paramName, target, e))
        except Exception as e:
            self.setEditWidgetValidity(widget, False)
            raise Exception('Error setting attribute {0} on {1}: {2}'.format(paramName, target, e))

    def setEditWidgetValidity(self, widget, validity):
        if validity:
            # clear background on widget
            widget.setStyleSheet("")
        else:
            # yellow background
            widget.setStyleSheet("background-color: yellow;")

    def setContentFromCanvasItem(self, canvasItem):
        # empty current contents
        # from http://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
        for i in reversed(list(range(self.vBox.count()))):
            self.vBox.itemAt(i).widget().setParent(None)

        ### Add built-in attributes.

        # Create a group box for built-in parameters
        parameterGroupBox = QtWidgets.QGroupBox(title=str(canvasItem.item))
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)

        # set layout
        parameterGroupBox.setLayout(layout)

        # Component specific controls.
        if isinstance(canvasItem.item, optivis.bench.components.AbstractComponent):
            # Add aoi control
            aoiEditWidget = OptivisCanvasItemDataType.getCanvasWidget('aoi', OptivisCanvasItemDataType.SPINBOX, acceptRange=[-360, 360], increment=1)

            # set data
            aoiEditWidget.data = ('aoi', OptivisCanvasItemDataType.SPINBOX, weakref.ref(canvasItem.item))

            # connect edit widget text change signal to a slot that deals with it
            aoiEditWidget.valueChanged[float].connect(self.paramEditWidgetChanged)

            OptivisCanvasItemDataType.setCanvasWidgetValue(aoiEditWidget, OptivisCanvasItemDataType.SPINBOX, getattr(canvasItem.item, 'aoi'))

            # create a container for this edit widget
            container = QtWidgets.QWidget()
            containerLayout = QtWidgets.QHBoxLayout()

            # remove padding between widgets
            containerLayout.setContentsMargins(0, 0, 0, 0)

            # create label
            label = QtWidgets.QLabel(text="{0} aoi".format(canvasItem.item))

            # add label and edit widget to layout
            containerLayout.addWidget(label, 2) # stretch 2
            containerLayout.addWidget(aoiEditWidget, 1) # stretch 1

            # set layout of container
            container.setLayout(containerLayout)

            # add container to edit panel
            layout.addWidget(container)

        # Link specific controls.
        if isinstance(canvasItem.item, optivis.bench.links.AbstractLink):
            # Add length control
            lengthEditWidget = OptivisCanvasItemDataType.getCanvasWidget('length', OptivisCanvasItemDataType.SPINBOX, acceptRange=[0, float('inf')], increment=1)

            # set data
            lengthEditWidget.data = ('length', OptivisCanvasItemDataType.SPINBOX, weakref.ref(canvasItem.item))

            # connect edit widget text change signal to a slot that deals with it
            lengthEditWidget.valueChanged[float].connect(self.paramEditWidgetChanged)

            OptivisCanvasItemDataType.setCanvasWidgetValue(lengthEditWidget, OptivisCanvasItemDataType.SPINBOX, getattr(canvasItem.item, 'length'))

            # create a container for this edit widget
            container = QtWidgets.QWidget()
            containerLayout = QtWidgets.QHBoxLayout()

            # remove padding between widgets
            containerLayout.setContentsMargins(0, 0, 0, 0)

            # create label
            label = QtWidgets.QLabel(text='Length')

            # add label and edit widget to layout
            containerLayout.addWidget(label, 2) # stretch 2
            containerLayout.addWidget(lengthEditWidget, 1) # stretch 1

            # set layout of container
            container.setLayout(containerLayout)

            # add container to edit panel
            layout.addWidget(container)

        # Label specific controls.
        elif isinstance(canvasItem.item, optivis.bench.labels.AbstractLabel):
            azimuthEditWidget = OptivisCanvasItemDataType.getCanvasWidget('azimuth', OptivisCanvasItemDataType.SPINBOX, acceptRange=[-360, 360], increment=1)

            # set data
            azimuthEditWidget.data = ('azimuth', OptivisCanvasItemDataType.SPINBOX, weakref.ref(canvasItem.item))

            # connect edit widget text change signal to a slot that deals with it
            azimuthEditWidget.valueChanged[float].connect(self.paramEditWidgetChanged)

            OptivisCanvasItemDataType.setCanvasWidgetValue(azimuthEditWidget, OptivisCanvasItemDataType.SPINBOX, getattr(canvasItem.item, 'azimuth'))

            # create a container for this edit widget
            container = QtWidgets.QWidget()
            containerLayout = QtWidgets.QHBoxLayout()

            # remove padding between widgets
            containerLayout.setContentsMargins(0, 0, 0, 0)

            # create label
            label = QtWidgets.QLabel(text='azimuth')

            # add label and edit widget to layout
            containerLayout.addWidget(label, 2) # stretch 2
            containerLayout.addWidget(azimuthEditWidget, 1) # stretch 1

            # set layout of container
            container.setLayout(containerLayout)

            # add container to edit panel
            layout.addWidget(container)

        # Now that we've added built-in edit controls, add the layout to the panel
        self.vBox.addWidget(parameterGroupBox)

        # Add external parameters, if available.
        # These are only available on AbstractBenchItems, so components and links (but not labels).
        if isinstance(canvasItem.item, optivis.bench.AbstractBenchItem):
            # Create a group box for these external parameters
            externalParameterGroupBox = QtWidgets.QGroupBox(title='External Parameters')
            externalLayout = QtWidgets.QVBoxLayout()
            externalLayout.setAlignment(QtCore.Qt.AlignTop)

            # set layout
            externalParameterGroupBox.setLayout(externalLayout)

            if canvasItem.item.paramList is not None:
                # external edit controls provided

                # get attributes and external item
                attributes = canvasItem.item.paramList
                pykatObject = canvasItem.item.pykatObject

                # loop over attributes from external object and create
                for paramName in attributes:
                    dataType = attributes[paramName]

                    # get attribute value
                    paramValue = getattr(pykatObject, paramName)

                    # get widget for this parameter
                    try:
                        paramEditWidget = OptivisCanvasItemDataType.getCanvasWidget(paramName, dataType)

                        # give the edit widget knowledge of its canvas item
                        # use a weak reference to avoid making the canvas item a zombie if it is deleted
                        paramEditWidget.data = (paramName, dataType, weakref.ref(pykatObject))
                    except AttributeError as e:
                        print("[GUI] WARNING: the value of a parameter specified in the parameter list with this object is not available. Skipping.")
                        continue

                    # connect edit widget text change signal to a slot that deals with it
                    self.connect(paramEditWidget, QtCore.SIGNAL("textChanged(QString)"), self.paramEditWidgetChanged)

                    OptivisCanvasItemDataType.setCanvasWidgetValue(paramEditWidget, dataType, paramValue)

                    # create a container for this edit widget
                    container = QtWidgets.QWidget()
                    containerLayout = QtWidgets.QHBoxLayout()

                    # remove padding between widgets
                    containerLayout.setContentsMargins(0, 0, 0, 0)

                    # create label
                    label = QtWidgets.QLabel(text=paramName)

                    # add label and edit widget to layout
                    containerLayout.addWidget(label, 2) # stretch 2
                    containerLayout.addWidget(paramEditWidget, 1) # stretch 1

                    # set layout of container
                    container.setLayout(containerLayout)

                    # add container to edit panel
                    externalLayout.addWidget(container)

                # Now that we've added external edit controls, add the layout to the panel
                self.vBox.addWidget(externalParameterGroupBox)

class AbstractCanvasItem(with_metaclass(abc.ABCMeta, object)):
    """
    Class to represent an item that can be drawn on the canvas (e.g. component, link, label).
    """

    def __init__(self, item, *args, **kwargs):
        self.item = item
        self.graphicsItem = None

    @property
    def graphicsItem(self):
        return self.__graphicsItem

    @graphicsItem.setter
    def graphicsItem(self, graphicsItem):
        if not isinstance(graphicsItem, (type(None), QtWidgets.QGraphicsItem, QtWidgets.QWidget, OptivisItemContainer)):
            raise Exception('Specified graphics item is not a QGraphicsItem, QWidget, OptivisItemContainer or None')

        self.__graphicsItem = graphicsItem

    @abc.abstractmethod
    def draw(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def redraw(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def setGraphicsFromItem(self):
        """
        Set graphics item information based on data from item, e.g. position, rotation, start of line, end of line, etc.
        """
        pass

class CanvasComponent(AbstractCanvasItem):
    def __init__(self, component, *args, **kwargs):
        if not isinstance(component, optivis.bench.components.AbstractComponent):
            raise Exception('Specified component is not of type AbstractComponent')

        super(CanvasComponent, self).__init__(item=component, *args, **kwargs)

    def draw(self, qScene):
        print("[GUI] Drawing component {0} at {1}".format(self.item, self.item.position))

        # Create full system path from filename and SVG directory.
        path = os.path.join(self.item.svgDir, self.item.filename)

        # Create graphical representation of SVG image at path.
        self.graphicsItem = OptivisSvgItem(path)

        # reference this CanvasComponent in the data payload
        self.graphicsItem.data = self

        # set graphics information
        self.setGraphicsFromItem()

        qScene.addItem(self.graphicsItem)

    def redraw(self):
        print("[GUI] Redrawing component {0} at {1}".format(self.item, self.item.position))

        self.setGraphicsFromItem()

    def setGraphicsFromItem(self):
        # Reset transforms and rotations
        self.graphicsItem.resetTransform()

        # Set position of top-left corner.
        # self.position.{x, y} are relative to the centre of the component, so we need to compensate for this.
        self.graphicsItem.setPos(self.item.position.x - self.item.size.x / 2, self.item.position.y - self.item.size.y / 2)

        # Rotate clockwise.
        # Qt rotates with respect to the component's origin, i.e. top left, so to rotate around the centre we need to translate it before and after rotating it.
        self.graphicsItem.translate(self.item.size.x / 2, self.item.size.y / 2)
        self.graphicsItem.rotate(self.item.azimuth)
        self.graphicsItem.translate(-self.item.size.x / 2, -self.item.size.y / 2)

        # Set tooltip.
        if self.item.tooltip is not None:
            if hasattr(self.item.tooltip, "__call__"):
                self.graphicsItem.setToolTip(str(self.item.tooltip()))
            else:
                self.graphicsItem.setToolTip(str(self.item.tooltip))

class OptivisSvgItem(QtSvg.QGraphicsSvgItem):
    mousePressed = QtCore.Signal(QtWidgets.QGraphicsSceneMouseEvent)
    mouseReleased = QtCore.Signal(QtWidgets.QGraphicsSceneMouseEvent)

    def __init__(self, *args, **kwargs):
        super(OptivisSvgItem, self).__init__(*args, **kwargs)

    def mousePressEvent(self, event, *args, **kwargs):
        # accept the event
        # this is the default, but we'll call it anyway
        event.accept()

        # emit event as a signal
        self.mousePressed.emit(event)

    def mouseReleaseEvent(self, event, *args, **kwargs):
        # accept the event
        # this is the default, but we'll call it anyway
        event.accept()

        # emit event as a signal
        self.mouseReleased.emit(event)

class CanvasLink(AbstractCanvasItem):
    def __init__(self, link, *args, **kwargs):
        if not isinstance(link, optivis.bench.links.AbstractLink):
            raise Exception('Specified link is not of type AbstractLink')

        self.startMarker = None
        self.endMarker = None

        super(CanvasLink, self).__init__(item=link, *args, **kwargs)

    def draw(self, qScene, *args, **kwargs):
        print("[GUI] Drawing link {0}".format(self.item))

        # create graphics object(s)
        container = OptivisItemContainer()

        # reference this CanvasLink in the data payload
        container.comms.data = self

        for spec in self.item.specs:
            lineItem = OptivisLineItem()

            container.addItem(lineItem)

        self.graphicsItem = container

        # create start and end markers
        self.startMarker = QtWidgets.QGraphicsEllipseItem()
        self.endMarker = QtWidgets.QGraphicsEllipseItem()

        # add markers to graphics scene
        qScene.addItem(self.startMarker)
        qScene.addItem(self.endMarker)

        # set graphics information
        self.setGraphicsFromItem(*args, **kwargs)

        container.draw(qScene)

    def redraw(self, *args, **kwargs):
        print("[GUI] Redrawing link {0}".format(self.item))

        self.setGraphicsFromItem(*args, **kwargs)

    def setGraphicsFromItem(self, startMarkerRadius=5, endMarkerRadius=3, startMarkerColor=None, endMarkerColor=None):
        for i in range(0, len(self.item.specs)):
            # create an offset coordinate
            linePos = optivis.geometry.Coordinates(self.item.end.x - self.item.start.x, self.item.end.y - self.item.start.y)
            azimuth = linePos.getAzimuth()

            offsetPos = optivis.geometry.Coordinates(0, self.item.specs[i].offset)
            offsetPos = offsetPos.rotate(azimuth)

            # set start/end
            self.graphicsItem.getItem(i).setLine(self.item.start.x + offsetPos.x, self.item.start.y + offsetPos.y, self.item.end.x + offsetPos.x, self.item.end.y + offsetPos.y)

            # create pen
            pen = QtGui.QPen(QtGui.QColor(self.item.specs[i].color), self.item.specs[i].width, QtCore.Qt.SolidLine)

            # set pattern
            pen.setDashPattern(self.item.specs[i].pattern)

            # set pen
            self.graphicsItem.getItem(i).setPen(pen)

        # set markers
        self.startMarker.setRect(self.item.start.x - startMarkerRadius, self.item.start.y - startMarkerRadius, startMarkerRadius * 2, startMarkerRadius * 2)
        self.startMarker.setPen(QtGui.QPen(QtGui.QColor(startMarkerColor), 1, QtCore.Qt.SolidLine))

        self.endMarker.setRect(self.item.end.x - endMarkerRadius, self.item.end.y - endMarkerRadius, endMarkerRadius * 2, endMarkerRadius * 2)
        self.endMarker.setPen(QtGui.QPen(QtGui.QColor(endMarkerColor), 1, QtCore.Qt.SolidLine))

class OptivisLineItemCommunicator(QtCore.QObject):
    """
    Qt Signals communication class for OptivisLineItem
    """

    mousePressed = QtCore.Signal(QtWidgets.QGraphicsSceneMouseEvent)
    mouseReleased = QtCore.Signal(QtWidgets.QGraphicsSceneMouseEvent)

class OptivisLineItem(QtWidgets.QGraphicsLineItem):
    def __init__(self, *args, **kwargs):
        # Create a communicator.
        # This is necessary because QGraphicsLineItem does not inherit from QObject, so it does
        # not inherit signalling functionality. Instead, we do our signalling via a separate
        # communicator class which DOES inherit QObject.
        self.comms = OptivisLineItemCommunicator()

        super(OptivisLineItem, self).__init__(*args, **kwargs)

    def mousePressEvent(self, event, *args, **kwargs):
        # Accept the event.
        # this is the default, but we'll call it anyway
        event.accept()

        # emit event as a signal
        self.comms.mousePressed.emit(event)

    def mouseReleaseEvent(self, event, *args, **kwargs):
        # Accept the event.
        # this is the default, but we'll call it anyway
        event.accept()

        # emit event as a signal
        self.comms.mouseReleased.emit(event)

class CanvasLabel(AbstractCanvasItem):
    def __init__(self, label, *args, **kwargs):
        if not isinstance(label, optivis.bench.labels.AbstractLabel):
            raise Exception('Specified label is not of type AbstractLabel')

        super(CanvasLabel, self).__init__(item=label, *args, **kwargs)

    def draw(self, qScene, *args, **kwargs):
        print("[GUI] Drawing label {0}".format(self.item))

        # create label
        self.graphicsItem = OptivisLabelItem()

        # reference this CanvasLabel in the data payload
        self.graphicsItem.comms.data = self

        # set graphics information
        self.setGraphicsFromItem()

        # add to scene
        qScene.addItem(self.graphicsItem)

    def redraw(self, *args, **kwargs):
        print("[GUI] Redrawing label {0}".format(self.item))

        # Update graphical representation.
        self.setGraphicsFromItem(*args, **kwargs)

    def setGraphicsFromItem(self, labelFlags=None):
        ### Set label text.
        # Label text is set first so we can calculate the label's boundingRect() below.

        content = []

        # Create label sub-content
        if labelFlags is not None:
            for kv in list(self.item.content.items()):
                if kv[0] in list(labelFlags.keys()):
                    if labelFlags[kv[0]]:
                        # label is turned on
                        content.append("{0} = {1}".format(kv[0], kv[1]))

        # Set text
        self.graphicsItem.setText(self.item.text + "\n" + "\n".join(content))

        ### Calculate label size and azimuth.
        labelSize = optivis.geometry.Coordinates(self.graphicsItem.boundingRect().width(), self.graphicsItem.boundingRect().height())
        labelAzimuth = self.item.item.getLabelAzimuth() + self.item.azimuth

        ### Draw label at the correct position and orientation.

        # get nominal position
        labelPosition = self.item.item.getLabelOrigin()

        # translate to user-defined position
        labelPosition = labelPosition.translate((self.item.position * self.item.item.getSize()).rotate(self.item.item.getLabelAzimuth()))

        # move label such that the text is y-centered
        labelPosition = labelPosition.translate(optivis.geometry.Coordinates(0, labelSize.y / 2).flip().rotate(labelAzimuth))

        # add user-defined offset
        labelPosition = labelPosition.translate(self.item.offset.rotate(self.item.item.getLabelAzimuth()))

        # set position and angle
        self.graphicsItem.setPos(labelPosition.x, labelPosition.y)
        self.graphicsItem.setRotation(labelAzimuth)

class OptivisLabelItemCommunicator(QtCore.QObject):
    """
    Qt Signals communication class for OptivisLabelItem
    """

    mousePressed = QtCore.Signal(QtWidgets.QGraphicsSceneMouseEvent)
    mouseMoved = QtCore.Signal(QtWidgets.QGraphicsSceneMouseEvent)
    mouseReleased = QtCore.Signal(QtWidgets.QGraphicsSceneMouseEvent)

class OptivisLabelItem(QtWidgets.QGraphicsSimpleTextItem):
    def __init__(self, *args, **kwargs):
        # Create a communicator.
        # This is necessary because QGraphicsSimpleTextItem does not inherit from QObject, so it does
        # not inherit signalling functionality. Instead, we do our signalling via a separate
        # communicator class which DOES inherit QObject.
        self.comms = OptivisLabelItemCommunicator()

        super(OptivisLabelItem, self).__init__(*args, **kwargs)

    def mousePressEvent(self, event, *args, **kwargs):
        # Accept the event.
        # this is the default, but we'll call it anyway
        event.accept()

        # emit event as a signal
        self.comms.mousePressed.emit(event)

    def mouseMoveEvent(self, event, *args, **kwargs):
        # Accept the event.
        # this is the default, but we'll call it anyway
        event.accept()

        # emit event as a signal
        self.comms.mouseMoved.emit(event)

    def mouseReleaseEvent(self, event, *args, **kwargs):
        # Accept the event.
        # this is the default, but we'll call it anyway
        event.accept()

        # emit event as a signal
        self.comms.mouseReleased.emit(event)

class OptivisItemContainerCommunicator(QtCore.QObject):
    """
    Qt Signals communication class for OptivisItemContainer
    """

    mousePressed = QtCore.Signal(QtWidgets.QGraphicsSceneMouseEvent)
    mouseReleased = QtCore.Signal(QtWidgets.QGraphicsSceneMouseEvent)

class OptivisItemContainer(object):
    """
    Generic container for other OptivisItem objects. Supports draw().
    """

    def __init__(self):
        self.items = []

        # Create a communicator.
        self.comms = OptivisItemContainerCommunicator()

    def addItem(self, item):
        if not isinstance(item, (QtWidgets.QGraphicsItem, QtWidgets.QWidget)):
            raise Exception('Specified item is not of type QGraphicsItem or QWidget')

        item.comms.mousePressed.connect(self.comms.mousePressed)
        item.comms.mouseReleased.connect(self.comms.mouseReleased)

        self.items.append(item)

    def getItem(self, index):
        # FIXME: check index is valid and raise an exception if not (and make test)
        return self.items[index]

    def draw(self, qScene):
        for item in self.items:
            qScene.addItem(item)

    def setVisible(self, visibility):
        for item in self.items:
            item.setVisible(visibility)

    @property
    def items(self):
        return self.__items

    @items.setter
    def items(self, items):
        self.__items = items

class OptivisItemDataType(object):
    """
    Class to define data types for editable parameters of bench items.
    """

    TEXTBOX = 1
    CHECKBOX = 2
    SPINBOX = 3

class OptivisCanvasItemDataType(OptivisItemDataType):
    """
    Factory class for Qt objects associated with data types defined in OptivisItemDataType.
    """

    @staticmethod
    def getCanvasWidget(itemParamName, itemDataType, *args, **kwargs):

        if itemDataType == OptivisCanvasItemDataType.TEXTBOX:
            widget = QtWidgets.QLineEdit()

            return widget
        elif itemDataType == OptivisCanvasItemDataType.SPINBOX:
            widget = QtWidgets.QDoubleSpinBox()

            # set range and increment
            acceptRange = kwargs['acceptRange']
            increment = kwargs['increment']

            widget.setMinimum(acceptRange[0])
            widget.setMaximum(acceptRange[1])

            widget.setSingleStep(increment)

            return widget
        else:
            raise Exception('Specified item data type is invalid')

    @staticmethod
    def getCanvasWidgetValue(widget, itemDataType):
        if itemDataType == OptivisCanvasItemDataType.TEXTBOX:
            return str(widget.text())
        elif itemDataType == OptivisCanvasItemDataType.SPINBOX:
            return float(widget.value())
        else:
            raise Exception('Specified item data type is invalid')

    @staticmethod
    def setCanvasWidgetValue(widget, itemDataType, itemValue):
        # FIXME: check inputs are valid
        if itemDataType == OptivisCanvasItemDataType.TEXTBOX:
            itemValue = str(itemValue)

            if itemValue == 'None':
                itemValue = ''

            widget.setText(itemValue)
        elif itemDataType == OptivisCanvasItemDataType.SPINBOX:
            widget.setValue(float(itemValue))
        else:
            raise Exception('Specified item data type is invalid')

class CanvasScaleFunctionEditor(QtWidgets.QMainWindow):
    def __init__(self, layoutManager, *args, **kwargs):
        self.layoutManager = layoutManager

        super(CanvasScaleFunctionEditor, self).__init__(*args, **kwargs)

    @property
    def layoutManager(self):
        return self.__layoutManager

    @layoutManager.setter
    def layoutManager(self, layoutManager):
        if not isinstance(layoutManager, optivis.layout.AbstractLayout):
            raise Exception('Specified layout manager is not of type AbstractLayout')

        self.__layoutManager = layoutManager
