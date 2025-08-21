package de.scadsai.infoextract.database.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import lombok.AllArgsConstructor;
import lombok.Getter;

import io.swagger.v3.oas.annotations.media.Schema;

/**
 * Data transfer object for {@link de.scadsai.infoextract.database.entity.Feedback}.
 */
/*
 * The following fields are transferred:
 *  Feedback.feedbackId -> Feedback.feedbackId
 *  Feedback.historyId -> FeedbackDto.historyId
 *  Feedback.drawingId -> FeedbackDto.drawingId
 *  Feedback.feedbackDesc -> FeedbackDto.feedbackDesc
 *  Feedback.feedbackValue -> FeedbackDto.feedbackValue
 */
@AllArgsConstructor
@Getter
public class FeedbackDto {

  /**
   * Primary key for persistence
   */
  @JsonProperty("feedback_id")
  @Schema(accessMode = Schema.AccessMode.READ_ONLY)
  private final Integer feedbackId;

  /**
   * Foreign key referencing history
   */
  @JsonProperty("history_id")
  private final int historyId;

   /**
   * Foreign key referencing drawing
   */
  @JsonProperty("drawing_id")
  private final int drawingId;

  /**
   * The description (reason) of the feedback
   */
  @JsonProperty("feedback_desc")
  private final String feedbackDesc;

  /**
   * The value of the feedback
   * Allowed values:
   * 0 - Negative feedback (no match)
   * 1 - Neutral feedback (uncertain)
   * 2 - Positive feedback (match)
   */
  @JsonProperty("feedback_value")
  private final int feedbackValue;

  @JsonCreator
  public FeedbackDto(
    @JsonProperty("history_id") int historyId,
    @JsonProperty("drawing_id") int drawingId,
    @JsonProperty("feedback_desc") String feedbackDesc,
    @JsonProperty("feedback_value") int feedbackValue) {
    this.feedbackId = null;
    this.historyId = historyId;
    this.drawingId = drawingId;
    this.feedbackDesc = feedbackDesc;
    this.feedbackValue = feedbackValue;
  }
}
