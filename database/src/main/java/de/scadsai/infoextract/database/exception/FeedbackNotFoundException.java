package de.scadsai.infoextract.database.exception;

public class FeedbackNotFoundException extends RuntimeException {

  public FeedbackNotFoundException(int feedbackId) {
    super("Could not find feedback with id " + feedbackId);
  }

  public FeedbackNotFoundException(String msg, Throwable cause) {
    super(msg, cause);
  }
}
