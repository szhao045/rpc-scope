# This code is licensed under the MIT License (see LICENSE file for details)

import pathlib
from PyQt5 import Qt

from . import device_widget

class StatusWidget(device_widget.DeviceWidget):
    @staticmethod
    def can_run(scope):
        return True

    PROPERTY_DEFAULTS = dict(running=False, queued_jobs=0, errored_jobs=0, duty_cycle=0, current_job=None)

    def __init__(self, scope, scope_properties, parent=None):
        super().__init__(scope, scope_properties, parent)
        self.scope = scope
        self.setWindowTitle('Status')
        layout = Qt.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.server_label = Qt.QLabel()
        layout.addWidget(self.server_label)

        if hasattr(scope, 'job_runner'):
            self.runner_label = Qt.QLabel()
            layout.addWidget(self.runner_label)
            self.current_label = Qt.QLabel()
            layout.addWidget(self.current_label)
            self.has_runner = True
            for name, default in self.PROPERTY_DEFAULTS.items():
                setattr(self, name, default)
                self.subscribe('scope.job_runner.'+name, self._get_updater(name))
        else:
            self.has_runner = False
        layout.addStretch()
        self.server_running = False
        self.timerEvent(None)
        self.startTimer(60*1000, Qt.Qt.VeryCoarseTimer) # run timerEvent every 60 sec

    def _get_updater(self, name):
        def updater(value):
            setattr(self, name, value)
            self.update()
        return updater

    def update(self):
        _label_text(self.server_label, 'Server', self.server_running)
        if self.has_runner:
            suffix = f'{self.duty_cycle}% duty; {self.queued_jobs} queued'
            if self.errored_jobs > 0:
                suffix +=f'; <span style="font-weight: bold; color: red">{self.errored_jobs} errors</span>'
            _label_text(self.runner_label, 'Job Runner', self.running, suffix)
            if self.current_job is None:
                self.current_label.setText('No job running.')
            else:
                job = pathlib.Path(self.current_job)
                self.current_label.setText(f'Running "{job.parent.parent.name}/{job.parent.name}".')

    def timerEvent(self, event):
        if self.scope._rpc_client.heartbeat_error:
            self.scope._rpc_client.reconnect()
            self.scope_properties.reconnect()
            self.scope._image_transfer_client.reconnect()

        try:
            self.scope._ping()
            self.server_running = True
        except:
            self.server_running = False
        self.update()

def _label_text(label, prefix, status_ok=True, suffix=None):
    color = 'green' if status_ok else 'red'
    dot = f'<span style="color: {color}">\N{BLACK CIRCLE}</span>'
    if suffix is not None:
        suffix = f' ({suffix})'
    else:
        suffix = ''
    label.setText(f'{prefix}: {dot}{suffix}')