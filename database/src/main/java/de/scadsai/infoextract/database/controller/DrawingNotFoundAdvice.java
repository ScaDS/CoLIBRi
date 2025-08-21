package de.scadsai.infoextract.database.controller;

import de.scadsai.infoextract.database.exception.DrawingNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class DrawingNotFoundAdvice {

  /**
   * On DrawingNotFoundException, for the controller response,
   * set HttpStatus.NOT_FOUND and provide exception message.
   * @param ex DrawingNotFoundException
   * @return Exception message
   */
  @ExceptionHandler(DrawingNotFoundException.class)
  @ResponseStatus(HttpStatus.NOT_FOUND)
  public String drawingNotFoundHandler(DrawingNotFoundException ex) {
    return ex.getMessage();
  }
}
