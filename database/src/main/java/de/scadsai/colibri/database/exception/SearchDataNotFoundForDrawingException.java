package de.scadsai.colibri.database.exception;

public class SearchDataNotFoundForDrawingException extends RuntimeException {

  public SearchDataNotFoundForDrawingException(int drawingId) {
    super("Could not find search data for drawing with id " + drawingId);
  }

  public SearchDataNotFoundForDrawingException(String msg, Throwable cause) {
    super(msg, cause);
  }
}
