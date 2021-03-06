# -*- coding: utf-8 -*-
# This code is licensed under the MIT License (see LICENSE file for details)

import platform
import datetime
import time

from .. import scope_client
from .. import scope_job_runner
from ..config import scope_configuration

def main():
    runner = scope_job_runner.JobRunner()
    jobs = runner.jobs.get_jobs()
    to_email = set()
    for job in jobs:
        if job.status == scope_job_runner.STATUS_QUEUED and job.alert_emails:
            to_email.update(job.alert_emails)

    print('Concerned parties: {}'.format(', '.join(sorted(to_email))))

    if to_email:
        # there's someone to alert, so let's see if there's an alert to send:
        has_scope = False
        try:
            scope = scope_client.ScopeClient()
            has_scope = True
        except RuntimeError:
            print('Could not communicate with scope server. Is it running?')

    if to_email and has_scope:
        errors = []
        has_humidity = has_temperature = False
        try:
            humidity, temperature = scope.humidity_controller.data
            target_humidity = scope.humidity_controller.target_humidity
            has_humidity = True
        except:
            humidity = temperature = target_humidity = 'NO DATA'
            errors.append('HUMIDITY CONTROLLER NOT AVAILABLE')
        try:
            target_temperature = scope.temperature_controller.target_temperature
            has_temperature = True
        except:
            target_temperature = 'NO DATA'
            errors.append('TEMPERATURE CONTROLLER NOT AVAILABLE')

        if has_humidity and (humidity > 98 or target_humidity - humidity > 8):
            # humidity over 98%, or more than 8% less than desired.
            errors.append('HUMIDITY DEVIATION')
        if has_humidity and has_temperature and abs(temperature - target_temperature) >= 2:
            errors.append('TEMPERATURE DEVIATION')

        host = platform.node().split('.')[0]
        now = datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
        err_text = '\n'.join(errors)
        if errors:
            err_text += '\n\n'
        message = 'Machine: {}\nTime: {}\n\n{}Actual temperature: {}°C\nTarget temperature: {}°C\n\nActual humidity: {}%\nTarget humidity: {}%\n'
        message = message.format(host, now, err_text, temperature, target_temperature, humidity, target_humidity)
        print(message)

        if errors:
            subject = '{}: {}'.format(host, ' AND '.join(errors))
            last_email_file = scope_configuration.CONFIG_DIR / '.last_incubator_error_email_time'
            send_email = False
            if not last_email_file.exists():
                send_email = True
            else:
                last_email = float(last_email_file.read_text())
                if time.time() > last_email + 6*60*60: # email every 6h at most
                    send_email = True
            if send_email:
                print('sending email: {}'.format(subject))
                runner.send_error_email(sorted(to_email), subject, message)
                last_email_file.write_text(str(time.time()))
            else:
                print('not sending email (previous alert too recent)')

    # ask to run again in 20 mins
    print('next run:{}'.format(time.time() + 20*60))
