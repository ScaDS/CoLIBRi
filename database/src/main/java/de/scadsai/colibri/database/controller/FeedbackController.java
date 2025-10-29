package de.scadsai.colibri.database.controller;

import de.scadsai.colibri.database.dto.FeedbackDto;
import de.scadsai.colibri.database.entity.Feedback;
import de.scadsai.colibri.database.exception.FeedbackNotFoundException;
import de.scadsai.colibri.database.exception.FeedbacksNotFoundForHistoryException;
import de.scadsai.colibri.database.service.DtoService;
import de.scadsai.colibri.database.service.FeedbackService;
import io.swagger.v3.oas.annotations.Operation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import java.util.List;

@RestController
@RequestMapping("/feedback")
public class FeedbackController {

  /**
   * The autowired feedback service bean
   */
  private final FeedbackService feedbackService;

  /**
   * The autowired entity-dto mapping service bean
   */
  private final DtoService dtoService;

  @Autowired
  public FeedbackController(FeedbackService feedbackService, DtoService dtoService) {
    this.feedbackService = feedbackService;
    this.dtoService = dtoService;
  }

  /**
   * REST request to save a feedback entity
   *
   * @param feedbackDto Feedback to save
   * @return Saved feedback
   */
  @Operation(
    summary = "Save a feedback object",
    description = "Saves a new feedback and returns the saved feedback."
  )
  @PostMapping(
    value = "/save",
    consumes = MediaType.APPLICATION_JSON_VALUE
  )
  @ResponseStatus(HttpStatus.CREATED)
  public FeedbackDto save(@RequestBody FeedbackDto feedbackDto) {
    Feedback feedback = dtoService.convertDtoToEntity(feedbackDto);
    Feedback feedbackSaved = feedbackService.saveFeedback(feedback);
    return dtoService.convertEntityToDto(feedbackSaved);
  }

  /**
   * REST request to save a given list of feedbacks
   *
   * @param feedbackDtoList Runtimes to save
   * @return Saved feedbacks
   */
  @Operation(
    summary = "Save multiple feedbacks",
    description = "Saves a list of feedbacks and returns the list of saved feedbacks."
  )
  @PostMapping(
    value = "/save-all",
    consumes = MediaType.APPLICATION_JSON_VALUE
  )
  @ResponseStatus(HttpStatus.CREATED)
  public List<FeedbackDto> save(@RequestBody List<FeedbackDto> feedbackDtoList) {
    List<Feedback> feedbackList = feedbackDtoList.stream().map(dtoService::convertDtoToEntity).toList();
    List<Feedback> feedbacksSaved = feedbackService.saveFeedbacks(feedbackList);
    return feedbacksSaved.stream().map(dtoService::convertEntityToDto).toList();
  }

  /**
   * REST request to delete a feedback for a given feedback id
   *
   * @param id Feedback id
   */
  @Operation(
    summary = "Delete a feedback by its ID",
    description = "Deletes a feedback based on its ID."
  )
  @DeleteMapping(value = "/delete/{id}")
  @ResponseStatus(HttpStatus.OK)
  public void deleteFeedbackById(@PathVariable("id") Integer id) {
    feedbackService.deleteFeedbackById(id);
  }

  /**
   * REST request to retrieve feedback data for a given feedback id
   *
   * @param id Feedback id
   * @return Feedback object, NOT_FOUND message if no results were found
   */
  @Operation(
    summary = "Retrieve a feedback by its ID",
    description = "Retrieves a feedback based on its ID. " +
      "Yields HttpStatus.NOT_FOUND if no feedback was found."
  )
  @GetMapping(
    value = "/get/{id}",
    produces = MediaType.APPLICATION_JSON_VALUE
  )
  public FeedbackDto getFeedbackById(@PathVariable("id") Integer id) {
    Feedback feedback = feedbackService.findFeedbackById(id);
    if (feedback == null) {
      throw new FeedbackNotFoundException(id);
    }
    return dtoService.convertEntityToDto(feedback);
  }

  /**
   * REST request to retrieve all feedbacks for a given history id
   *
   * @param id  id
   * @return List of feedback objects, empty if no results were found
   */
  @Operation(
    summary = "Retrieve feedbacks by their associated history ID",
    description = "Retrieves a list of all feedbacks associated with a specific history ID." +
      "Yields HttpStatus.NOT_FOUND if no feedback was found."
  )
  @GetMapping(
    value = "/get-for-history/{id}",
    produces = MediaType.APPLICATION_JSON_VALUE
  )
  public List<FeedbackDto> getFeedbacksByHistoryId(@PathVariable("id") Integer id) {
    List<Feedback> feedbacks = feedbackService.findFeedbacksByHistoryId(id);
    if (feedbacks == null || feedbacks.isEmpty()) {
      throw new FeedbacksNotFoundForHistoryException(id);
    }
    return feedbacks.stream().map(dtoService::convertEntityToDto).toList();
  }

  /**
   * REST request to retrieve all feedbacks
   *
   * @return List of feedback objects, empty if no results were found
   */
  @Operation(
    summary = "Retrieve all feedbacks",
    description = "Retrieves a list of all feedbacks." +
      "Yields an empty list if no feedbacks were found."
  )
  @GetMapping(
    value = "/get-all",
    produces = MediaType.APPLICATION_JSON_VALUE
  )
  public List<FeedbackDto> getAllFeedbacks() {
    List<Feedback> feedbacks = feedbackService.findAllFeedbacks();
    return feedbacks.stream().map(dtoService::convertEntityToDto).toList();
  }
}
