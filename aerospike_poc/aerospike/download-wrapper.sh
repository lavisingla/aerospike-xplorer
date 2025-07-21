#!/bin/bash

# Create directory if it doesn't exist
mkdir -p gradle/wrapper

# Download the Gradle wrapper JAR
echo "Downloading Gradle wrapper JAR..."
curl -L -o gradle/wrapper/gradle-wrapper.jar https://github.com/gradle/gradle/raw/v7.6.0/gradle/wrapper/gradle-wrapper.jar

echo "Gradle wrapper JAR downloaded successfully."
