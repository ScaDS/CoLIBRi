package de.scadsai.colibri.database.controller;

import de.scadsai.colibri.database.exception.SearchDataNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class SearchDataNotFoundAdvice {

  /**
   * On SearchDataNotFoundException, for the controller response,
   * set HttpStatus.NOT_FOUND and provide exception message.
   * @param ex SearchDataNotFoundException
   * @return Exception message
   */
  @ExceptionHandler(SearchDataNotFoundException.class)
  @ResponseStatus(HttpStatus.NOT_FOUND)
  public String searchDataNotFoundHandler(SearchDataNotFoundException ex) {
    return ex.getMessage();
  }
}
