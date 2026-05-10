# FROM ubuntu:24.04

# ARG ARCH=amd64

# # 1. CÀI ĐẶT JAVA & PYTHON (Cốt lõi để hỗ trợ uv từ Spark)
# # Cài đặt Python 3.10 ở cấp OS để các NodeManager có thể chạy code PySpark
# ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-${ARCH}
# RUN apt-get update && \
#     DEBIAN_FRONTEND=noninteractive apt-get install -y \
#     openjdk-8-jdk \
#     wget \
#     libzip4 \
#     libsnappy1v5 \
#     libssl-dev \
#     python3.10 \
#     python3-pip \
#     python-is-python3 && \
#     rm -rf /var/lib/apt/lists/*

# # 2. CÀI ĐẶT HADOOP
# ENV HADOOP_VERSION=3.3.6
# ENV HADOOP_HOME=/usr/local/hadoop
# ENV HADOOP_OPTS=-Djava.library.path=/usr/local/hadoop/lib/native
# ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

# ENV YARN_RESOURCEMANAGER_USER=root
# ENV YARN_NODEMANAGER_USER=root

# # Chạy script tải và giải nén Hadoop
# COPY ./install-hadoop.sh /tmp/install-hadoop.sh
# RUN chmod +x /tmp/install-hadoop.sh && bash /tmp/install-hadoop.sh && rm /tmp/install-hadoop.sh

# # Tạo thư mục vật lý cho HDFS
# RUN mkdir -p /data/dfs/data /data/dfs/name /data/dfs/namesecondary
# VOLUME /data

# # Kịch bản khởi động NameNode
# COPY start-namenode.sh /usr/local/bin/start-namenode.sh
# RUN chmod +x /usr/local/bin/start-namenode.sh

# # 3. MỞ CỔNG (PORTS)
# EXPOSE 9000 9870 9866 9867 9864 9868 8088 8042

# CMD ["hdfs"]


FROM ubuntu:22.04

ARG ARCH=amd64

# ==========================================
# 1. JAVA + PYTHON RUNTIME
# ==========================================

ENV DEBIAN_FRONTEND=noninteractive

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-${ARCH}

RUN apt-get update && \
    apt-get install -y \
    openjdk-11-jdk \
    python3 \
    python3-pip \
    python-is-python3 \
    wget \
    curl \
    tar \
    ssh \
    rsync \
    procps \
    net-tools \
    libsnappy1v5 \
    libssl-dev && \
    rm -rf /var/lib/apt/lists/*

# ==========================================
# 2. HADOOP ENVIRONMENT
# ==========================================

ENV HADOOP_VERSION=3.3.6
ENV HADOOP_HOME=/usr/local/hadoop

ENV HADOOP_OPTS="-Djava.library.path=/usr/local/hadoop/lib/native"

ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

ENV YARN_RESOURCEMANAGER_USER=root
ENV YARN_NODEMANAGER_USER=root

# ==========================================
# 3. COPY HADOOP ARTIFACT
# ==========================================

COPY ./artifacts/hadoop-3.3.6.tar.gz /tmp/

# ==========================================
# 4. INSTALL HADOOP
# ==========================================

COPY ./install-hadoop.sh /tmp/install-hadoop.sh

RUN chmod +x /tmp/install-hadoop.sh && \
    bash /tmp/install-hadoop.sh && \
    rm -f /tmp/install-hadoop.sh

# ==========================================
# 5. HDFS STORAGE DIRECTORIES
# ==========================================

RUN mkdir -p \
    /data/dfs/name \
    /data/dfs/data \
    /data/dfs/namesecondary

VOLUME ["/data"]

# ==========================================
# 6. STARTUP SCRIPT
# ==========================================

COPY ./start-namenode.sh /usr/local/bin/start-namenode.sh

RUN chmod +x /usr/local/bin/start-namenode.sh

# ==========================================
# 7. EXPOSE PORTS
# ==========================================

EXPOSE 9000
EXPOSE 9870
EXPOSE 9864
EXPOSE 9866
EXPOSE 9867
EXPOSE 9868
EXPOSE 8088
EXPOSE 8042

CMD ["bash"]