package de.scadsai.infoextract.database.repository;

import de.scadsai.infoextract.database.entity.Drawing;
import de.scadsai.infoextract.database.entity.Runtime;
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

import static org.hamcrest.Matchers.samePropertyValuesAs;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertIterableEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@DataJpaTest
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class RuntimeRepositoryTest {

  @Autowired
  private TestEntityManager testEntityManager;
  @Autowired
  private RuntimeRepository runtimeRepository;
  @Autowired
  private DrawingRepository drawingRepository;

  private static final int runtime1Id = 1;
  private Runtime runtime1;
  private static final int runtime2Id = 2;
  private Runtime runtime2;
  private static final int runtime3Id = 3;
  private Runtime runtime3;
  private static final int runtime4Id = 4;
  private Runtime runtime4;
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

    runtime1 = new Runtime();
    runtime1.setRuntimeId(runtime1Id);
    runtime1.setDrawing(drawing1);
    runtime1.setMachine("machine1");
    runtime1.setMachineRuntime(1f);

    runtime2 = new Runtime();
    runtime2.setRuntimeId(runtime2Id);
    runtime2.setDrawing(drawing1);
    runtime2.setMachine("machine2");
    runtime2.setMachineRuntime(2f);

    runtime3 = new Runtime();
    runtime3.setRuntimeId(runtime3Id);
    runtime3.setDrawing(drawing2);
    runtime3.setMachine("machine3");
    runtime3.setMachineRuntime(3f);

    runtime4 = new Runtime();
    runtime4.setRuntimeId(runtime4Id);
    runtime4.setDrawing(drawing3);
    runtime4.setMachine("machine4");
    runtime4.setMachineRuntime(4f);
  }

  @BeforeEach
  void populateRepository() {
    runtimeRepository.deleteAll();
    assertEquals(0L, runtimeRepository.count());

    testEntityManager.persist(runtime1);
    testEntityManager.persist(runtime2);
    assertEquals(2L, runtimeRepository.count());
  }

  @AfterAll
  void cleanUp() {
    drawingRepository.deleteAll();
    assertEquals(0L, drawingRepository.count());
    runtimeRepository.deleteAll();
    assertEquals(0L, runtimeRepository.count());
  }

  @Test
  void testSaveRuntime() {
    Runtime runtimeSaved = runtimeRepository.save(runtime3);
    assertNotNull(runtimeSaved);
    assertEquals(3L, runtimeRepository.count());
    assertTrue(runtimeRepository.existsById(runtime3Id));
  }

  @Test
  void testSaveRuntimes() {
    Iterable<Runtime> runtimesSaved = runtimeRepository.saveAll(List.of(runtime3, runtime4));
    assertNotNull(runtimesSaved);
    assertEquals(4L, runtimeRepository.count());
    assertTrue(runtimeRepository.existsById(runtime3Id));
    assertTrue(runtimeRepository.existsById(runtime4Id));
  }

  @Test
  void testFindRuntimeById() {
    Optional<Runtime> result = runtimeRepository.findById(runtime1Id);
    assertTrue(result.isPresent());
    assertThat(runtime1, samePropertyValuesAs(result.get()));
  }

  @Test
  void testFindRuntimesByDrawingId() {
    Iterable<Runtime> result = runtimeRepository.findRuntimesByDrawing_DrawingId(drawing1Id);
    assertIterableEquals(result, List.of(runtime1, runtime2));
  }

  @Test
  void testFindAllRuntimes() {
    Iterable<Runtime> result = runtimeRepository.findAll();
    assertIterableEquals(result, List.of(runtime1, runtime2));
  }

  @Test
  void testDeleteRuntimeById() {
    runtimeRepository.deleteById(runtime1Id);
    assertEquals(1L, runtimeRepository.count());
    assertFalse(runtimeRepository.existsById(runtime1Id));
  }

  @Test
  void testDeleteRuntimeByDrawingId() {
    runtimeRepository.saveAll(List.of(runtime3, runtime4));
    assertEquals(4L, runtimeRepository.count());

    runtimeRepository.deleteRuntimesByDrawing_DrawingId(drawing1Id);
    assertEquals(2L, runtimeRepository.count());
    assertFalse(runtimeRepository.existsById(runtime1Id));
    assertFalse(runtimeRepository.existsById(runtime2Id));

    runtimeRepository.deleteRuntimesByDrawing_DrawingId(drawing3Id);
    assertEquals(1L, runtimeRepository.count());
    assertFalse(runtimeRepository.existsById(runtime4Id));
  }
}
