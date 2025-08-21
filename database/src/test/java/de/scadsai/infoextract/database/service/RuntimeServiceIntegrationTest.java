package de.scadsai.infoextract.database.service;

import de.scadsai.infoextract.database.entity.Runtime;
import de.scadsai.infoextract.database.exception.DrawingNotFoundException;
import de.scadsai.infoextract.database.repository.RuntimeRepository;
import de.scadsai.infoextract.database.entity.Drawing;
import de.scadsai.infoextract.database.repository.DrawingRepository;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.io.IOException;
import java.util.List;
import java.util.Collections;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

@SpringBootTest
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class RuntimeServiceIntegrationTest {

  @Autowired
  private RuntimeService runtimeService;
  @Autowired
  private RuntimeRepository runtimeRepository;
  @Autowired
  private DrawingRepository drawingRepository;

  private static final int runtime1Id = 1;
  private Runtime runtime1;
  private static final int runtime2Id = 2;
  private Runtime runtime2;

  @BeforeAll
  void initObjects() throws IOException {
    Drawing drawing1 = new Drawing();
    drawing1.setDrawingId(1);
    drawing1.setOriginalDrawing(new byte[] {});
    drawing1.setRuntimes(Collections.emptyList());

    Drawing drawing2 = new Drawing();
    drawing2.setDrawingId(2);
    drawing2.setOriginalDrawing(new byte[] {});
    drawing2.setRuntimes(Collections.emptyList());

    drawingRepository.saveAll(List.of(drawing1, drawing2));

    runtime1 = new Runtime();
    runtime1.setRuntimeId(runtime1Id);
    runtime1.setDrawing(drawing1);
    runtime1.setMachine("machine1");
    runtime1.setMachineRuntime(5f);

    runtime2 = new Runtime();
    runtime2.setRuntimeId(runtime2Id);
    runtime2.setDrawing(drawing2);
    runtime2.setMachine("machine2");
    runtime2.setMachineRuntime(10f);
  }

  @BeforeEach
  void initRepository() {
    runtimeRepository.deleteAll();
    assertEquals(0L, runtimeRepository.count());
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
    runtimeService.saveRuntime(runtime1);
    assertEquals(1L, runtimeRepository.count());
  }

  @Test
  void testSaveRuntimes() {
    runtimeService.saveRuntimes(List.of(runtime1, runtime2));
    assertEquals(2L, runtimeRepository.count());
  }

  @Test
  void testSaveRuntimeForUnknownDrawing() {
    Drawing drawing = new Drawing();
    drawing.setDrawingId(10);

    Runtime invalidRuntime = new Runtime();
    invalidRuntime.setRuntimeId(5);
    invalidRuntime.setDrawing(drawing);
    invalidRuntime.setMachine("machine1");
    invalidRuntime.setMachineRuntime(1f);

    assertThrows(DrawingNotFoundException.class, () -> runtimeService.saveRuntime(invalidRuntime));
  }

  @Test
  void testSaveRuntimesForUnknownDrawing() {
    Drawing drawing = new Drawing();
    drawing.setDrawingId(10);

    Runtime invalidRuntime = new Runtime();
    invalidRuntime.setRuntimeId(5);
    invalidRuntime.setDrawing(drawing);
    invalidRuntime.setMachine("machine1");
    invalidRuntime.setMachineRuntime(1f);

    assertThrows(DrawingNotFoundException.class, () -> runtimeService.saveRuntimes(List.of(runtime1, runtime2, invalidRuntime)));
  }

  @Test
  void testFindRuntimeById() {
    runtimeService.saveRuntime(runtime1);
    assertEquals(1L, runtimeRepository.count());

    Runtime runtimeFound = runtimeService.findRuntimeById(runtime1Id);
    assertNotNull(runtimeFound);
    assertEquals(runtime1.getRuntimeId(), runtimeFound.getRuntimeId());
    assertEquals(runtime1.getDrawing().getDrawingId(), runtimeFound.getDrawing().getDrawingId());
    assertEquals(runtime1.getMachine(), runtimeFound.getMachine());
    assertEquals(runtime1.getMachineRuntime(), runtimeFound.getMachineRuntime());
  }

  @Test
  void testFindRuntimeByDrawingId() {
    runtimeService.saveRuntime(runtime2);
    assertEquals(1L, runtimeRepository.count());

    List<Runtime> runtimesFound = runtimeService.findRuntimesByDrawingId(2);
    assertNotNull(runtimesFound);
    assertFalse(runtimesFound.isEmpty());
    Runtime runtimeFound = runtimesFound.getFirst();
    assertEquals(runtime2.getRuntimeId(), runtimeFound.getRuntimeId());
    assertEquals(runtime2.getDrawing().getDrawingId(), runtimeFound.getDrawing().getDrawingId());
    assertEquals(runtime2.getMachine(), runtimeFound.getMachine());
    assertEquals(runtime2.getMachineRuntime(), runtimeFound.getMachineRuntime());
  }

  @Test
  void testFindAllRuntimes() {
    runtimeService.saveRuntimes(List.of(runtime1, runtime2));
    assertEquals(2L, runtimeRepository.count());

    List<Runtime> runtimesFound = runtimeService.findAllRuntimes();
    assertNotNull(runtimesFound);
    assertEquals(2, runtimesFound.size());
  }

  @Test
  void testDeleteRuntimeById() {
    runtimeService.saveRuntimes(List.of(runtime1, runtime2));
    assertEquals(2L, runtimeRepository.count());

    runtimeService.deleteRuntimeById(runtime1Id);
    assertEquals(1L, runtimeRepository.count());
    assertFalse(runtimeRepository.existsById(runtime1Id));
  }

  @Test
  void testDeleteRuntimeByDrawingId() {
    runtimeService.saveRuntimes(List.of(runtime1, runtime2));
    assertEquals(2L, runtimeRepository.count());

    runtimeService.deleteRuntimesByDrawingId(2);
    assertEquals(1L, runtimeRepository.count());
    assertFalse(runtimeRepository.existsById(runtime2Id));
  }
}
