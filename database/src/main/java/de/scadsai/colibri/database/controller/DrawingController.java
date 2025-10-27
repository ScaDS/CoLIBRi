package de.scadsai.colibri.database.controller;

import de.scadsai.colibri.database.exception.DrawingNotFoundException;
import de.scadsai.colibri.database.dto.DrawingDto;
import de.scadsai.colibri.database.entity.Drawing;
import de.scadsai.colibri.database.service.DrawingService;
import de.scadsai.colibri.database.service.DtoService;
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
@RequestMapping("/drawing")
public class DrawingController {

  /**
   * The autowired drawing service bean
   */
  private final DrawingService drawingService;

  /**
   * The autowired entity-dto mapping service bean
   */
  private final DtoService dtoService;

  @Autowired
  public DrawingController(DrawingService drawingService, DtoService dtoService) {
    this.drawingService = drawingService;
    this.dtoService = dtoService;
  }

  /**
   * REST request to save a given drawing
   *
   * @param drawingDto Drawing to save
   * @return Saved drawing
   */
  @Operation(
    summary = "Save a drawing",
    description = "Saves a new drawing and returns the saved drawing."
  )
  @PostMapping(
    value = "/save",
    consumes = MediaType.APPLICATION_JSON_VALUE
  )
  @ResponseStatus(HttpStatus.CREATED)
  public DrawingDto save(@RequestBody DrawingDto drawingDto) {
    Drawing drawing = dtoService.convertDtoToEntity(drawingDto);
    Drawing drawingSaved = drawingService.saveDrawing(drawing);
    return dtoService.convertEntityToDto(drawingSaved);
  }

  /**
   * REST request to save a given list of drawings
   *
   * @param drawingDtoList Drawings to save
   * @return Saved drawings
   */
  @Operation(
    summary = "Save multiple drawings",
    description = "Saves a list of drawings and returns the list of saved drawings."
  )
  @PostMapping(
    value = "/save-all",
    consumes = MediaType.APPLICATION_JSON_VALUE
  )
  @ResponseStatus(HttpStatus.CREATED)
  public List<DrawingDto> save(@RequestBody List<DrawingDto> drawingDtoList) {
    List<Drawing> drawingList = drawingDtoList.stream().map(dtoService::convertDtoToEntity).toList();
    List<Drawing> drawingsSaved = drawingService.saveDrawings(drawingList);
    return drawingsSaved.stream().map(dtoService::convertEntityToDto).toList();
  }

  /**
   * REST request to delete a drawing for a given drawing id
   *
   * @param id Drawing id
   */
  @Operation(
    summary = "Delete a drawing by its ID",
    description = "Deletes a drawing based on its ID."
  )
  @DeleteMapping(value = "/delete/{id}")
  @ResponseStatus(HttpStatus.OK)
  public void deleteDrawingById(@PathVariable("id") Integer id) {
    drawingService.deleteDrawingById(id);
  }

  /**
   * REST request to retrieve drawing data for a given drawing id
   *
   * @param id Drawing id
   * @return Drawing object, NOT_FOUND message if no results were found
   */
  @Operation(
    summary = "Retrieve a drawing by its ID",
    description = "Retrieves a drawing based on its ID. " +
      "Yields HttpStatus.NOT_FOUND if no drawing was found."
  )
  @GetMapping(
    value = "/get/{id}",
    produces = MediaType.APPLICATION_JSON_VALUE
  )
  public DrawingDto getDrawingById(@PathVariable("id") Integer id) {
    Drawing drawing = drawingService.findDrawingById(id);
    if (drawing == null) {
      throw new DrawingNotFoundException(id);
    }
    return dtoService.convertEntityToDto(drawing);
  }

  /**
   * REST request to retrieve drawing data for all drawings
   *
   * @return List of drawing objects, empty if no results were found
   */
  @Operation(
    summary = "Retrieve all drawings",
    description = "Retrieves a list of all drawings. Yields an empty list if no drawings were found."
  )
  @GetMapping(
    value = "/get-all",
    produces = MediaType.APPLICATION_JSON_VALUE
  )
  public List<DrawingDto> getAllDrawings() {
    List<Drawing> drawings = drawingService.findAllDrawings();
    return drawings.stream().map(dtoService::convertEntityToDto).toList();
  }
}
