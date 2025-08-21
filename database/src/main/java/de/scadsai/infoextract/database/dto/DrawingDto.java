package de.scadsai.infoextract.database.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;

import java.util.List;

/**
 * Data transfer object for {@link de.scadsai.infoextract.database.entity.Drawing}.
 */
/*
 * The following fields are transferred:
 *  Drawing.drawingId -> DrawingDto.drawingId
 *  Drawing.originalDrawing -> DrawingDto.originalDrawing
 *  Drawing.runtimes -> DrawingDto.runtimes
 *  Drawing.searchData -> DrawingDto.searchData
 */
@AllArgsConstructor
@Getter
public class DrawingDto {

  /**
   * Primary key for persistence
   */
  @JsonProperty("drawing_id")
  private final int drawingId;

  /**
   * Base64 string-encoding of the byte array representation for the drawing
   */
  @JsonProperty("original_drawing")
  private final String originalDrawing;

  /**
   * List of related runtime DTOs
   */
  @JsonProperty("runtimes")
  private List<RuntimeDto> runtimes;

   /**
   * Related search data DTO
   */
  @JsonProperty("searchdata")
  private SearchDataDto searchData;

  /**
   * Related feedback DTO
   */
  @JsonProperty("feedbacks")
  private List<FeedbackDto> feedbacks;
}
