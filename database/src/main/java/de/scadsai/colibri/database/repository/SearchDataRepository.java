package de.scadsai.colibri.database.repository;

import de.scadsai.colibri.database.dto.SearchVectorDto;
import de.scadsai.colibri.database.entity.SearchData;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.CrudRepository;

import java.util.List;
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

  /**
   * Retrieve all search vectors and their associated drawing ids
   * for building the frontend search index.
   *
   * @return list of search vector DTOs containing search data id,
   *         drawing id, and numerical search vector
   */
  @Query("""
    select new de.scadsai.colibri.database.dto.SearchVectorDto(
      sd.searchDataId,
      sd.drawing.drawingId,
      sd.searchVector
    )
    from SearchData sd
  """)
  List<SearchVectorDto> findAllSearchVectors();
}
