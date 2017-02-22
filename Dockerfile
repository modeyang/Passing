FROM docker-registry.yg.hunantv.com/pypy:2

ADD sources.list /etc/apt/sources.list

RUN echo "Asia/Shanghai" > /etc/timezone && dpkg-reconfigure -f noninteractive tzdata

WORKDIR /home/work

RUN apt-get update \
   && mkdir -p /home/work \
   && apt-get install -y  snappy libsnappy-dev

RUN apt-get install -y libmysqld-dev

ADD requirements.txt /home/work/requirements.txt

RUN pip install -r /home/work/requirements.txt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com

ADD . /home/work

HEALTHCHECK --interval=2m --timeout=3s CMD ps aux |grep pypy || exit 1

