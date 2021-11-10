import json
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Slot, Signal, QObject

from src.colormap import get_colors


class MapView(QObject):
    dataset_changed = Signal()  # signals for notification of Javascript
    dataset_closed = Signal()

    def __init__(self, model, controller, parent=None):
        super(MapView, self).__init__()
        self.model = model
        self.controller = controller
        self.parent = parent
        # connect signals and slots
        self.controller.source_deleted.connect(self.dataset_closed)        
        self.model.dataset_closed.connect(self.dataset_closed)
        self.model.selected_source_changed.connect(self.dataset_changed)
        self.model.selected_column_changed.connect(self.dataset_changed)

    @Slot(str)
    def printObj(self, obj):
        py_obj = json.loads(obj)
        print(py_obj)

    @Slot(result=str)
    def loadData(self):
        data = []
        colors = {}
        if self.model.dataset_is_open:
            data = self.model.data
            data_column = self.controller.get_selected_column()
            if len(data_column) > 0:
                # colormaps = {
                #     0: "plasma",
                #     1: "Reds",
                #     2: "viridis"
                # }
                # colormap = colormaps[self.model.map_model.colormap]
                # colors = get_colors(data_column, cmap=colormap, vmin=self.model.map_model.min_temp, vmax=self.model.map_model.max_temp)
                colors = get_colors(data_column, cmap="plasma", vmin=-5, vmax=5)
            else:
                default_color = "#ff7800"
                track_ids = list(self.controller.get_column("track_id").values())
                colors = {track_id: default_color for track_id in track_ids}
        return json.dumps({
            "data": data,
            "colors": colors
        })

    @Slot(str)
    def updateImages(self, track_id):
        self.model.track_id = json.loads(track_id)


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, dpi=96):
        self.fig = Figure(dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.7)
        super(MplCanvas, self).__init__(self.fig)


class ColorbarView(QWidget):
    def __init__(self, model, controller):
        super().__init__()
        self.model = model
        self.controller = controller
        self.widget = MplCanvas()
        self.widget.setFixedHeight(50)

        #self.update()
        self.widget.hide()

        # connect signals and slots
        self.model.map_model.min_temp_changed.connect(self.update)
        self.model.map_model.max_temp_changed.connect(self.update)
        self.model.map_model.colormap_changed.connect(self.update)
       
        self.model.selected_source_changed.connect(self.update)
        self.model.selected_column_changed.connect(self.update)

        
        self.model.dataset_opened.connect(self.show)
        self.model.dataset_closed.connect(self.widget.hide)
        self.controller.source_deleted.connect(self.widget.hide)

    def show(self):
        if self.model.meta is None:
            return
        self.widget.show()

    def update(self):
        if self.model.meta is None:
            self.widget.hide()
            return
        
        self.widget.show()

        cmap = matplotlib.cm.Reds
        norm = matplotlib.colors.Normalize(
            vmin=self.model.map_model.min_temp, 
            vmax=self.model.map_model.max_temp)

        cbar = self.widget.fig.colorbar(
            matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap),
            cax=self.widget.axes,
            orientation='horizontal')

        label = ""
        if self.model.meta["type"] == "module_temperatures":
            label = "Temperatures / °C"
        
        cbar.set_label(label, labelpad=0, fontsize=10)
        cbar.ax.tick_params(labelsize=10, length=2, width=1)
        self.widget.draw()