package de.scadsai.colibri.database.controller;

import de.scadsai.colibri.database.exception.SearchDataNotFoundForDrawingException;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class SearchDataNotFoundForDrawingAdvice {

  /**
   * On SearchDataNotFoundForDrawingException, for the controller response,
   * set HttpStatus.NOT_FOUND and provide exception message.
   * @param ex SearchDataNotFoundForDrawingException
   * @return Exception message
   */
  @ExceptionHandler(SearchDataNotFoundForDrawingException.class)
  @ResponseStatus(HttpStatus.NOT_FOUND)
  public String searchDataNotFoundForDrawingHandler(SearchDataNotFoundForDrawingException ex) {
    return ex.getMessage();
  }
}
