# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

FROM python:3.11
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.1.12/supercronic-linux-amd64 \
    SUPERCRONIC=supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=048b95b48b708983effb2e5c935a1ef8483d9e3e\
    PYTHONUNBUFFERED=1

ENV PYTHONUNBUFFERED=1
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN mkdir /app && \
    mkdir -p /srv/media && \
    mkdir -p /var/cache/pant && \
    groupadd -g 75140 -r pant && \
    groupadd -g 75100 -r certificate_exporter && \
    useradd -u 75140 --no-log-init -r -g pant -G certificate_exporter pant && \
    chown pant:pant /var/cache/pant && chmod a+w /var/cache/pant && \
    chown pant:pant /srv/media
COPY esani_pantportal/requirements.txt /app/requirements.txt
# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get install -y --no-install-recommends gettext python3-distutils graphviz libxmlsec1-dev xmlsec1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* \
    && curl -fsSLO "$SUPERCRONIC_URL" \
    && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
    && chmod +x "$SUPERCRONIC" \
    && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
    && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic

RUN pip3 install --no-cache-dir -r /app/requirements.txt
USER pant
COPY ./docker/entrypoint.sh /entrypoint.sh
COPY --chown=pant:pant ./esani_pantportal /app
EXPOSE 8000
VOLUME /srv/media
ENTRYPOINT ["/entrypoint.sh"]
WORKDIR /app
VOLUME  /var/cache/pant
CMD ["gunicorn", "-b", "0.0.0.0:8000", "project.wsgi:application", "-w 4", "--timeout", "120", "--error-logfile", "-", "--capture-output"]
