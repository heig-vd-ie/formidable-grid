FROM lfenergy/arras:latest

RUN apt-get update && apt-get install -y nano

COPY data/ /tmp/models/

CMD ["/bin/bash", "-c", "cp -r /tmp/models/* /app/models/ && exec bash"]
