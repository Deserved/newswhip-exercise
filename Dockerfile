FROM python:3

RUN adduser --disabled-password app
USER app
WORKDIR /home/app
ENV PATH="/home/app/.local/bin:${PATH}"

ADD data/newswhip-snrinfraeng.tar.bz .
COPY --chown=app:app src .

RUN pip install --user -r requirements.txt

CMD [ "python", "index.py" ]