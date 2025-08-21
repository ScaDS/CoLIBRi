package de.scadsai.infoextract.database.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * Data transfer object for {@link de.scadsai.infoextract.database.entity.SearchData}.
 */
/*
 * The following fields are transferred:
 *  SearchData.searchDataId -> SearchDataDto.searchDataId
 *  SearchData.drawing -> SearchDataDto.drawingID
 *  SearchData.shape -> SearchDataDto.shape
 *  SearchData.material -> SearchDataDto.material
 *  SearchData.generalTolerances -> SearchDataDto.generalTolerances
 *  SearchData.surfaces -> SearchDataDto.surfaces
 *  SearchData.gdts -> SearchDataDto.gdts
 *  SearchData.threads -> SearchDataDto.threads
 *  SearchData.outerDimensions -> SearchDataDto.outer_dimensions
 *  SearchData.searchVector -> SearchDataDto.searchVector
 *  SearchData.partNumber -> SearchDataDto.partNumber
 *  SearchData.ocrText -> SearchDataDto.ocrText
 *  SearchData.runtimeText -> SearchDataDto.runtimeText
 */
@AllArgsConstructor
@Getter
public class SearchDataDto {

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
   * Numerical vector to represent shapes
   */
  @JsonProperty("shape")
  private final float[] shape;

  /**
   * Material(s) used for the manufacturing
   */
  @JsonProperty("material")
  private final String[] material;

  /**
   * General tolerance standards / tolerance classes
   */
  @JsonProperty("general_tolerances")
  private final String[] generalTolerances;

  /**
   * Surface roughnesses required on the finished surfaces
   */
  @JsonProperty("surfaces")
  private final String[] surfaces;

  /**
   * Geometric Dimensioning and Tolerancing (GD&T)
   */
  @JsonProperty("gdts")
  private final String[] gdts;

  /**
   * Thread readings
   */
  @JsonProperty("threads")
  private final String[] threads;

  /**
   * Maximal measures for each spatial dimension
   */
  @JsonProperty("outer_dimensions")
  private final float[] outerDimensions;

  /**
   * Numerical vector for the search
   * including textual information from OCR and visual information of shapes
   */
  @JsonProperty("search_vector")
  private final float[] searchVector;

  /**
   * Part number to reference drawings (parts)
   */
  @JsonProperty("part_number")
  private final String partNumber;

  /**
   * Full OCR text
   */
  @JsonProperty("ocr_text")
  private final String[] ocrText;

  /**
   * Text field containing information on machines and runtimes
   */
  @JsonProperty("runtime_text")
  private final String runtimeText;
}
