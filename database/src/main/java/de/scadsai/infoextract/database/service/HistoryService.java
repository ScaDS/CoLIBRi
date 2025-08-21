package de.scadsai.infoextract.database.service;

import de.scadsai.infoextract.database.entity.History;

import java.util.List;

public interface HistoryService {

  /**
   * Store a history entity to the database
   *
   * @param history History entity
   * @return The stored history entity
   */
  History saveHistory(History history);

  /**
   * Store a collection of history entities to the database
   *
   * @param histories Collection of history entities
   * @return The stored collection of history entities
   */
  List<History> saveHistories(List<History> histories);

  /**
   * Retrieve a history entity from the database by its id
   * @param id History id
   * @return History entity
   */
  History findHistoryById(int id);

  /**
   * Retrieve all history entities from the database
   * @return Collection of all history entities
   */
  List<History> findAllHistories();

  /**
   * Delete a history entity from the database by its id
   * @param id History id
   */
  void deleteHistoryById(int id);
}
