package de.scadsai.colibri.database.controller;

import de.scadsai.colibri.database.exception.RuntimeNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class RuntimeNotFoundAdvice {

  /**
   * On RuntimeNotFoundException, for the controller response,
   * set HttpStatus.NOT_FOUND and provide exception message.
   * @param ex RuntimeNotFoundException
   * @return Exception message
   */
  @ExceptionHandler(RuntimeNotFoundException.class)
  @ResponseStatus(HttpStatus.NOT_FOUND)
  public String runtimeNotFoundHandler(RuntimeNotFoundException ex) {
    return ex.getMessage();
  }
}
