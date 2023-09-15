FROM python:3.11
ENV PYTHONUNBUFFERED=1
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN mkdir /app \
  && groupadd -g 75050 -r pantportal \
  && groupadd -g 75100 -r certificate_exporter \
  && useradd -u 75130 --no-log-init -r -g pantportal -G certificate_exporter pantportal
COPY esani_pantportal/requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt
# hadolint ignore=DL3008
RUN apt-get update \
  && apt-get install -y --no-install-recommends gettext python3-distutils graphviz \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

USER pantportal
COPY ./docker/entrypoint.sh /entrypoint.sh
COPY --chown=pantportal:pantportal ./esani_pantportal /app
EXPOSE 8000
VOLUME /srv/media
ENTRYPOINT ["/entrypoint.sh"]
WORKDIR /app
CMD ["gunicorn", "-b", "0.0.0.0:8000", "project.wsgi:application", "-w 4", "--timeout 120", "--error-logfile", "-", "--capture-output"]
