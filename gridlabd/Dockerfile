FROM ubuntu:24.04

ENV GRIDLABD_INSTALL_DIR=/opt/gridlabd
ENV PATH="${GRIDLABD_INSTALL_DIR}/bin:${PATH}"

# Install dependencies for .deb packages
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        libncurses6 libtinfo6 python3 python3-pip bash wget gdebi-core && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
  
# Copy the .deb file into Docker
COPY GridLAB-D-5.3.0-Linux.deb /tmp/gridlabd.deb

# Install the .deb
RUN gdebi -n /tmp/gridlabd.deb && rm /tmp/gridlabd.deb

# RUN git clone --recursive --depth 1 https://github.com/gridlab-d/tools.git /app/tools

WORKDIR /app
CMD ["bash"]
