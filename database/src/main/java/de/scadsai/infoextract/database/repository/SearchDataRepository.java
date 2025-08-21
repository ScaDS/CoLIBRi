package de.scadsai.infoextract.database.repository;

import de.scadsai.infoextract.database.entity.SearchData;
import org.springframework.data.repository.CrudRepository;

import java.util.Optional;

public interface SearchDataRepository extends CrudRepository<SearchData, Integer> {

  /**
   * Retrieve searchData for a given drawing referenced by its drawing id
   * @param drawingId Drawing id
   * @return searchData for a given drawing
   */
  Optional<SearchData> findSearchDataByDrawing_DrawingId(int drawingId);

  /**
   * Delete searchData for a given drawing referenced by its drawing id
   * @param drawingId Drawing id
   */
  void deleteSearchDataByDrawing_DrawingId(int drawingId);
}
