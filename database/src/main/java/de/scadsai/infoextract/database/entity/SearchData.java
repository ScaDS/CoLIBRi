package de.scadsai.infoextract.database.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.OneToOne;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "searchdata")
@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
public class SearchData {

  /**
   * Primary key for persistence
   */
  @Id
  @Column(name = "searchdata_id")
  private int searchDataId;

  /**
   * Drawing referenced by foreign key drawing_id
   */
  @OneToOne(fetch = FetchType.EAGER)
  @JoinColumn(name = "drawing_id")
  private Drawing drawing;

  /**
   * Numerical vector to represent shapes
   */
  @Column(
    name = "shape",
    columnDefinition = "float ARRAY"
  )
  private float[] shape;

  /**
   * Material(s) used for the manufacturing
   */
  @Column(
    name = "material",
    columnDefinition = "text ARRAY"
  )
  private String[] material;

  /**
   * General tolerance standards / tolerance classes
   */
  @Column(
    name = "general_tolerances",
    columnDefinition = "text ARRAY"
  )
  private String[] generalTolerances;

  /**
   * Surface roughness required on the finished surfaces
   */
  @Column(
    name = "surfaces",
    columnDefinition = "text ARRAY"
  )
  private String[] surfaces;

  /**
   * Geometric Dimensioning and Tolerancing (GD&T)
   */
  @Column(
    name = "gdts",
    columnDefinition = "text ARRAY"
  )
  private String[] gdts;

  /**
   * Thread readings
   */
  @Column(
    name = "threads",
    columnDefinition = "text ARRAY"
  )
  private String[] threads;

  /**
   * Maximal measures for each spatial dimension
   */
  @Column(
    name = "outer_dimensions",
    columnDefinition = "float ARRAY"
  )
  private float[] outerDimensions;

  /**
   * Numerical vector for the search
   * including textual information from OCR and visual information of shapes
   */
  @Column(
    name = "search_vector",
    columnDefinition = "float ARRAY"
  )
  private float[] searchVector;

  /**
   * Part number used to reference drawings (parts)
   */
  @Column(
    name = "part_number",
    columnDefinition = "text"
  )
  private String partNumber;

  /**
   * Full OCR text
   */
  @Column(
    name = "ocr_text",
    columnDefinition = "text ARRAY"
  )
  private String[] ocrText;

  /**
   * Text field containing information on machines and runtimes
   */
  @Column(
    name = "runtime_text",
    columnDefinition = "text"
  )
  private String runtimeText;

   /**
   * Text field used for llm
   */
  @Column(
    name = "llm_text",
    columnDefinition = "text"
  )
  private String llmText;

   /**
   * Numerical text embedding used for llm
   */
  @Column(
    name = "llm_vector",
    columnDefinition = "float ARRAY"
  )
  private float[] llmVector;
}
