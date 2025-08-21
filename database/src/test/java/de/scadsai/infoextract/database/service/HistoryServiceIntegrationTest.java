package de.scadsai.infoextract.database.service;

import de.scadsai.infoextract.database.entity.Drawing;
import de.scadsai.infoextract.database.entity.History;
import de.scadsai.infoextract.database.entity.Feedback;
import de.scadsai.infoextract.database.repository.HistoryRepository;
import de.scadsai.infoextract.database.repository.FeedbackRepository;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class HistoryServiceIntegrationTest {

  @Autowired
  private HistoryService historyService;
  @Autowired
  private HistoryRepository historyRepository;
  @Autowired
  private FeedbackService feedbackService;
  @Autowired
  private FeedbackRepository feedbackRepository;
  @Autowired
  ResourceLoader resourceLoader;

  @BeforeAll
  void initObjects() throws IOException {
    String imagePath = "classpath:data/example_drawing.pdf";
    Resource imageFileResource = resourceLoader.getResource(imagePath);
    assertNotNull(imageFileResource);
    assertTrue(imageFileResource.getFile().exists());
    byte[] imageByteArray = imageFileResource.getInputStream().readAllBytes();
    assertTrue(imageByteArray.length > 0);
    /*
    history1 = new History();
    history1.setQueryDrawing(imageByteArray);
    history2 = new History();
    history2.setQueryDrawing(imageByteArray);

    feedback1 = new Feedback();
    feedback1.setHistory(history1);
    feedback2 = new Feedback();
    feedback2.setHistory(history2);

    history1.setFeedbacks(List.of(feedback1));
    history2.setFeedbacks(List.of(feedback2));
    */
  }

  @BeforeEach
  void initRepository() {
    historyRepository.deleteAll();
    assertEquals(0L, historyRepository.count());
  }

  @AfterAll
  void cleanUp() {
    historyRepository.deleteAll();
    assertEquals(0L, historyRepository.count());
    feedbackRepository.deleteAll();
    assertEquals(0L, feedbackRepository.count());
  }

  // Build new entities per test to avoid optimistic locking exceptions when reusing entities over test cases
  private History newHistory() {
    History h = new History();
    h.setQueryDrawing(new byte[] {});
    return h;
  }

  private Feedback newFeedback(History h) {
    Feedback f = new Feedback();
    f.setHistory(h);
    return f;
  }

  @Test
  void testSaveHistory() {
    historyService.saveHistory(newHistory());
    assertEquals(1L, historyRepository.count());
  }

  @Test
  void testSaveHistories() {
    historyService.saveHistories(List.of(newHistory(), newHistory()));
    assertEquals(2L, historyRepository.count());
  }

  @Test
  void testFindHistoryById() {
    History history = historyService.saveHistory(newHistory());
    assertEquals(1L, historyRepository.count());

    History historyFound = historyService.findHistoryById(history.getHistoryId());
    assertNotNull(historyFound);
    assertEquals(history.getHistoryId(), historyFound.getHistoryId());
    assertArrayEquals(history.getQueryDrawing(), historyFound.getQueryDrawing());
  }

  @Test
  void testFindAllHistories() {
    historyService.saveHistories(List.of(newHistory(), newHistory()));
    assertEquals(2L, historyRepository.count());

    List<History> historiesFound = historyService.findAllHistories();
    assertNotNull(historiesFound);
    assertEquals(2, historiesFound.size());
  }

  @Test
  void testDeleteHistoryById() {
    History history1 = historyService.saveHistory(newHistory());
    History history2 = historyService.saveHistory(newHistory());
    assertEquals(2L, historyRepository.count());

    historyService.deleteHistoryById(history1.getHistoryId());
    assertEquals(1L, historyRepository.count());
    assertFalse(historyRepository.existsById(history1.getHistoryId()));
  }

  @Test
  void testDeleteHistoryCascade() {
    History history1 = newHistory();
    History history2 = newHistory();
    Feedback feedback1 = newFeedback(history1);
    Feedback feedback2 = newFeedback(history2);
    history1.setFeedbacks(List.of(feedback1));
    history2.setFeedbacks(List.of(feedback2));
    historyRepository.saveAll(List.of(history1, history2));

    assertEquals(2, historyRepository.count());
    assertEquals(2, feedbackRepository.count());

    historyRepository.delete(history1);
    assertEquals(1, historyRepository.count());
    assertEquals(1, feedbackRepository.count());
  }

  @Transactional
  @Test
  void testUpdateHistoryCascade() {
    History history = newHistory();
    Feedback feedback1 = newFeedback(history);
    history.addFeedback(feedback1);
    history = historyRepository.save(history);
    assertEquals(1, historyRepository.count());
    assertEquals(1, feedbackRepository.count());

    Feedback feedback2 = newFeedback(history);
    feedback2 = feedbackService.saveFeedback(feedback2);

    assertEquals(1, historyRepository.count());
    assertEquals(2, feedbackRepository.count());

    History updatedHistory = historyRepository.findById(history.getHistoryId()).orElseThrow();
    assertTrue(updatedHistory.getFeedbacks().contains(feedback2));
  }
}
