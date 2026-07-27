FROM "python:slim"

WORKDIR /home/app

COPY requirements.txt /home/app

RUN mkdir -p /home/app && pip install -no-cache-dir -r requirements.txt

COPY newUI.py /home/app

ENV MONGO_ADMIN_USER
ENV MONGO_ADMIN_PASSWORD
ENV MONGO_HOST
ENV MONGO_PORT

EXPOSE 5000

ENTRYPOINT ["python"]

CMD ["/home/app/newUI.py"]

