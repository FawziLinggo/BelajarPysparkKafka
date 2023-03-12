import logging
import psycopg2
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

topic_name = "cdc.fix..fawzi.dbo.data"
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
conditition_update = fn.col("op") == "u"
conditition_delete = fn.col("op") == "d"
conditition_create = fn.col("op") == "c"
conditition_not_null_data = fn.col("op") != ""

kafka_raw_df = df.withColumn('topicValue', from_avro(
    fn.expr("substring(value, 6, length(value) - 5)"),
    schema_value.schema.schema_str, from_avro_options)).select('topicValue.*').where(conditition_not_null_data)

## Menampilkan seluruh data create
# kafka_raw_df.where(conditition_create).writeStream \
#     .format("console") \
#     .outputMode("append") \
#     .start() \
#     .awaitTermination()

urlPostgre="192.168.35.79"
portPostgre=5432
DBPostgre="postgres"
urlJDBCPostgres = f"jdbc:postgresql://{urlPostgre}:{portPostgre}/{DBPostgre}"
tabelPostgres = "data"
userPostgres = "postgres"
passwordPostgres = "postgres"


# Menulis data ke PostgreSQL menggunakan modul JDBC
def write_to_postgresql(df, epoch_id):
    df.write \
        .format("jdbc") \
        .option("url", urlJDBCPostgres) \
        .option("dbtable", tabelPostgres) \
        .option("user", userPostgres) \
        .option("password", passwordPostgres) \
        .mode("append") \
        .save()

    logging.info("Data berhasil ditulis ke PostgreSQL, dengan data : {}".format(df.collect()))

def delete_from_postgresql(df, epoch_id):
    conn = psycopg2.connect(host=urlPostgre,
                            port=portPostgre,
                            dbname=DBPostgre,
                            user=userPostgres,
                            password=passwordPostgres)
    cur = conn.cursor()
    rows = df.rdd.collect()
    num_rows = len(rows)
    logging.info("Menerima {} baris untuk dihapus".format(num_rows))
    for row in df.rdd.collect():
        cur.execute("DELETE FROM {} WHERE id = '{}'".format(tabelPostgres, row.id))
        logging.info("Data berhasil dihapus dari PostgreSQL, dengan id : {}".format(row.id))
    conn.commit()
    cur.close()
    conn.close()


## Hanya menampilkan data yang dibuat (create)
kafka_raw_df.where(conditition_create).select("after.*")\
    .writeStream \
    .foreachBatch(write_to_postgresql) \
    .start() \
    .awaitTermination()

## Menghapus data (delete)
kafka_raw_df.where(conditition_delete).select("before.*")\
    .writeStream \
    .foreachBatch(delete_from_postgresql) \
    .start() \
    .awaitTermination()