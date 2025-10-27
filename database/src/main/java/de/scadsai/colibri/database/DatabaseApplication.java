package de.scadsai.colibri.database;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class DatabaseApplication {

  /**
   * Entry method for application start up
   *
   * @param args Command line arguments
   */
  public static void main(String[] args) {
    SpringApplication.run(DatabaseApplication.class, args);
  }
}
