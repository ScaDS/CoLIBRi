package de.scadsai.colibri.database.exception;

public class DrawingNotFoundException extends RuntimeException {

  public DrawingNotFoundException(int drawingId) {
    super("Unable to find Drawing with id " + drawingId);
  }

  public DrawingNotFoundException(String msg, Throwable cause) {
    super(msg, cause);
  }
}
