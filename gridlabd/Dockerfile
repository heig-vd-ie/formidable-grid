FROM ubuntu:22.04

# Install build dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        build-essential git cmake \
        autoconf automake libtool \
        libxerces-c-dev libxml2-dev \
        libboost-all-dev libreadline-dev \
        python3 python3-pip && \
    apt-get clean

# Build and install GridLAB-D from source
RUN git clone --recursive https://github.com/gridlab-d/gridlab-d.git /opt/gridlab-d && \
    cd /opt/gridlab-d && \
    git submodule update --init && \
    mkdir cmake-build && \
    cd cmake-build && \
    cmake .. && \
    make -j$(nproc) && \
    make install

WORKDIR /app
CMD ["bash"]
