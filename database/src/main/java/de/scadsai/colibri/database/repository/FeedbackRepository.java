package de.scadsai.colibri.database.repository;

import de.scadsai.colibri.database.entity.Feedback;
import org.springframework.data.repository.CrudRepository;

public interface FeedbackRepository extends CrudRepository<Feedback, Integer> {

  /**
   * Retrieve all feedbacks for a given history referenced by its history id
   * @param historyId History id
   * @return Feedbacks for a given history
   */
  Iterable<Feedback> findFeedbacksByHistoryHistoryId(int historyId);
}
