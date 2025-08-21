package de.scadsai.infoextract.database.exception;

public class SearchDataNotFoundException extends RuntimeException {

  public SearchDataNotFoundException(int searchDataId) {
    super("Could not find search data with id " + searchDataId);
  }

  public SearchDataNotFoundException(String msg, Throwable cause) {
    super(msg, cause);
  }
}
