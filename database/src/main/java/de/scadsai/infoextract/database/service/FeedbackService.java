package de.scadsai.infoextract.database.service;

import de.scadsai.infoextract.database.entity.Feedback;

import java.util.List;

public interface FeedbackService {

  /**
   * Store a feedback entity to the database
   *
   * @param feedback Feedback entity
   * @return The stored feedback entity
   */
  Feedback saveFeedback(Feedback feedback);

  /**
   * Store a collection of feedback entities to the database
   *
   * @param feedbacks Collection of feedback entities
   * @return The stored collection of feedback entities
   */
  List<Feedback> saveFeedbacks(List<Feedback> feedbacks);

  /**
   * Retrieve a feedback entity from the database by its id
   * @param id Feedback id
   * @return Feedback entity
   */
  Feedback findFeedbackById(int id);

   /**
   * Retrieve all feedback entities from the database by its referencing history id
   * @param id History id
   * @return Collection of all feedback entities
   */
  List<Feedback> findFeedbacksByHistoryId(int id);

  /**
   * Retrieve all feedback entities from the database
   * @return Collection of all feedback entities
   */
  List<Feedback> findAllFeedbacks();

  /**
   * Delete a feedback entity from the database by its id
   * @param id Feedback id
   */
  void deleteFeedbackById(int id);
}
