import os
import pyspark.sql.functions as fn
from pyspark.sql.types import StringType
from pyspark.sql import SparkSession
from confluent_kafka.schema_registry import SchemaRegistryClient
from pyspark.sql.avro.functions import from_avro

# source : https://nsclass.github.io/2021/11/11/pyspark-kafka-schema-registry
# os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-streaming-kafka-0-10_2.12:3.2.0,' \
#                                     'org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0,' \
#                                     'org.apache.spark:spark-avro_2.12:3.3.1  pyspark-shell'


schemaRegistryUrl = 'http://developer.alldataint.com:8081'
bootstrapServers = "developer.alldataint.com:9092"
schema_registry_conf = {
    'url': schemaRegistryUrl
}

topic_name = "cdc.fix..fawzi.dbo.data"
schema_registry_client = SchemaRegistryClient(schema_registry_conf)
schema_value = schema_registry_client.get_latest_version(f"{topic_name}-value")
print(schema_value.schema.schema_str)


#
spark = SparkSession.builder.master("spark://developer.alldataint.com:7077") \
    .appName("testing") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")
#
binary_to_string = fn.udf(lambda x: str(int.from_bytes(x, byteorder='big')), StringType())
starting_offset = "earliest"
#
df = spark.read.format("kafka") \
    .option("kafka.bootstrap.servers", bootstrapServers) \
    .option("subscribe", topic_name) \
    .option("startingOffsets", starting_offset) \
    .option("failOnDataLoss", "false") \
    .load()
#
df.show()
#
# # # mode Avro
# from_avro_options = {"mode": "PERMISSIVE"}
# #
# # # menampilak pesan
# df.select(from_avro(fn.expr("substring(value, 6, length(value) - 5)"),
#                     schema_value.schema.schema_str,
#                     from_avro_options)
#           .alias("topicValue")).show()
#
# # menampilkan data nasted json
# kafka_raw_df = df.withColumn('topicValue', from_avro(
#     fn.expr("substring(value, 6, length(value) - 5)"),
#     schema_value.schema.schema_str, from_avro_options))
#
# kafka_raw_df.select("topicValue.*").show()
# #
# #
# # # Condition
# conditition_update = fn.col("op") == "u"
# conditition_delete = fn.col("op") == "d"
# conditition_create = fn.col("op") == "c"
# conditition_not_null_data = fn.col("op") != ""
#
#
# df_new = kafka_raw_df.select(kafka_raw_df.topicValue.alias('data'))\
#     .select('data.*').where(conditition_not_null_data)
#
# df_new.show()
# # # Filter Update
# df_update = df_new.filter(conditition_update)
# df_update.show()
# #
# # # Filter Delete
# df_delete = df_new.filter(conditition_delete)
# df_delete.show()
# #
# # # Filter Create
# df_create = df_new.filter(conditition_create)
# df_create.show()
#
