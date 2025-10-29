package de.scadsai.colibri.database.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Table;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "feedbacks")
@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
public class Feedback {

  /**
   * Primary key for persistence
   */
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY) // Auto-incrementing ID
  @Column(name = "feedback_id")
  private Integer feedbackId;

  /**
   * History referenced by foreign key history_id
   */
  @ManyToOne(fetch = FetchType.EAGER)
  @JoinColumn(name = "history_id")
  private History history;

  /**
   * Drawing referenced by foreign key drawing_id
   */
  @ManyToOne(fetch = FetchType.EAGER)
  @JoinColumn(name = "drawing_id")
  private Drawing drawing;

  /**
   * The description (reason) of the feedback
   */
  @Column(
    name = "feedback_desc",
    columnDefinition = "text"
  )
  private String feedbackDesc;

  /**
   * The value of the feedback
   * Allowed values:
   * 0 - Negative feedback (no match)
   * 1 - Neutral feedback (uncertain)
   * 2 - Positive feedback (match)
   */
  @Column(
    name = "feedback_value",
    columnDefinition = "INTEGER"
  )
  private int feedbackValue;
}
