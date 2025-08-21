package de.scadsai.infoextract.database.controller;

import de.scadsai.infoextract.database.exception.RuntimesNotFoundForDrawingException;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class RuntimesNotFoundForDrawingAdvice {

  /**
   * On RuntimesNotFoundForDrawingException, for the controller response,
   * set HttpStatus.NOT_FOUND and provide exception message.
   * @param ex RuntimesNotFoundForDrawingException
   * @return Exception message
   */
  @ExceptionHandler(RuntimesNotFoundForDrawingException.class)
  @ResponseStatus(HttpStatus.NOT_FOUND)
  public String runtimesNotFoundForDrawingHandler(RuntimesNotFoundForDrawingException ex) {
    return ex.getMessage();
  }
}
