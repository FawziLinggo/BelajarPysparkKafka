## install dependencies
```shell
pip install -r requirements.txt
```
## untuk install pyodbc

jalankan perintah berikut pada os ubuntu
```shell
pip install pyodbc
sudo apt-get install unixodbc-dev unixodbc odbcinst -y
```

## download driver odbc untuk sql server
```shell
wget https://packages.microsoft.com/ubuntu/20.04/prod/pool/main/m/msodbcsql18/msodbcsql18_18.0.1.1-1_amd64.deb -O msodbcsql.deb
sudo dpkg -i msodbcsql.deb
```

## check driver odbc
```shell
odbcinst -q -d
```

## install pymongo
```shell
pip install pymongo
```

## running mongo docker
```shell
docker run -d -p 27017:27017 --name mongo mongo:4.2
```

## create database and collection
```shell
docker exec -it mongo mongo
use pyspark
db.createCollection("from_kafka")
```
