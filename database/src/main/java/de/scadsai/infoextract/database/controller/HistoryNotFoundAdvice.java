package de.scadsai.infoextract.database.controller;

import de.scadsai.infoextract.database.exception.HistoryNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class HistoryNotFoundAdvice {

  /**
   * On HistoryNotFoundException, for the controller response,
   * set HttpStatus.NOT_FOUND and provide exception message.
   * @param ex HistoryNotFoundException
   * @return Exception message
   */
  @ExceptionHandler(HistoryNotFoundException.class)
  @ResponseStatus(HttpStatus.NOT_FOUND)
  public String historyNotFoundHandler(HistoryNotFoundException ex) {
    return ex.getMessage();
  }
}
