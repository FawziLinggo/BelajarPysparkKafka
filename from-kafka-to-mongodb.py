import logging
from pymongo import MongoClient
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

# Databases Connection MongoDB
urlMongoDB = "mongodb://developer.alldataint.com:27017"
DBMongoDB = "pyspark"
collectionMongoDB = "from_kafka"


def proces_rows(df, epoch_id):

    client = MongoClient(urlMongoDB)
    db = client[DBMongoDB]
    collection = db[collectionMongoDB]


    rows = df.rdd.collect()
    num_rows = len(rows)
    logging.info("menerima {} row".format(num_rows))
    for row in df.rdd.collect():
        print(row)
        if row.op == "c":
            after = row.after
            collection.insert_one(after.asDict())
            logging.info("Data berhasil ditulis ke MongoDB, dengan data : {}".format(after))

        elif row.op == "u":
            after = row.after
            before = row.before
            collection.update_one({"id": before.id}, {"$set": after.asDict()})
            logging.info("Data berhasil diupdate ke MongoDB, dengan data : {}".format(after))

        elif row.op == "d":
            before = row.before
            collection.delete_one({"id": before.id})
            logging.info("Data berhasil dihapus ke MongoDB, dengan data : {}".format(before))

    logging.info("Selesai menulis {} row".format(num_rows))
    client.close()
    

# Menghapus data (delete)

kafka_raw_df.where(conditition_not_null_data)\
    .writeStream \
    .foreachBatch(proces_rows) \
    .start() \
    .awaitTermination()