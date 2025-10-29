package de.scadsai.colibri.database.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Table;
import jakarta.persistence.OneToMany;
import jakarta.persistence.CascadeType;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;
import java.util.ArrayList;

import java.time.LocalDateTime;

@Entity
@Table(name = "history")
@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
public class History {

  /**
   * Primary key for persistence
   */
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY) // Auto-incrementing ID
  @Column(name = "history_id")
  private Integer historyId;

  /**
   * Byte array representation of the query drawing
   */
  @Column(
    name = "query_drawing",
    columnDefinition = "bytea"
  )
  private byte[] queryDrawing;

  /**
   * Input path (filename) of the query drawing
   */
  @Column(
    name = "query_path",
    columnDefinition = "text"
  )
  private String queryPath;

  /**
   * Timestamp of the search
   */
  @Column(
    name = "timestamp",
    columnDefinition = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
  )
  private LocalDateTime timestamp;

  /**
   * List of related feedbacks
   */
  @OneToMany(
    mappedBy = "history",
    cascade = CascadeType.ALL,
    orphanRemoval = true
  )
  private List<Feedback> feedbacks = new ArrayList<>();

  /**
   * Helper Method to update feedbacks
   *
   * @param feedback Feedback to add to the list of related feedbacks
   */
  public void addFeedback(Feedback feedback) {
    feedback.setHistory(this);
    feedbacks.add(feedback);
  }
}
