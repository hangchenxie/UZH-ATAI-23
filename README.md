# UZH Advanced Topics of Artificial Intelligence (ATAI) Fall 23

This project is based on SparkNLP.

## Installations

It's highly recommended to run this project using macOS or Linux systems. For Windows users, please refer to the Hadoop tutorial first.

### Prerequisites

- **Java**: Ensure you have Java 8 or later installed. You can download it from [Oracle's official website](https://www.oracle.com/java/technologies/javase-downloads.html).
- **Python**: Ensure you have Python 3.6 or later installed. You can download it from [Python's official website](https://www.python.org/downloads/).

### Installing SparkNLP

1. **Install Apache Spark**:
    ```bash
    pip install pyspark
    ```

2. **Install SparkNLP**:
    ```bash
    pip install spark-nlp
    ```

3. **Verify Installation**:
    ```python
    import sparknlp
    print(sparknlp.version())
    ```

### Installing Hadoop

1. **Download Hadoop**:
    - Download the latest stable release from the [Apache Hadoop website](https://hadoop.apache.org/releases.html).

2. **Extract the Downloaded File**:
    ```bash
    tar -xzvf hadoop-x.y.z.tar.gz
    ```

3. **Set Up Environment Variables**:
    Add the following lines to your `.bashrc` or `.zshrc` file:
    ```bash
    export HADOOP_HOME=/path/to/hadoop
    export PATH=$PATH:$HADOOP_HOME/bin
    ```

4. **Verify Installation**:
    ```bash
    hadoop version
    ```

For more detailed instructions, refer to the [Hadoop Installation Guide](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-common/SingleCluster.html).

## Contributions

Thanks for the generous help from @rongliyuan, this project couldn't have been done without you. And thanks to @LagShaggy for useful software suggestions.
