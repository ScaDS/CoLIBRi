package de.scadsai.colibri.database.repository;

import de.scadsai.colibri.database.entity.Drawing;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;

import java.io.IOException;
import java.util.Collections;
import java.util.List;
import java.util.Optional;

import static org.hamcrest.Matchers.samePropertyValuesAs;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertIterableEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@DataJpaTest
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class DrawingRepositoryTest {

  @Autowired
  private TestEntityManager testEntityManager;
  @Autowired
  private DrawingRepository drawingRepository;
  @Autowired
  ResourceLoader resourceLoader;

  private static final int drawing1Id = 1;
  private Drawing drawing1;
  private static final int drawing2Id = 2;
  private Drawing drawing2;
  private static final int drawing3Id = 3;
  private Drawing drawing3;
  private static final int drawing4Id = 4;
  private Drawing drawing4;

  @BeforeAll
  void initObjects() throws IOException {
    Resource imageFileResource = resourceLoader.getResource("classpath:data/example_drawing.pdf");
    assertNotNull(imageFileResource);
    assertTrue(imageFileResource.getFile().exists());
    byte[] imageByteArray = imageFileResource.getInputStream().readAllBytes();
    assertTrue(imageByteArray.length > 0);

    drawing1 = new Drawing();
    drawing1.setDrawingId(drawing1Id);
    drawing1.setOriginalDrawing(imageByteArray);
    drawing1.setRuntimes(Collections.emptyList());

    drawing2 = new Drawing();
    drawing2.setDrawingId(drawing2Id);
    drawing2.setOriginalDrawing(imageByteArray);
    drawing2.setRuntimes(Collections.emptyList());

    drawing3 = new Drawing();
    drawing3.setDrawingId(drawing3Id);
    drawing3.setOriginalDrawing(imageByteArray);
    drawing3.setRuntimes(Collections.emptyList());

    drawing4 = new Drawing();
    drawing4.setDrawingId(drawing4Id);
    drawing4.setOriginalDrawing(imageByteArray);
    drawing4.setRuntimes(Collections.emptyList());
  }

  @BeforeEach
  void populateRepository() {
    drawingRepository.deleteAll();
    assertEquals(0L, drawingRepository.count());

    testEntityManager.persist(drawing1);
    testEntityManager.persist(drawing2);
    assertEquals(2L, drawingRepository.count());
  }

  @AfterAll
  void cleanUp() {
    drawingRepository.deleteAll();
    assertEquals(0L, drawingRepository.count());
  }

  @Test
  void testSaveDrawing() {
    Drawing drawingSaved = drawingRepository.save(drawing3);
    assertNotNull(drawingSaved);
    assertEquals(3L, drawingRepository.count());
    assertTrue(drawingRepository.existsById(drawing3Id));
  }

  @Test
  void testSaveDrawings() {
    Iterable<Drawing> drawingsSaved = drawingRepository.saveAll(List.of(drawing3, drawing4));
    assertNotNull(drawingsSaved);
    assertEquals(4L, drawingRepository.count());
    assertTrue(drawingRepository.existsById(drawing3Id));
    assertTrue(drawingRepository.existsById(drawing4Id));
  }

  @Test
  void testFindDrawingById() {
    Optional<Drawing> result = drawingRepository.findById(drawing1Id);
    assertTrue(result.isPresent());
    assertThat(drawing1, samePropertyValuesAs(result.get()));
  }

  @Test
  void testFindAllDrawings() {
    Iterable<Drawing> result = drawingRepository.findAll();
    assertIterableEquals(result, List.of(drawing1, drawing2));
  }

  @Test
  void testDeleteDrawingById() {
    drawingRepository.deleteById(drawing1Id);
    assertEquals(1L, drawingRepository.count());
    assertFalse(drawingRepository.existsById(drawing1Id));
  }
}
