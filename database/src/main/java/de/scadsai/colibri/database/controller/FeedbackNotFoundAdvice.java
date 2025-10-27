package de.scadsai.colibri.database.controller;

import de.scadsai.colibri.database.exception.FeedbackNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class FeedbackNotFoundAdvice {

  /**
   * On FeedbackNotFoundException, for the controller response,
   * set HttpStatus.NOT_FOUND and provide exception message.
   * @param ex FeedbackNotFoundException
   * @return Exception message
   */
  @ExceptionHandler(FeedbackNotFoundException.class)
  @ResponseStatus(HttpStatus.NOT_FOUND)
  public String feedbackNotFoundHandler(FeedbackNotFoundException ex) {
    return ex.getMessage();
  }
}
