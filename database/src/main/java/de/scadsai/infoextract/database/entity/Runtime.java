package de.scadsai.infoextract.database.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "runtimes")
@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
public class Runtime {

  /**
   * Primary key for persistence
   */
  @Id
  @Column(name = "runtime_id")
  private int runtimeId;

  /**
   * Drawing referenced by foreign key drawing_id
   */
  @ManyToOne(fetch = FetchType.EAGER)
  @JoinColumn(name = "drawing_id")
  private Drawing drawing;

  /**
   * Machine used for the manufacturing
   */
  @Column(
    name = "machine",
    columnDefinition = "text"
  )
  private String machine;

  /**
   * Runtime of the machine
   */
  @Column(
    name = "machine_runtime",
    columnDefinition = "real"
  )
  private float machineRuntime;
}
