package de.scadsai.infoextract.database.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * Data transfer object for {@link de.scadsai.infoextract.database.entity.Runtime}.
 */
/*
 * The following fields are transferred:
 *  Runtime.runtimeId -> RuntimeDto.runtimeId
 *  Runtime.drawingId -> RuntimeDto.drawingId
 *  Runtime.machine -> RuntimeDto.machine
 *  Runtime.runtime -> RuntimeDto.runtime
 */
@AllArgsConstructor
@Getter
public class RuntimeDto {

  /**
   * Primary key for persistence
   */
  @JsonProperty("runtime_id")
  private final int runtimeId;

   /**
   * Foreign key referencing drawing
   */
  @JsonProperty("drawing_id")
  private final int drawingId;

  /**
   * Machine used for the manufacturing
   */
  @JsonProperty("machine")
  private final String machine;

  /**
   * Runtime of the machine
   */
  @JsonProperty("machine_runtime")
  private final float machineRuntime;
}
