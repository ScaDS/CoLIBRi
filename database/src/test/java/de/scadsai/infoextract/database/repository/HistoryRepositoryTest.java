package de.scadsai.infoextract.database.repository;

import de.scadsai.infoextract.database.entity.History;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.samePropertyValuesAs;
import static org.junit.jupiter.api.Assertions.*;

@DataJpaTest
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class HistoryRepositoryTest {

  @Autowired
  private TestEntityManager testEntityManager;
  @Autowired
  private HistoryRepository historyRepository;
  @Autowired
  ResourceLoader resourceLoader;

  private History history1;
  private History history2;
  private History history3;
  private History history4;

  private History createHistory() throws IOException {
    String imagePath = "classpath:data/example_drawing.pdf";
    Resource imageFileResource = resourceLoader.getResource(imagePath);
    byte[] imageByteArray = imageFileResource.getInputStream().readAllBytes();

    History history = new History();
    history.setQueryDrawing(imageByteArray);
    history.setQueryPath(imagePath);
    history.setTimestamp(LocalDateTime.now());
    return history;
  }

  @BeforeAll
  void initObjects() throws IOException {
    String imagePath = "classpath:data/example_drawing.pdf";
    Resource imageFileResource = resourceLoader.getResource(imagePath);
    assertNotNull(imageFileResource);
    assertTrue(imageFileResource.getFile().exists());
    byte[] imageByteArray = imageFileResource.getInputStream().readAllBytes();
    assertTrue(imageByteArray.length > 0);
  }

  @BeforeEach
  void populateRepository() throws IOException {
    historyRepository.deleteAll();
    assertEquals(0L, historyRepository.count());
    history1 = createHistory();
    history2 = createHistory();
    testEntityManager.persist(history1);
    testEntityManager.persist(history2);
    assertEquals(2L, historyRepository.count());
  }

  @AfterAll
  void cleanUp() {
    historyRepository.deleteAll();
    assertEquals(0L, historyRepository.count());
  }

  @Test
  void testSaveHistory() throws IOException {
    history3 = createHistory();
    History historySaved = historyRepository.save(history3);
    assertNotNull(historySaved);
    assertEquals(3L, historyRepository.count());
    assertTrue(historyRepository.existsById(historySaved.getHistoryId()));
  }

  @Test
  void testSaveHistories() throws IOException {
    history3 = createHistory();
    history4 = createHistory();
    Iterable<History> historiesSaved = historyRepository.saveAll(List.of(history3, history4));
    assertNotNull(historiesSaved);
    assertEquals(4L, historyRepository.count());
    assertTrue(historyRepository.existsById(history3.getHistoryId()));
    assertTrue(historyRepository.existsById(history4.getHistoryId()));
  }

  @Test
  void testFindHistoryById() {
    Optional<History> result = historyRepository.findById(history1.getHistoryId());
    assertTrue(result.isPresent());
    assertThat(history1, samePropertyValuesAs(result.get()));
  }

  @Test
  void testFindAllHistories() {
    Iterable<History> result = historyRepository.findAll();
    assertIterableEquals(result, List.of(history1, history2));
  }

  @Test
  void testDeleteHistoryById() {
    historyRepository.deleteById(history1.getHistoryId());
    assertEquals(1L, historyRepository.count());
    assertFalse(historyRepository.existsById(history1.getHistoryId()));
  }
}
