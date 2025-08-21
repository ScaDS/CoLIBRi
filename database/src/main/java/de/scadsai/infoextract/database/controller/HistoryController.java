package de.scadsai.infoextract.database.controller;

import de.scadsai.infoextract.database.dto.HistoryDto;
import de.scadsai.infoextract.database.entity.History;
import de.scadsai.infoextract.database.exception.HistoryNotFoundException;
import de.scadsai.infoextract.database.service.HistoryService;
import de.scadsai.infoextract.database.service.DtoService;
import io.swagger.v3.oas.annotations.Operation;
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

@RestController
@RequestMapping("/history")
public class HistoryController {

  /**
   * The autowired history service bean
   */
  private final HistoryService historyService;

  /**
   * The autowired entity-dto mapping service bean
   */
  private final DtoService dtoService;

  @Autowired
  public HistoryController(HistoryService historyService, DtoService dtoService) {
    this.historyService = historyService;
    this.dtoService = dtoService;
  }

  /**
   * REST request to save a given history
   *
   * @param historyDto History to save
   * @return Saved history
   */
  @Operation(
    summary = "Save a history",
    description = "Saves a new history and returns the saved history."
  )
  @PostMapping(
    value = "/save",
    consumes = MediaType.APPLICATION_JSON_VALUE
  )
  @ResponseStatus(HttpStatus.CREATED)
  public HistoryDto save(@RequestBody HistoryDto historyDto) {
    History history = dtoService.convertDtoToEntity(historyDto);
    History historySaved = historyService.saveHistory(history);
    return dtoService.convertEntityToDto(historySaved);
  }

  /**
   * REST request to save a given list of histories
   *
   * @param historyDtoList Histories to save
   * @return Saved histories
   */
  @Operation(
    summary = "Save multiple histories",
    description = "Saves a list of histories and returns the list of saved histories."
  )
  @PostMapping(
    value = "/save-all",
    consumes = MediaType.APPLICATION_JSON_VALUE
  )
  @ResponseStatus(HttpStatus.CREATED)
  public List<HistoryDto> save(@RequestBody List<HistoryDto> historyDtoList) {
    List<History> historyList = historyDtoList.stream().map(dtoService::convertDtoToEntity).toList();
    List<History> historiesSaved = historyService.saveHistories(historyList);
    return historiesSaved.stream().map(dtoService::convertEntityToDto).toList();
  }

  /**
   * REST request to delete a history for a given history id
   *
   * @param id History id
   */
  @Operation(
    summary = "Delete a history by its ID",
    description = "Deletes a history based on its ID."
  )
  @DeleteMapping(value = "/delete/{id}")
  @ResponseStatus(HttpStatus.OK)
  public void deleteHistoryById(@PathVariable("id") Integer id) {
    historyService.deleteHistoryById(id);
  }

  /**
   * REST request to retrieve history data for a given history id
   *
   * @param id History id
   * @return History, NOT_FOUND message if no results were found
   */
  @Operation(
    summary = "Retrieve a history by its ID",
    description = "Retrieves a history based on its ID. " +
      "Yields HttpStatus.NOT_FOUND if no history was found."
  )
  @GetMapping(
    value = "/get/{id}",
    produces = MediaType.APPLICATION_JSON_VALUE
  )
  public HistoryDto getHistoryById(@PathVariable("id") Integer id) {
    History history = historyService.findHistoryById(id);
    if (history == null) {
      throw new HistoryNotFoundException(id);
    }
    return dtoService.convertEntityToDto(history);
  }

  /**
   * REST request to retrieve history data for all histories
   *
   * @return List of histories, empty if no results were found
   */
  @Operation(
    summary = "Retrieve all histories",
    description = "Retrieves a list of all histories. Yields an empty list if no histories were found."
  )
  @GetMapping(
    value = "/get-all",
    produces = MediaType.APPLICATION_JSON_VALUE
  )
  public List<HistoryDto> getAllHistories() {
    List<History> histories = historyService.findAllHistories();
    return histories.stream().map(dtoService::convertEntityToDto).toList();
  }
}
