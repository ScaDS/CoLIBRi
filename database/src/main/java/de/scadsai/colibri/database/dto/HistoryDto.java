package de.scadsai.colibri.database.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import de.scadsai.colibri.database.entity.History;
import lombok.AllArgsConstructor;
import lombok.Getter;

import java.time.LocalDateTime;
import java.util.List;
import java.util.ArrayList;

import io.swagger.v3.oas.annotations.media.Schema;

/**
 * Data transfer object for {@link History}.
 */
/*
 * The following fields are transferred:
 *  History.historyId -> HistoryDto.historyId
 *  History.queryDrawing -> HistoryDto.queryDrawing
 *  History.queryPath -> HistoryDto.queryPath
 *  History.timestamp -> HistoryDto.timestamp
 */
@AllArgsConstructor
@Getter
public class HistoryDto {

  /**
   * Primary key for persistence
   */
  @JsonProperty("history_id")
  @Schema(accessMode = Schema.AccessMode.READ_ONLY)
  private final Integer historyId;

  /**
   * Base64 string-encoding of the byte array representation for the query drawing
   */
  @JsonProperty("query_drawing")
  private final String queryDrawing;

  /**
   * Input path (filename) of the query drawing
   */
  @JsonProperty("query_path")
  private String queryPath;

   /**
   * Timestamp of the search
   */
  @JsonProperty("timestamp")
  @Schema(accessMode = Schema.AccessMode.READ_ONLY)
  private LocalDateTime timestamp;

  /**
   * Related feedback DTO
   */
  @JsonProperty("feedbacks")
  @Schema(accessMode = Schema.AccessMode.READ_ONLY)
  private List<FeedbackDto> feedbacks;

  @JsonCreator
  public HistoryDto(
    @JsonProperty("query_drawing") String queryDrawing,
    @JsonProperty("query_path") String queryPath
  ) {
    this.historyId = null;
    this.queryDrawing = queryDrawing;
    this.queryPath = queryPath;
    this.timestamp = LocalDateTime.now();
    this.feedbacks = new ArrayList<>();
  }
}
