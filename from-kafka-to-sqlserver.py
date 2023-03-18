import logging
import pyodbc
import os
import pyspark.sql.functions as fn
from pyspark.sql.types import StringType
from pyspark.sql import SparkSession
from confluent_kafka.schema_registry import SchemaRegistryClient
from pyspark.sql.avro.functions import from_avro


logging.basicConfig(level=logging.INFO , format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# source : https://nsclass.github.io/2021/11/11/pyspark-kafka-schema-registry
# Install jdbc driver org.postgresql:postgresql:42.3.2
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-streaming-kafka-0-10_2.12:3.2.0,' \
                                    'org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0,' \
                                    'org.apache.spark:spark-avro_2.12:3.3.1,' \
                                    'org.postgresql:postgresql:42.5.4  pyspark-shell'

schemaRegistryUrl = 'http://developer.alldataint.com:8081'
bootstrapServers = "developer.alldataint.com:9092"
schema_registry_conf = {
    'url': schemaRegistryUrl
}

topic_name = "cdc.fix.fawzi.dbo.data2"
schema_registry_client = SchemaRegistryClient(schema_registry_conf)
schema_value = schema_registry_client.get_latest_version(f"{topic_name}-value")
print(schema_value.schema.schema_str)

spark = SparkSession.builder.master("local[*]") \
    .appName("KafkaSparkStreaming") \
    .config("spark.driver.extraClassPath", "/home/adi/library/postgresql-42.5.4.jar")\
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")

binary_to_string = fn.udf(lambda x: str(int.from_bytes(x, byteorder='big')), StringType())
starting_offset = "earliest"

df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", bootstrapServers) \
    .option("subscribe", topic_name) \
    .option("startingOffsets", starting_offset) \
    .option("failOnDataLoss", "false") \
    .load()

# mode Avro
from_avro_options = {"mode": "PERMISSIVE"}

# Condition
conditition_not_null_data = fn.col("op") != ""

kafka_raw_df = df.withColumn('topicValue', from_avro(
    fn.expr("substring(value, 6, length(value) - 5)"),
    schema_value.schema.schema_str, from_avro_options)).select('topicValue.*').where(conditition_not_null_data)
# Databases Connection SQL Server

urlSQLServer="192.168.35.80"
portSQLServer=1433
DBSQLServer="fawzi"
tabelSQLServer = "data3"
schemaSQLServer = "dbo"
userSQLServer = "username"
passwordSQLServer = "password"

def proces_rows(df, epoch_id):
    conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+urlSQLServer+
    ';DATABASE='+DBSQLServer+
    ';UID='+userSQLServer+
    ';PWD='+ passwordSQLServer+
    ';PORT='+str(portSQLServer)+
    ';TrustServerCertificate=yes')

    cur = conn.cursor()
    rows = df.rdd.collect()
    num_rows = len(rows)
    logging.info("menerima {} row".format(num_rows))
    for row in df.rdd.collect():
        print(row)
        if row.op == "c":
            after = row.after
            cur.execute("INSERT INTO {}.{} (id, name, kategory) VALUES ('{}', '{}', '{}')"
            .format(schemaSQLServer, tabelSQLServer, after.id, after.name, after.kategory))

            logging.info("Data berhasil ditulis ke SQLserver, dengan data : {}".format(after))
        
        elif row.op == "u":
            after = row.after
            before = row.before
            cur.execute("UPDATE {}.{} SET id = '{}', name = '{}', kategory = '{}' WHERE id = '{}'"
            .format(schemaSQLServer, tabelSQLServer, after.id, after.name, after.kategory, before.id))

            logging.info("Data berhasil diupdate ke SQLserver, dengan data : {}".format(after))

        elif row.op == "d":
            before = row.before
            cur.execute("DELETE FROM {}.{} WHERE id = '{}'".format(schemaSQLServer, tabelSQLServer, before.id))
            
            logging.info("Data berhasil dihapus dari SQLserver, dengan id : {}".format(before.id))

    conn.commit()
    cur.close()
    conn.close()
    logging.info("Data berhasil ditulis ke SQLserver, dengan data : {}".format(df.collect()))


# Menghapus data (delete)

kafka_raw_df.where(conditition_not_null_data)\
    .writeStream \
    .foreachBatch(proces_rows) \
    .start() \
    .awaitTermination()