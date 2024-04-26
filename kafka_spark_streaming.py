from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Define the schema for the IoT data
schema = StructType([
    StructField("topic", StringType(), False),
    StructField("timestamp", StringType(), False),  # Initially as StringType
    StructField("device", StringType(), False),
    StructField("value", IntegerType(), False)
])

# Initialize the SparkSession to connect to the Spark master
spark = SparkSession \
    .builder \
    .appName("streaming-iot") \
    .getOrCreate()
    # .master("spark://localhost:7077") \

# Set log level to WARN to reduce verbosity of log output
spark.sparkContext.setLogLevel("WARN")

# Function to handle processing streams
def process_stream(stream, query_description):
    try:
        query = stream.start()
        query.awaitTermination()
    except Exception as e:
        print(f"Error processing {query_description}: {str(e)}")
        query.stop()
        spark.stop()

# Read streaming data from HDFS and convert timestamp to actual timestamp type
stream = spark \
    .readStream \
    .schema(schema) \
    .json("hdfs:/namenode:9870/usr/iot") \
    .withColumn("timestamp", to_timestamp("timestamp"))

# Stream Processing Query #1: Output the raw data to the console
simpleQuery = stream \
    .writeStream \
    .format("console") \
    .queryName("Raw Data Output")

process_stream(simpleQuery, "simpleQuery")

# Stream Processing Query #2: Compute the average value per device and output to the console
avgQuery = stream \
    .groupBy("device") \
    .avg("value") \
    .writeStream \
    .outputMode("complete") \
    .format("console") \
    .queryName("Average Value per Device")

process_stream(avgQuery, "avgQuery")

# Stream Processing Query #3: Compute average values in a window for each device
windowedAvgQuery = stream \
    .groupBy(window("timestamp", "10 seconds", "5 seconds"), "device") \
    .avg("value") \
    .writeStream \
    .outputMode("complete") \
    .format("console") \
    .queryName("Windowed Average Query")

process_stream(windowedAvgQuery, "windowedAvgQuery")

# Stream Processing Query #4: Compute total value in a window for each device and sort by the total
windowedSumQuery = stream \
    .groupBy(window("timestamp", "60 seconds", "5 seconds"), "device") \
    .sum("value") \
    .orderBy("sum(value)", ascending=False) \
    .writeStream \
    .outputMode("complete") \
    .format("console") \
    .queryName("Windowed Sum Query")

process_stream(windowedSumQuery, "windowedSumQuery")
