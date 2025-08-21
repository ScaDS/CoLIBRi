package de.scadsai.infoextract.database.repository;

import de.scadsai.infoextract.database.entity.Runtime;
import org.springframework.data.repository.CrudRepository;

public interface RuntimeRepository extends CrudRepository<Runtime, Integer> {

  /**
   * Retrieve all runtimes for a given drawing referenced by its drawing id
   * @param drawingId Drawing id
   * @return Runtimes for a given drawing
   */
  Iterable<Runtime> findRuntimesByDrawing_DrawingId(int drawingId);

  /**
   * Delete all runtimes for a given drawing referenced by its drawing id
   * @param drawingId Drawing id
   */
  void deleteRuntimesByDrawing_DrawingId(int drawingId);
}
