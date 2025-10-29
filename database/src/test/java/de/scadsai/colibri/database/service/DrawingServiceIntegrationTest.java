package de.scadsai.colibri.database.service;

import de.scadsai.colibri.database.entity.Drawing;
import de.scadsai.colibri.database.repository.DrawingRepository;
import de.scadsai.colibri.database.entity.SearchData;
import de.scadsai.colibri.database.repository.SearchDataRepository;
import de.scadsai.colibri.database.entity.Runtime;
import de.scadsai.colibri.database.repository.RuntimeRepository;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;

import java.io.IOException;
import java.util.List;
import java.util.Collections;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class DrawingServiceIntegrationTest {

  @Autowired
  private DrawingService drawingService;
  @Autowired
  private DrawingRepository drawingRepository;
  @Autowired
  private RuntimeRepository runtimeRepository;
  @Autowired
  private SearchDataRepository searchDataRepository;
  @Autowired
  ResourceLoader resourceLoader;

  private static final int drawing1Id = 1;
  private Drawing drawing1;
  private static final int drawing2Id = 2;
  private Drawing drawing2;
  private Runtime runtime1;
  private Runtime runtime2;
  private SearchData searchData1;
  private SearchData searchData2;

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

    drawing2 = new Drawing();
    drawing2.setDrawingId(drawing2Id);
    drawing2.setOriginalDrawing(imageByteArray);

    runtime1 = new Runtime();
    runtime1.setRuntimeId(1);
    runtime1.setMachine("machine1");
    runtime1.setMachineRuntime(1f);
    runtime1.setDrawing(drawing1);

    runtime2 = new Runtime();
    runtime2.setRuntimeId(2);
    runtime2.setMachine("machine2");
    runtime2.setMachineRuntime(2f);
    runtime2.setDrawing(drawing2);

    searchData1 = new SearchData();
    searchData1.setSearchDataId(1);
    searchData1.setDrawing(drawing1);

    searchData2 = new SearchData();
    searchData2.setSearchDataId(2);
    searchData2.setDrawing(drawing2);

    drawing1.setSearchData(searchData1);
    drawing2.setSearchData(searchData2);
    drawing1.setRuntimes(List.of(runtime1));
    drawing2.setRuntimes(List.of(runtime2));
    drawing1.setFeedbacks(Collections.emptyList());
    drawing2.setFeedbacks(Collections.emptyList());
  }

  @BeforeEach
  void initRepository() {
    drawingRepository.deleteAll();
    assertEquals(0L, drawingRepository.count());
  }

  @AfterAll
  void cleanUp() {
    drawingRepository.deleteAll();
    assertEquals(0L, drawingRepository.count());
    runtimeRepository.deleteAll();
    assertEquals(0L, runtimeRepository.count());
    searchDataRepository.deleteAll();
    assertEquals(0L, searchDataRepository.count());
  }

  @Test
  void testSaveDrawing() {
    drawingService.saveDrawing(drawing1);
    assertEquals(1L, drawingRepository.count());
  }

  @Test
  void testSaveDrawings() {
    drawingService.saveDrawings(List.of(drawing1, drawing2));
    assertEquals(2L, drawingRepository.count());
  }

  @Test
  void testFindDrawingById() {
    drawingService.saveDrawing(drawing1);
    assertEquals(1L, drawingRepository.count());

    Drawing drawingFound = drawingService.findDrawingById(drawing1Id);
    assertNotNull(drawingFound);
    assertEquals(drawing1.getDrawingId(), drawingFound.getDrawingId());
    assertArrayEquals(drawing1.getOriginalDrawing(), drawingFound.getOriginalDrawing());
  }

  @Test
  void testFindAllDrawings() {
    drawingService.saveDrawings(List.of(drawing1, drawing2));
    assertEquals(2L, drawingRepository.count());

    List<Drawing> drawingsFound = drawingService.findAllDrawings();
    assertNotNull(drawingsFound);
    assertEquals(2, drawingsFound.size());
  }

  @Test
  void testDeleteDrawingById() {
    drawingService.saveDrawings(List.of(drawing1, drawing2));
    assertEquals(2L, drawingRepository.count());

    drawingService.deleteDrawingById(drawing1Id);
    assertEquals(1L, drawingRepository.count());
    assertFalse(drawingRepository.existsById(drawing1Id));
  }

  @Test
  void testDeleteDrawingCascade() {
    drawingRepository.saveAll(List.of(drawing1, drawing2));
    assertEquals(2, drawingRepository.count());
    assertEquals(2, runtimeRepository.count());
    assertEquals(2, searchDataRepository.count());

    drawingRepository.delete(drawing1);
    assertEquals(1, drawingRepository.count());
    assertEquals(1, runtimeRepository.count());
    assertEquals(1, searchDataRepository.count());
  }

  @Test
  void testUpdateDrawingCascade() {
    drawingRepository.save(drawing1);
    assertEquals(1, drawingRepository.count());
    assertEquals(1, searchDataRepository.count());
    assertEquals(1, runtimeRepository.count());

    drawingRepository.save(drawing1);

    assertEquals(1, drawingRepository.count());
    assertEquals(1, runtimeRepository.count());
    assertEquals(1, searchDataRepository.count());
  }
}
