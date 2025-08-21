package de.scadsai.infoextract.database.service;

import de.scadsai.infoextract.database.entity.History;
import de.scadsai.infoextract.database.entity.Drawing;
import de.scadsai.infoextract.database.entity.Feedback;
import de.scadsai.infoextract.database.exception.DrawingNotFoundException;
import de.scadsai.infoextract.database.repository.HistoryRepository;
import de.scadsai.infoextract.database.repository.DrawingRepository;
import de.scadsai.infoextract.database.repository.FeedbackRepository;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.io.IOException;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

@SpringBootTest
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class FeedbackServiceIntegrationTest {

  @Autowired
  private FeedbackService feedbackService;
  @Autowired
  private FeedbackRepository feedbackRepository;
  @Autowired
  private DrawingRepository drawingRepository;
  @Autowired
  private HistoryRepository historyRepository;

  private Drawing drawing1;

  @BeforeAll
  void initObjects() throws IOException {
    drawing1 = new Drawing();
    drawing1.setDrawingId(1);
    drawing1.setOriginalDrawing(new byte[] {});
    drawing1.setFeedbacks(Collections.emptyList());

    Drawing drawing2 = new Drawing();
    drawing2.setDrawingId(2);
    drawing2.setOriginalDrawing(new byte[] {});
    drawing2.setFeedbacks(Collections.emptyList());

    drawingRepository.saveAll(List.of(drawing1, drawing2));
  }

  @BeforeEach
  void initRepository() {
    feedbackRepository.deleteAll();
    assertEquals(0L, feedbackRepository.count());
  }

  @AfterAll
  void cleanUp() {
    historyRepository.deleteAll();
    assertEquals(0L, historyRepository.count());
    feedbackRepository.deleteAll();
    assertEquals(0L, feedbackRepository.count());
    drawingRepository.deleteAll();
    assertEquals(0L, drawingRepository.count());
  }

  // Build new entities per test to avoid optimistic locking exceptions when reusing entities over test cases
  private History newHistory() {
    History h = new History();
    h.setQueryDrawing(new byte[] {});
    return h;
  }

  private Feedback newFeedback(String desc, int value, Drawing d, History h) {
    Feedback f = new Feedback();
    f.setFeedbackDesc(desc);
    f.setFeedbackValue(value);
    f.setDrawing(d);
    f.setHistory(h);
    return f;
  }

  @Test
  void testSaveFeedback() {
    History history1 = historyRepository.save(newHistory());
    feedbackService.saveFeedback(newFeedback("feedback", 1, drawing1, history1));

    assertEquals(1L, feedbackRepository.count());
  }

  @Test
  void testSaveFeedbacks() {
    History history1 = historyRepository.save(newHistory());
    History history2 = historyRepository.save(newHistory());
    feedbackService.saveFeedback(newFeedback("feedback1", 1, drawing1, history1));
    feedbackService.saveFeedback(newFeedback("feedback2", 1, drawing1, history2));

    assertEquals(2L, feedbackRepository.count());
  }

  @Test
  void testSaveFeedbackForUnknownDrawing() {
    Drawing drawing = new Drawing();
    drawing.setDrawingId(10);

    Feedback invalidFeedback = newFeedback("", 1, drawing, newHistory());
    invalidFeedback.setFeedbackId(5);

    assertThrows(DrawingNotFoundException.class, () -> feedbackService.saveFeedback(invalidFeedback));
  }

  @Test
  void testSaveFeedbacksForUnknownDrawing() {
    Drawing drawing = new Drawing();
    drawing.setDrawingId(10);

    History history1 = historyRepository.save(newHistory());
    History history2 = historyRepository.save(newHistory());
    Feedback feedback1 = feedbackService.saveFeedback(newFeedback("feedback1", 1, drawing1, history1));
    Feedback feedback2 = feedbackService.saveFeedback(newFeedback("feedback2", 1, drawing1, history2));

    Feedback invalidFeedback = newFeedback("", 1, drawing, null);
    invalidFeedback.setFeedbackId(5);

    assertThrows(DrawingNotFoundException.class, () -> feedbackService.saveFeedbacks(List.of(feedback1, feedback2, invalidFeedback)));
  }

  @Test
  void testFindFeedbackById() {
    History history = historyRepository.save(new History());

    Feedback feedback = feedbackService.saveFeedback(newFeedback("feedback", 1, drawing1, history));
    assertEquals(1L, feedbackRepository.count());

    Feedback feedbackFound = feedbackService.findFeedbackById(feedback.getFeedbackId());
    assertNotNull(feedbackFound);
    assertEquals(feedback.getFeedbackId(), feedbackFound.getFeedbackId());
    assertEquals(feedback.getHistory().getHistoryId(), feedbackFound.getHistory().getHistoryId());
    assertEquals(feedback.getDrawing().getDrawingId(), feedbackFound.getDrawing().getDrawingId());
    assertEquals(feedback.getFeedbackDesc(), feedbackFound.getFeedbackDesc());
    assertEquals(feedback.getFeedbackValue(), feedbackFound.getFeedbackValue());
  }

  @Test
  void testFindFeedbackByHistoryId() {
    History history = historyRepository.save(new History());

    Feedback feedback = feedbackService.saveFeedback(newFeedback("feedback", 1, drawing1, history));
    assertEquals(1L, feedbackRepository.count());

    List<Feedback> feedbacksFound = feedbackService.findFeedbacksByHistoryId(feedback.getHistory().getHistoryId());
    assertNotNull(feedbacksFound);
    assertFalse(feedbacksFound.isEmpty());
    Feedback feedbackFound = feedbacksFound.getFirst();
    assertEquals(feedback.getFeedbackId(), feedbackFound.getFeedbackId());
    assertEquals(feedback.getHistory().getHistoryId(), feedbackFound.getHistory().getHistoryId());
    assertEquals(feedback.getDrawing().getDrawingId(), feedbackFound.getDrawing().getDrawingId());
    assertEquals(feedback.getFeedbackDesc(), feedbackFound.getFeedbackDesc());
    assertEquals(feedback.getFeedbackValue(), feedbackFound.getFeedbackValue());
  }

  @Test
  void testFindAllFeedbacks() {
    History history1 = historyRepository.save(newHistory());
    History history2 = historyRepository.save(newHistory());
    Feedback feedback1 = feedbackService.saveFeedback(newFeedback("feedback1", 1, drawing1, history1));
    Feedback feedback2 = feedbackService.saveFeedback(newFeedback("feedback2", 1, drawing1, history2));
    assertEquals(2L, feedbackRepository.count());

    List<Feedback> feedbacksFound = feedbackService.findAllFeedbacks();
    assertNotNull(feedbacksFound);
    assertEquals(2, feedbacksFound.size());
  }

  @Test
  void testDeleteFeedbackById() {
    History history1 = historyRepository.save(newHistory());
    History history2 = historyRepository.save(newHistory());
    Feedback feedback1 = feedbackService.saveFeedback(newFeedback("feedback1", 1, drawing1, history1));
    Feedback feedback2 = feedbackService.saveFeedback(newFeedback("feedback2", 1, drawing1, history2));
    feedbackService.saveFeedbacks(List.of(feedback1, feedback2));
    assertEquals(2L, feedbackRepository.count());

    feedbackService.deleteFeedbackById(feedback1.getFeedbackId());
    assertEquals(1L, feedbackRepository.count());
    assertFalse(feedbackRepository.existsById(feedback1.getFeedbackId()));
  }
}
