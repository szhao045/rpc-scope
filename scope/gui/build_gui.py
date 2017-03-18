import signal
from PyQt5 import Qt
from ris_widget import shared_resources

from .. import scope_client
from . import scope_widgets
from . import andor_camera_widget
from . import lamp_widget
from . import scope_viewer_widget
from . import microscope_widget
from . import stage_pos_table_widget
from . import game_controller_input_widget
from . import incubator_widget

WIDGETS = [
    # properties not specified as True are assumed False
    dict(name='camera', cls=andor_camera_widget.AndorCameraWidget, start_visible=True, docked=True),
    dict(name='lamps', cls=lamp_widget.LampWidget, start_visible=True, docked=True),
    dict(name='incubator', cls=incubator_widget.IncubatorWidget, start_visible=True, docked=True),
    dict(name='microscope', cls=microscope_widget.MicroscopeWidget, start_visible=True, docked=True),
    dict(name='advanced_camera', cls=andor_camera_widget.AndorAdvancedCameraWidget, pad=True),
    dict(name='viewer', cls=scope_viewer_widget.ScopeViewerWidget, start_visible=True),
    dict(name='stage_table', cls=stage_pos_table_widget.StagePosTableWidget),
    dict(name='game_controller', cls=game_controller_input_widget.GameControllerInputWidget)
]

WIDGET_NAMES = set(widget['name'] for widget in WIDGETS)

def sigint_handler(*args):
    """Handler for the SIGINT signal."""
    Qt.QApplication.quit()

def gui_main(host, desired_widgets=None):
    shared_resources.create_default_QSurfaceFormat() # must be called before starting QApplication
    app = Qt.QApplication([])

    scope, scope_properties = scope_client.client_main(host)
    if desired_widgets is None:
        widgets = WIDGETS
    else:
        desired_widgets = set(desired_widgets)
        for widget in desired_widgets:
            if not widget in WIDGET_NAMES:
                raise ValueError('Unknown GUI widget "{}"'.format(widget))
            # keep widget order from WIDGETS list
            widgets = [widget for widget in WIDGETS if widget['name'] in desired_widgets]

    title = "Microscope Control"
    if host not in {'localhost', '127.0.0.1'}:
        title += ': {}'.format(host)
    main_window = scope_widgets.WidgetWindow(scope, scope_properties, widgets, window_title=title)
    main_window.show()

    # install a custom signal handler so that when python receives control-c, QT quits
    signal.signal(signal.SIGINT, sigint_handler)
    # now arrange for the QT event loop to allow the python interpreter to
    # run occasionally. Otherwise it never runs, and hence the signal handler
    # would never get called.
    timer = Qt.QTimer()
    timer.start(100)
    # add a no-op callback for timeout. What's important is that the python interpreter
    # gets a chance to run so it can see the signal and call the handler.
    timer.timeout.connect(lambda: None)

    app.exec()
