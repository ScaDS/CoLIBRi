package de.scadsai.infoextract.database.controller;

import de.scadsai.infoextract.database.exception.FeedbacksNotFoundForHistoryException;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class FeedbacksNotFoundForHistoryAdvice {

  /**
   * On FeedbacksNotFoundForDrawingException, for the controller response,
   * set HttpStatus.NOT_FOUND and provide exception message.
   * @param ex FeedbacksNotFoundForDrawingException
   * @return Exception message
   */
  @ExceptionHandler(FeedbacksNotFoundForHistoryException.class)
  @ResponseStatus(HttpStatus.NOT_FOUND)
  public String feedbacksNotFoundForDrawingHandler(FeedbacksNotFoundForHistoryException ex) {
    return ex.getMessage();
  }
}
