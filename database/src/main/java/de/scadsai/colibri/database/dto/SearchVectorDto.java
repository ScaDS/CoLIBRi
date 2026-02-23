package de.scadsai.colibri.database.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * Data transfer object for search index building (vectors only).
 */
/*
 * The following fields are transferred:
 *  SearchData.searchDataId -> SearchVectorDto.searchDataId
 *  SearchData.drawing (drawingId) -> SearchVectorDto.drawingId
 *  SearchData.searchVector -> SearchVectorDto.searchVector
 */
@AllArgsConstructor
@Getter
public class SearchVectorDto {

  /**
   * Primary key for persistence
   */
  @JsonProperty("searchdata_id")
  private final int searchDataId;

  /**
   * Foreign key referencing drawing
   */
  @JsonProperty("drawing_id")
  private final int drawingId;

  /**
   * Numerical vector for the search
   * including textual information from OCR and visual information of shapes
   */
  @JsonProperty("search_vector")
  private final float[] searchVector;
}
