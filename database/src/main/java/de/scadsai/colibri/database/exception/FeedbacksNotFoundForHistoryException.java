package de.scadsai.colibri.database.exception;

public class FeedbacksNotFoundForHistoryException extends RuntimeException {

  public FeedbacksNotFoundForHistoryException(int historyId) {
    super("Could not find feedbacks for history with id " + historyId);
  }

  public FeedbacksNotFoundForHistoryException(String msg, Throwable cause) {
    super(msg, cause);
  }
}
