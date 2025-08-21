package de.scadsai.infoextract.database.service;

import de.scadsai.infoextract.database.entity.Feedback;
import de.scadsai.infoextract.database.entity.History;
import de.scadsai.infoextract.database.exception.DrawingNotFoundException;
import de.scadsai.infoextract.database.repository.FeedbackRepository;
import de.scadsai.infoextract.database.repository.HistoryRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataAccessException;
import org.springframework.data.util.Streamable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class FeedbackServiceImpl implements FeedbackService {

  /**
   * The autowired repository for the feedback
   */
  private final FeedbackRepository feedbackRepository;

  /**
   * The autowired repository for the history
   */
  private final HistoryRepository historyRepository;

  @Autowired
  public FeedbackServiceImpl(FeedbackRepository feedbackRepository, HistoryRepository historyRepository) {
    this.feedbackRepository = feedbackRepository;
    this.historyRepository = historyRepository;
  }

  @Transactional
  @Override
  public Feedback saveFeedback(Feedback feedback) {
    try {
      History history = historyRepository.findById(feedback.getHistory().getHistoryId())
        .orElseThrow(() -> new IllegalArgumentException("History not found"));
      history.addFeedback(feedback);
      return feedbackRepository.save(feedback);
    } catch (DataAccessException dae) {
      throw new DrawingNotFoundException(dae.getMessage(), dae);
    }
  }

  @Override
  public List<Feedback> saveFeedbacks(List<Feedback> feedbacks) {
    try {
      Iterable<Feedback> feedbackIterable = feedbackRepository.saveAll(feedbacks);
      return Streamable.of(feedbackIterable).stream().toList();
    } catch (DataAccessException dae) {
      throw new DrawingNotFoundException(dae.getMessage(), dae);
    }
  }

  @Override
  public Feedback findFeedbackById(int id) {
    return feedbackRepository.findById(id).orElse(null);
  }

  @Override
  public List<Feedback> findFeedbacksByHistoryId(int id) {
    Iterable<Feedback> feedbackIterable = feedbackRepository.findFeedbacksByHistoryHistoryId(id);
    return Streamable.of(feedbackIterable).stream().toList();
  }

  @Override
  public List<Feedback> findAllFeedbacks() {
    Iterable<Feedback> feedbackIterable = feedbackRepository.findAll();
    return Streamable.of(feedbackIterable).stream().toList();
  }

  @Override
  public void deleteFeedbackById(int id) {
    feedbackRepository.deleteById(id);
  }
}
