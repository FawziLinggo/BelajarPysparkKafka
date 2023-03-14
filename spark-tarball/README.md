## Download Spark Tarball

```shell
wget wget https://dlcdn.apache.org/spark/spark-3.3.2/spark-3.3.2-bin-hadoop3.tgz
tar -xvf spark-3.3.2-bin-hadoop3.tgz
sudo mkdir /opt/spark
sudo mv spark-3.3.2-bin-hadoop3/* /opt/spark
```


## Edit .bashrc
```shell
echo "export SPARK_HOME=/opt/spark" >> ~/.bashrc
echo "export PATH=$PATH:$SPARK_HOME/bin" >> ~/.bashrc
source ~/.bashrc
```

## Install Dependencies

```shell
pip install -r requirements.txt
```

## Run file py using spark

```shell
spark-submit --packages org.apache.spark:spark-streaming-kafka-0-10_2.12:3.2.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0,org.apache.spark:spark-avro_2.12:3.3.1 pengenalan.py
```

## Jalankan ssh VS Code

link : https://code.visualstudio.com/docs/remote/ssh
yt : https://www.youtube.com/watch?v=rh1Ag41J6IA

