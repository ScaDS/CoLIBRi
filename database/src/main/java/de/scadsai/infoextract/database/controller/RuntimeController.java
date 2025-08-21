package de.scadsai.infoextract.database.controller;

import de.scadsai.infoextract.database.exception.RuntimeNotFoundException;
import de.scadsai.infoextract.database.dto.RuntimeDto;
import de.scadsai.infoextract.database.entity.Runtime;
import de.scadsai.infoextract.database.exception.RuntimesNotFoundForDrawingException;
import de.scadsai.infoextract.database.service.RuntimeService;
import de.scadsai.infoextract.database.service.DtoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

import io.swagger.v3.oas.annotations.Operation;

@RestController
@RequestMapping("/runtime")
public class RuntimeController {

  /**
   * The autowired runtime service bean
   */
  private final RuntimeService runtimeService;

  /**
   * The autowired entity-dto mapping service bean
   */
  private final DtoService dtoService;

  @Autowired
  public RuntimeController(RuntimeService runtimeService, DtoService dtoService) {
    this.runtimeService = runtimeService;
    this.dtoService = dtoService;
  }

  /**
   * REST request to save a runtime entity
   *
   * @param runtimeDto Runtime to save
   * @return Saved runtime
   */
  @Operation(
    summary = "Save a runtime object",
    description = "Saves a new runtime and returns the saved runtime."
  )
  @PostMapping(
    value = "/save",
    consumes = MediaType.APPLICATION_JSON_VALUE
  )
  @ResponseStatus(HttpStatus.CREATED)
  public RuntimeDto save(@RequestBody RuntimeDto runtimeDto) {
    Runtime runtime = dtoService.convertDtoToEntity(runtimeDto);
    Runtime runtimeSaved = runtimeService.saveRuntime(runtime);
    return dtoService.convertEntityToDto(runtimeSaved);
  }

  /**
   * REST request to save a given list of runtimes
   *
   * @param runtimeDtoList Runtimes to save
   * @return Saved runtimes
   */
  @Operation(
    summary = "Save multiple runtimes",
    description = "Saves a list of runtimes and returns the list of saved runtimes."
  )
  @PostMapping(
    value = "/save-all",
    consumes = MediaType.APPLICATION_JSON_VALUE
  )
  @ResponseStatus(HttpStatus.CREATED)
  public List<RuntimeDto> save(@RequestBody List<RuntimeDto> runtimeDtoList) {
    List<Runtime> runtimeList = runtimeDtoList.stream().map(dtoService::convertDtoToEntity).toList();
    List<Runtime> runtimesSaved = runtimeService.saveRuntimes(runtimeList);
    return runtimesSaved.stream().map(dtoService::convertEntityToDto).toList();
  }

  /**
   * REST request to delete a runtime for a given runtime id
   *
   * @param id Runtime id
   */
  @Operation(
    summary = "Delete a runtime by its ID",
    description = "Deletes a runtime based on its ID."
  )
  @DeleteMapping(value = "/delete/{id}")
  @ResponseStatus(HttpStatus.OK)
  public void deleteRuntimeById(@PathVariable("id") Integer id) {
    runtimeService.deleteRuntimeById(id);
  }

  /**
   * REST request to delete all runtimes for a given drawing id
   *
   * @param id Drawing id
   */
  @Operation(
    summary = "Delete runtimes by ist associated drawing ID",
    description = "Deletes all runtimes associated with a specific drawing ID."
  )
  @DeleteMapping(value = "/delete-for-drawing/{id}")
  @ResponseStatus(HttpStatus.OK)
  public void deleteRuntimesByDrawingId(@PathVariable("id") Integer id) {
    runtimeService.deleteRuntimesByDrawingId(id);
  }

  /**
   * REST request to retrieve runtime data for a given runtime id
   *
   * @param id Runtime id
   * @return Runtime object, NOT_FOUND message if no results were found
   */
  @Operation(
    summary = "Retrieve a runtime by its ID",
    description = "Retrieves a runtime based on its ID. " +
      "Yields HttpStatus.NOT_FOUND if no runtime was found."
  )
  @GetMapping(
    value = "/get/{id}",
    produces = MediaType.APPLICATION_JSON_VALUE
  )
  public RuntimeDto getRuntimeById(@PathVariable("id") Integer id) {
    Runtime runtime = runtimeService.findRuntimeById(id);
    if (runtime == null) {
      throw new RuntimeNotFoundException(id);
    }
    return dtoService.convertEntityToDto(runtime);
  }

  /**
   * REST request to retrieve all runtimes for a given drawing id
   *
   * @param id Drawing id
   * @return List of runtime objects, empty if no results were found
   */
  @Operation(
    summary = "Retrieve runtimes by their associated drawing ID",
    description = "Retrieves a list of all runtimes associated with a specific drawing ID." +
      "Yields HttpStatus.NOT_FOUND if no runtime was found."
  )
  @GetMapping(
    value = "/get-for-drawing/{id}",
    produces = MediaType.APPLICATION_JSON_VALUE
  )
  public List<RuntimeDto> getRuntimesByDrawingId(@PathVariable("id") Integer id) {
    List<Runtime> runtimes = runtimeService.findRuntimesByDrawingId(id);
    if (runtimes == null || runtimes.isEmpty()) {
      throw new RuntimesNotFoundForDrawingException(id);
    }
    return runtimes.stream().map(dtoService::convertEntityToDto).toList();
  }

  /**
   * REST request to retrieve all runtimes
   *
   * @return List of runtime objects, empty if no results were found
   */
  @Operation(
    summary = "Retrieve all runtimes",
    description = "Retrieves a list of all runtimes." +
      "Yields an empty list if no runtimes were found."
  )
  @GetMapping(
    value = "/get-all",
    produces = MediaType.APPLICATION_JSON_VALUE
  )
  public List<RuntimeDto> getAllRuntimes() {
    List<Runtime> runtimes = runtimeService.findAllRuntimes();
    return runtimes.stream().map(dtoService::convertEntityToDto).toList();
  }
}
