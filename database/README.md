# Database Microservice

This directory contains the code for the database application microservice to persist and access the preprocessed data for the technical drawings.
It operates an application based on the Spring Boot Framework for REST resources, and a PostgreSQL database.

## Project Tools

The following tools are used:
* [Java 21 - OpenJDK](https://openjdk.org/projects/jdk/21/)
* [Gradle 9](https://docs.gradle.org/current/userguide/userguide.html)
* [Spring Boot Framework 3.5](https://docs.spring.io/spring-boot/3.5/index.html)

## Application Setup

### Project Configuration Files

* `gradlew`: Gradle Wrapper script, the recommended way to execute a Gradle build  
* `build.gradle`: Script for [Gradle build](https://docs.gradle.org/current/userguide/build_file_basics.html) configuration, tasks and plugins written in [Groovy DSL](https://docs.gradle.org/current/dsl/index.html)
* `settings.gradle`: [Entry point](https://docs.gradle.org/current/userguide/settings_file_basics.html) to Gradle project, used to add subprojects to the build
* `Dockerfile`: Dockerfile to build a Docker image for the Spring Boot application
* `initdb`: Folder with SQL initialization scripts for the PostgreSQL database.  
  Scripts get executed in order, so `1_script_name` gets executed before `2_script_name`.
* `resources`: Files loaded on database setup to populate tables with example data 
* `config`: Configuration files for the development and automatic code analysis with Java and Gradle

### Application Properties for Runtime

Runtime configuration for the Spring Boot application is done via `src/main/resources/application.properties`.  
Here, the database connection is configured via environment variables which are set by the Docker Compose 
file in the parent directory.

### Application Structure

The Spring Boot application works on the following pattern, which is reflected by the according Java packages:

* **_Controller_**:
  * Exposing functionalities via REST interface, consumable by external applications
  * Calls de.scadsai.colibri.service layer
* **_Service_**:
  * Business logic implementations
  * Called by de.scadsai.colibri.controller layer
  * Calls de.scadsai.colibri.repository layer to access data
* **_Repository_**
  * [CRUD](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) actions for data 
  * Works on connected datasource, e.g. [h2 in-memory](https://www.h2database.com/html/main.html) or [PostgreSQL](https://www.postgresql.org/docs/16/index.html)
  * Called by de.scadsai.colibri.service layer

Data is handled via two concepts, also reflected by the according Java packages:

* **_Entities_**
  * Closely tied to the database schema and application domain-specific operations
  * Encapsulate and manage the state and behavior of the objects
* **_DataTransferObjects (DTO)_**
  * Act as pure data carriers without logic, best to be immutable
  * Used to transmit data between different applications, e.g. via REST

### Build Microservice via Docker Compose

**Switch to the parent directory where the file `docker-compose.yml` is located.**

To build and run only the database and Spring application microservice:
* `docker compose build database spring-app`, to build the services
* `docker compose up -d database` to start the Postgres database service
* Wait until the database is up, running and all example tables are created
  * See the logs for any errors via `docker compose logs -f database`
  * Wait for "LOG:  database system is ready to accept connections"
* `docker compose up -d spring-app` to start the Spring application service
  * See the logs for any errors via `docker compose logs -f spring-app`

To inspect the running containers:
* `docker compose ps -a`

To stop all running containers, and fully remove the according images and volumes:
* `docker compose down --rmi "all" -v`

### REST API documentation

A Swagger-based REST API documentation for the Spring application is available at:
* `http://localhost:7201/swagger-ui.html`
