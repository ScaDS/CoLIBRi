package de.scadsai.infoextract.database.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.OneToMany;
import jakarta.persistence.CascadeType;
import jakarta.persistence.OneToOne;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Entity
@Table(name = "drawings")
@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
public class Drawing {

  /**
   * Primary key for persistence
   */
  @Id
  @Column(name = "drawing_id")
  private Integer drawingId;

  /**
   * Byte array representation of the drawing
   */
  @Column(
    name = "original_drawing",
    columnDefinition = "bytea"
  )
  private byte[] originalDrawing;

  /**
   * List of related runtimes
   */
  @OneToMany(
    mappedBy = "drawing",
    cascade = CascadeType.ALL,
    orphanRemoval = true
  )
  private List<Runtime> runtimes;

  /**
   * Related search data
   */
  @OneToOne(
    mappedBy = "drawing",
    cascade = CascadeType.ALL,
    orphanRemoval = true
  )
  private SearchData searchData;

  /**
   * List of related feedbacks
   */
  @OneToMany(
    mappedBy = "drawing",
    cascade = CascadeType.ALL
  )
  private List<Feedback> feedbacks;
}
