run mvn
```shell
mvn archetype:generate -DgroupId=com.example -DartifactId=myproject -DarchetypeArtifactId=maven-archetype-quickstart -DinteractiveMode=false
```

add dependencies to pom.xml
```xml
<dependencies>
  <dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-streaming-kafka-0-10_2.12</artifactId>
    <version>3.2.0</version>
  </dependency>
  <dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-sql-kafka-0-10_2.12</artifactId>
    <version>3.2.0</version>
  </dependency>
  <dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-avro_2.12</artifactId>
    <version>3.3.1</version>
  </dependency>
</dependencies>
```

compile and package
```shell
mvn dependency:copy-dependencies
```

archive the jar file
```shell
zip -r dependencies.zip target/dependencies/*
```

upload the zip file to the cluster
```shell
scp dependencies.zip root@<master-node-ip>:/root/
```

clean up the dependencies folder
```shell
mvn clean
```