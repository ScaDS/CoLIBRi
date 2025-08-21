package de.scadsai.infoextract.database.service;

import de.scadsai.infoextract.database.entity.Runtime;

import java.util.List;

public interface RuntimeService {

  /**
   * Store a runtime entity to the database
   *
   * @param runtime Runtime entity
   * @return The stored runtime entity
   */
  Runtime saveRuntime(Runtime runtime);

  /**
   * Store a collection of runtime entities to the database
   *
   * @param runtimes Collection of runtime entities
   * @return The stored collection of runtime entities
   */
  List<Runtime> saveRuntimes(List<Runtime> runtimes);

  /**
   * Retrieve a runtime entity from the database by its id
   * @param id Runtime id
   * @return Runtime entity
   */
  Runtime findRuntimeById(int id);

   /**
   * Retrieve all runtime entities from the database by its referencing drawing id
   * @param id Drawing id
   * @return Collection of all runtime entities
   */
  List<Runtime> findRuntimesByDrawingId(int id);

  /**
   * Retrieve all runtime entities from the database
   * @return Collection of all runtime entities
   */
  List<Runtime> findAllRuntimes();

  /**
   * Delete a runtime entity from the database by its id
   * @param id Runtime id
   */
  void deleteRuntimeById(int id);

  /**
   * Delete all runtime entities from the database by its referencing drawing id
   * @param id Drawing id
   */
  void deleteRuntimesByDrawingId(int id);
}
