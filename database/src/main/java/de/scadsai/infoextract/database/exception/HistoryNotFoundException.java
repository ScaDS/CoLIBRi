package de.scadsai.infoextract.database.exception;

public class HistoryNotFoundException extends RuntimeException {

  public HistoryNotFoundException(int historyId) {
    super("Unable to find History with id " + historyId);
  }

  public HistoryNotFoundException(String msg, Throwable cause) {
    super(msg, cause);
  }
}
