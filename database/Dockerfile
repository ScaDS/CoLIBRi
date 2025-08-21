### Stage 1: Build application with gradle and jdk
FROM gradle:9-jdk21 AS build
# Install adduser utility
USER root
RUN apt-get update && apt-get install -y adduser
# Use non-root system user without login shell
RUN adduser --system --shell /bin/false gradle-build
USER gradle-build
# Set current working directory
WORKDIR /home/gradle-build/
# Copy gradle executables and build files to workdir
COPY gradlew gradlew.bat ./
COPY gradle gradle
COPY build.gradle settings.gradle gradle.properties ./
# Copy the source code
COPY src src
# Build the jar file with gradle without running checks and tests
USER root
RUN gradle clean build -x check -x test
RUN chown -R gradle-build build
# Extract layers from jar into separate directories
# see https://docs.spring.io/spring-boot/gradle-plugin/packaging.html#packaging-executable.configuring.layered-archives
USER gradle-build
RUN mv build/libs/*.jar database-app.jar
RUN java -Djarmode=tools -jar database-app.jar extract --layers --launcher --destination extractedjar

### Stage 2: Build the Docker image to run the application with openjdk from eclipse-temurin
FROM eclipse-temurin:21-jdk AS image
# Install adduser utility
USER root
RUN apt-get update && apt-get install -y adduser
# Use non-root system user without login shell
RUN adduser --system --shell /bin/false docker-image
USER docker-image
# Set current working directory
WORKDIR /home/docker-image/
# Set directory for built and extracted jar
ARG BUILD_DIR=/home/gradle-build/extractedjar
# Incorporate separate jar layers from build stage:
# - dependencies: for any non-project dependency whose version does not contain SNAPSHOT
# - spring-boot-loader: for the jar loader classes
# - snapshot-dependencies: for any non-project dependency whose version contains SNAPSHOT
# - application: for project dependencies, application classes, and resources
# Places application code and dpendencies into layers that reflect how often they change.
# Only when a layer has changed, it will be rebuilt for the Docker image
# 'RUN true' used to avoid Docker bug with long COPY sequences
COPY --from=build ${BUILD_DIR}/application/ ./
RUN true
COPY --from=build ${BUILD_DIR}/dependencies/ ./
RUN true
COPY --from=build ${BUILD_DIR}/snapshot-dependencies/ ./
RUN true
COPY --from=build ${BUILD_DIR}/spring-boot-loader/ ./
# Define entrypoint for Docker image
# Runs Spring JarLauncher, which uses information in `layers.idx` and `classpath.idx` to run the application
ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]