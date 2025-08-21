package de.scadsai.infoextract.database.exception;

public class RuntimeNotFoundException extends RuntimeException {

  public RuntimeNotFoundException(int runtimeId) {
    super("Could not find runtime with id " + runtimeId);
  }

  public RuntimeNotFoundException(String msg, Throwable cause) {
    super(msg, cause);
  }
}
