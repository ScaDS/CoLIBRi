package de.scadsai.colibri.database.repository;

import de.scadsai.colibri.database.entity.Drawing;
import de.scadsai.colibri.database.entity.History;
import de.scadsai.colibri.database.entity.Feedback;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;

import java.io.IOException;
import java.util.List;
import java.util.Optional;
import java.util.stream.StreamSupport;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@DataJpaTest
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class FeedbackRepositoryTest {

  @Autowired
  private TestEntityManager testEntityManager;
  @Autowired
  private FeedbackRepository feedbackRepository;
  @Autowired
  private DrawingRepository drawingRepository;
  @Autowired
  private HistoryRepository historyRepository;

  private Feedback feedback1;
  private Feedback feedback2;
  private Feedback feedback3;
  private Feedback feedback4;
  private static final int drawing1Id = 1;
  private static final int drawing2Id = 2;
  private static final int drawing3Id = 3;

  @BeforeAll
  void initObjects() throws IOException {
    Drawing drawing1 = new Drawing();
    drawing1.setDrawingId(drawing1Id);

    Drawing drawing2 = new Drawing();
    drawing2.setDrawingId(drawing2Id);

    Drawing drawing3 = new Drawing();
    drawing3.setDrawingId(drawing3Id);

    drawingRepository.saveAll(List.of(drawing1, drawing2, drawing3));
    assertEquals(3L, drawingRepository.count());

    History history1 = new History();
    History history2 = new History();
    History history3 = new History();

    historyRepository.saveAll(List.of(history1, history2, history3));
    assertEquals(3L, drawingRepository.count());

    // Fetch the managed entities from the database
    history1 = historyRepository.findById(history1.getHistoryId()).orElseThrow();
    history2 = historyRepository.findById(history2.getHistoryId()).orElseThrow();
    history3 = historyRepository.findById(history3.getHistoryId()).orElseThrow();

    feedback1 = new Feedback();
    feedback1.setHistory(history1);
    feedback1.setDrawing(drawing1);
    feedback1.setFeedbackDesc("feedback1");
    feedback1.setFeedbackValue(0);

    feedback2 = new Feedback();
    feedback2.setHistory(history1);
    feedback2.setDrawing(drawing1);
    feedback2.setFeedbackDesc("feedback2");
    feedback2.setFeedbackValue(1);

    feedback3 = new Feedback();
    feedback3.setHistory(history2);
    feedback3.setDrawing(drawing2);
    feedback3.setFeedbackDesc("feedback3");
    feedback3.setFeedbackValue(1);

    feedback4 = new Feedback();
    feedback4.setHistory(history3);
    feedback4.setDrawing(drawing3);
    feedback4.setFeedbackDesc("feedback4");
    feedback4.setFeedbackValue(2);
  }

  @BeforeEach
  void populateRepository() {
    feedbackRepository.deleteAll();
    assertEquals(0L, feedbackRepository.count());

    // we reuse entities between tests, ensure new rows
    feedback1.setFeedbackId(null);
    feedback2.setFeedbackId(null);
    feedback3.setFeedbackId(null);
    feedback4.setFeedbackId(null);

    // Persist feedbacks to the repository
    feedback1 = testEntityManager.persistAndFlush(feedback1);
    feedback2 = testEntityManager.persistAndFlush(feedback2);

    // Simulate “committed” DB state with detached managed entities / empty cache
    testEntityManager.clear();
    assertEquals(2L, feedbackRepository.count());
  }

  @AfterAll
  void cleanUp() {
    historyRepository.deleteAll();
    assertEquals(0L, historyRepository.count());
    drawingRepository.deleteAll();
    assertEquals(0L, drawingRepository.count());
    feedbackRepository.deleteAll();
    assertEquals(0L, feedbackRepository.count());
  }

  @Test
  void testSaveFeedback() {
    Feedback feedbackSaved = feedbackRepository.save(feedback3);
    assertNotNull(feedbackSaved);
    assertEquals(3L, feedbackRepository.count());
    assertTrue(feedbackRepository.existsById(feedbackSaved.getFeedbackId()));
  }

  @Test
  void testSaveFeedbacks() {
    Iterable<Feedback> feedbacksSaved = feedbackRepository.saveAll(List.of(feedback3, feedback4));
    assertNotNull(feedbacksSaved);
    assertEquals(4L, feedbackRepository.count());
    assertTrue(feedbackRepository.existsById(feedback3.getFeedbackId()));
    assertTrue(feedbackRepository.existsById(feedback4.getFeedbackId()));
  }

  @Test
  void testFindFeedbackById() {
    Optional<Feedback> result = feedbackRepository.findById(feedback1.getFeedbackId());
    assertTrue(result.isPresent());
    assertEquals(feedback1.getFeedbackId(), result.get().getFeedbackId());
    assertEquals(feedback1.getFeedbackValue(), result.get().getFeedbackValue());
    assertEquals(feedback1.getFeedbackDesc(), result.get().getFeedbackDesc());
    assertEquals(feedback1.getDrawing().getDrawingId(), result.get().getDrawing().getDrawingId());
  }

  @Test
  void testFindAllFeedbacks() {
    Iterable<Feedback> result = feedbackRepository.findAll();
    assertNotNull(result);
    List<Feedback> resultList = StreamSupport.stream(result.spliterator(), false).toList();
    assertEquals(2L, resultList.size());
    List<Integer> resultIds = resultList.stream().map(Feedback::getFeedbackId).toList();
    assertTrue(resultIds.contains(feedback1.getFeedbackId()));
    assertTrue(resultIds.contains(feedback2.getFeedbackId()));
  }

  @Test
  void testDeleteFeedbackById() {
    feedbackRepository.deleteById(feedback1.getFeedbackId());
    assertEquals(1L, feedbackRepository.count());
    assertFalse(feedbackRepository.existsById(feedback1.getFeedbackId()));
  }
}
