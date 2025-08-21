package de.scadsai.infoextract.database.exception;

public class RuntimesNotFoundForDrawingException extends RuntimeException {

  public RuntimesNotFoundForDrawingException(int drawingId) {
    super("Could not find runtimes for drawing with id " + drawingId);
  }

  public RuntimesNotFoundForDrawingException(String msg, Throwable cause) {
    super(msg, cause);
  }
}
