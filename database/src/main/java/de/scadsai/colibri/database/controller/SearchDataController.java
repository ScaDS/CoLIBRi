package de.scadsai.colibri.database.controller;

import de.scadsai.colibri.database.exception.SearchDataNotFoundException;
import de.scadsai.colibri.database.dto.SearchDataDto;
import de.scadsai.colibri.database.entity.SearchData;
import de.scadsai.colibri.database.exception.SearchDataNotFoundForDrawingException;
import de.scadsai.colibri.database.service.SearchDataService;
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
@RequestMapping("/searchdata")
public class SearchDataController {

  /**
   * The autowired search data service bean
   */
  private final SearchDataService searchDataService;

  /**
   * The autowired entity-dto mapping service bean
   */
  private final DtoService dtoService;

  @Autowired
  public SearchDataController(SearchDataService searchDataService, DtoService dtoService) {
    this.searchDataService = searchDataService;
    this.dtoService = dtoService;
  }

  /**
   * REST request to save a search data entity
   *
   * @param searchDataDto Search data to save
   * @return Saved search data
   */
  @Operation(
    summary = "Save a search data object",
    description = "Saves a new search data and returns the saved search data."
  )
  @PostMapping(
    value = "/save",
    consumes = MediaType.APPLICATION_JSON_VALUE
  )
  @ResponseStatus(HttpStatus.CREATED)
  public SearchDataDto save(@RequestBody SearchDataDto searchDataDto) {
    SearchData searchData = dtoService.convertDtoToEntity(searchDataDto);
    SearchData searchDataSaved = searchDataService.saveSearchData(searchData);
    return dtoService.convertEntityToDto(searchDataSaved);
  }

  /**
   * REST request to save a given list of search data
   *
   * @param searchDataDtoList Search data to save
   * @return Saved search data
   */
  @Operation(
    summary = "Save multiple search data objects",
    description = "Saves a list of search data objects and returns the list of saved objects."
  )
  @PostMapping(
    value = "/save-all",
    consumes = MediaType.APPLICATION_JSON_VALUE
  )
  @ResponseStatus(HttpStatus.CREATED)
  public List<SearchDataDto> save(@RequestBody List<SearchDataDto> searchDataDtoList) {
    List<SearchData> searchDataList = searchDataDtoList.stream().map(dtoService::convertDtoToEntity).toList();
    List<SearchData> searchDataListSaved = searchDataService.saveSearchDataList(searchDataList);
    return searchDataListSaved.stream().map(dtoService::convertEntityToDto).toList();
  }

  /**
   * REST request to delete a search data for a given search data id
   *
   * @param id Search data id
   */
  @Operation(
    summary = "Delete a search data object by its ID",
    description = "Deletes a search data object based on its ID."
  )
  @DeleteMapping(value = "/delete/{id}")
  @ResponseStatus(HttpStatus.OK)
  public void deleteSearchDataById(@PathVariable("id") Integer id) {
    searchDataService.deleteSearchDataById(id);
  }

  /**
   * REST request to delete a search data for a given drawing id
   *
   * @param id Drawing id
   */
  @Operation(
    summary = "Delete search data by its associated drawing ID",
    description = "Deletes search data associated with a specific drawing ID."
  )
  @DeleteMapping(value = "/delete-for-drawing/{id}")
  @ResponseStatus(HttpStatus.OK)
  public void deleteSearchDataByDrawingId(@PathVariable("id") Integer id) {
    searchDataService.deleteSearchDataByDrawingId(id);
  }

  /**
   * REST request to retrieve search data for a given search data id
   *
   * @param id Search data id
   * @return Search data object, NOT_FOUND message if no results were found
   */
  @Operation(
    summary = "Retrieve a search data object by its ID",
    description = "Retrieves a search data object based on its ID. " +
      "Yields HttpStatus.NOT_FOUND if no search data object was found."
  )
  @GetMapping(
    value = "/get/{id}",
    produces = MediaType.APPLICATION_JSON_VALUE
  )
  public SearchDataDto getSearchDataById(@PathVariable("id") Integer id) {
    SearchData searchData = searchDataService.findSearchDataById(id);
    if (searchData == null) {
      throw new SearchDataNotFoundException(id);
    }
    return dtoService.convertEntityToDto(searchData);
  }

  /**
   * REST request to retrieve a search data for a given drawing id
   *
   * @param id Drawing id
   * @return Search data object, NOT_FOUND message if no results were found
   */
  @Operation(
    summary = "Retrieve search data by its associated drawing ID",
    description = "Retrieves a list of search data objects associated with a specific drawing ID." +
      "Yields HttpStatus.NOT_FOUND if no search data object was found."
  )
  @GetMapping(
    value = "/get-for-drawing/{id}",
    produces = MediaType.APPLICATION_JSON_VALUE
  )
  public SearchDataDto getSearchDataByDrawingId(@PathVariable("id") Integer id) {
    SearchData searchData = searchDataService.findSearchDataByDrawingId(id);
    if (searchData == null) {
      throw new SearchDataNotFoundForDrawingException(id);
    }
    return dtoService.convertEntityToDto(searchData);
  }

  /**
   * REST request to retrieve all search data
   *
   * @return List of search data objects, empty if no results were found
   */
  @Operation(
    summary = "Retrieve all search data",
    description = "Retrieves a list of all search data objects. " +
      "Yields an empty list if no search data objects were found."
  )
  @GetMapping(
    value = "/get-all",
    produces = MediaType.APPLICATION_JSON_VALUE
  )
  public List<SearchDataDto> getAllSearchData() {
    List<SearchData> searchDataList = searchDataService.findAllSearchData();
    return searchDataList.stream().map(dtoService::convertEntityToDto).toList();
  }
}
