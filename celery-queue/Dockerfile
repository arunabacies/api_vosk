ARG FUNCTION_DIR="/home/app/"
ARG RUNTIME_VERSION="3.9"

FROM python:3.9 AS python-image
ARG RUNTIME_VERSION
ARG FUNCTION_DIR
RUN apt-get install libstdc++6
RUN apt-get update -qq && apt-get -y install \
  autoconf \
  automake \
  build-essential \
  cmake \
  git-core \
  libass-dev \
  libfreetype6-dev \
  libgnutls28-dev \
  libmp3lame-dev \
  libsdl2-dev \
  libtool \
  libva-dev \
  libvdpau-dev \
  libvorbis-dev \
  libxcb1-dev \
  libxcb-shm0-dev \
  libxcb-xfixes0-dev \
  meson \
  ninja-build \
  pkg-config \
  texinfo \
  wget \
  yasm \
  zlib1g-dev

# Create function directory
RUN mkdir -p ${FUNCTION_DIR}
COPY ./model ${FUNCTION_DIR}model
# Copy required files
COPY ffmpeg config.py requirements.txt tasks.py ${FUNCTION_DIR}
RUN mkdir -p ${FUNCTION_DIR}tmp/
# Optional – Install the function's dependencies
RUN python${RUNTIME_VERSION} -m pip install -r ${FUNCTION_DIR}requirements.txt
ENV C_FORCE_ROOT true

# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}
# ADD https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz ${FUNCTION_DIR}
#RUN tar -xf ${FUNCTION_DIR}ffmpeg-release-i686-static.tar.xz --strip=1 --wildcards 'ffmpeg-*-i686-static/ffmpeg'
COPY  ./ffmpeg /usr/bin/
RUN chmod 755 /usr/bin/ffmpeg
