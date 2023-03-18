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