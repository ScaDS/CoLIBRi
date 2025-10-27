package de.scadsai.colibri.database.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.tomakehurst.wiremock.WireMockServer;
import com.github.tomakehurst.wiremock.core.Options;
import de.scadsai.colibri.database.exception.RuntimeNotFoundException;
import de.scadsai.colibri.database.dto.RuntimeDto;
import de.scadsai.colibri.database.entity.Runtime;
import de.scadsai.colibri.database.exception.RuntimesNotFoundForDrawingException;
import de.scadsai.colibri.database.repository.RuntimeRepository;
import de.scadsai.colibri.database.service.DtoService;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.io.IOException;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import de.scadsai.colibri.database.entity.Drawing;
import de.scadsai.colibri.database.repository.DrawingRepository;

class RuntimeControllerIntegrationTest extends SpringIntegrationTest {

  private static final String SAVE_RUNTIME = "/runtime/save";
  private static final String SAVE_RUNTIMES = "/runtime/save-all";
  private static final String DELETE_RUNTIME = "/runtime/delete/{id}";
  private static final String DELETE_FOR_DRAWING = "/runtime/delete-for-drawing/{id}";
  private static final String GET_RUNTIME = "/runtime/get/{id}";
  private static final String GET_FOR_DRAWING = "/runtime/get-for-drawing/{id}";
  private static final String GET_RUNTIMES = "/runtime/get-all";

  private static final int DRAWING_ID_1 = 1;
  private static final int DRAWING_ID_2 = 2;
  private static final int RUNTIME_ID_1 = 1;
  private static final int RUNTIME_ID_2 = 2;
  private static final int RUNTIME_ID_3 = 3;
  private static final int RUNTIME_ID_4 = 4;
  private static final String MACHINE_ID_1 = "machine1";
  private static final String MACHINE_ID_2 = "machine2";
  private static final float MACHINE_RUNTIME_1 = 1f;
  private static final float MACHINE_RUNTIME_2 = 2f;

  @Autowired
  private MockMvc mockMvc;
  @Autowired
  private RuntimeRepository runtimeRepository;
  @Autowired
  private DrawingRepository drawingRepository;
  @Autowired
  private DtoService dtoService;
  @Autowired
  ResourceLoader resourceLoader;

  private WireMockServer wireMockServer;
  private Drawing drawing1;
  private Drawing drawing2;
  private Runtime runtime1;
  private Runtime runtime2;
  private Runtime runtime3;
  private Runtime runtime4;

  @BeforeAll
  void startServerAndInitObjects() throws IOException {
    wireMockServer = new WireMockServer(Options.DYNAMIC_PORT);
    wireMockServer.start();
    assertTrue(wireMockServer.isRunning());

    Resource imageFileResource = resourceLoader.getResource("classpath:data/example_drawing.pdf");
    assertNotNull(imageFileResource);
    assertTrue(imageFileResource.getFile().exists());
    byte[] imageByteArray = imageFileResource.getInputStream().readAllBytes();
    assertTrue(imageByteArray.length > 0);

    drawing1 = new Drawing();
    drawing1.setDrawingId(DRAWING_ID_1);
    drawing1.setOriginalDrawing(imageByteArray);

    runtime1 = new Runtime();
    runtime1.setRuntimeId(RUNTIME_ID_1);
    runtime1.setDrawing(drawing1);
    runtime1.setMachine(MACHINE_ID_1);
    runtime1.setMachineRuntime(MACHINE_RUNTIME_1);

    runtime2 = new Runtime();
    runtime2.setRuntimeId(RUNTIME_ID_2);
    runtime2.setDrawing(drawing1);
    runtime2.setMachine(MACHINE_ID_2);
    runtime2.setMachineRuntime(MACHINE_RUNTIME_2);

    drawing1.setRuntimes(List.of(runtime1, runtime2));

    drawing2 = new Drawing();
    drawing2.setDrawingId(DRAWING_ID_2);
    drawing2.setOriginalDrawing(imageByteArray);
    drawing2.setRuntimes(Collections.emptyList());

    runtime3 = new Runtime();
    runtime3.setRuntimeId(RUNTIME_ID_3);
    runtime3.setDrawing(drawing2);
    runtime3.setMachine(MACHINE_ID_1);
    runtime3.setMachineRuntime(MACHINE_RUNTIME_1);

    runtime4 = new Runtime();
    runtime4.setRuntimeId(RUNTIME_ID_4);
    runtime4.setDrawing(drawing2);
    runtime4.setMachine(MACHINE_ID_2);
    runtime4.setMachineRuntime(MACHINE_RUNTIME_2);
  }

  @AfterAll
  void cleanUp() {
    wireMockServer.stop();
    drawingRepository.deleteAll();
    assertEquals(0L, drawingRepository.count());
    runtimeRepository.deleteAll();
    assertEquals(0L, runtimeRepository.count());
  }

  @BeforeEach
  void clearRepository() {
    runtimeRepository.deleteAll();
    assertEquals(0L, runtimeRepository.count());
    drawingRepository.deleteAll();
    assertEquals(0L, drawingRepository.count());
  }

  @Test
  void testSaveRuntime() throws Exception {
    drawingRepository.saveAll(List.of(drawing1, drawing2));
    assertEquals(2L, drawingRepository.count());
    assertEquals(2L, runtimeRepository.count());

    RuntimeDto runtimeDto = dtoService.convertEntityToDto(runtime3);
    ObjectMapper objectMapper = new ObjectMapper();
    String input = objectMapper.writeValueAsString(runtimeDto);

    mockMvc.perform(corsPost(SAVE_RUNTIME).contentType(MediaType.APPLICATION_JSON).content(input))
      .andExpect(status().isCreated())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(input))
      .andExpect(allowOrigin());

    assertEquals(3L, runtimeRepository.count());
  }

  @Test
  void testSaveRuntimes() throws Exception {
    drawingRepository.saveAll(List.of(drawing1, drawing2));
    assertEquals(2L, drawingRepository.count());
    assertEquals(2L, runtimeRepository.count());

    RuntimeDto runtime3Dto = dtoService.convertEntityToDto(runtime3);
    RuntimeDto runtime4Dto = dtoService.convertEntityToDto(runtime4);
    ObjectMapper objectMapper = new ObjectMapper();
    String input = objectMapper.writeValueAsString(List.of(runtime3Dto, runtime4Dto));

    mockMvc.perform(corsPost(SAVE_RUNTIMES).contentType(MediaType.APPLICATION_JSON).content(input))
      .andExpect(status().isCreated())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(input))
      .andExpect(allowOrigin());

    assertEquals(4L, runtimeRepository.count());
  }

  @Test
  void testDeleteRuntimeById() throws Exception {
    drawingRepository.saveAll(List.of(drawing1, drawing2));
    runtimeRepository.saveAll(List.of(runtime3, runtime4));
    assertEquals(2L, drawingRepository.count());
    assertEquals(4L, runtimeRepository.count());

    mockMvc.perform(corsDelete(DELETE_RUNTIME, RUNTIME_ID_1))
      .andExpect(status().isOk())
      .andExpect(allowOrigin());

    assertEquals(3L, runtimeRepository.count());
  }

  @Test
  void testDeleteRuntimesByDrawingId() throws Exception {
    drawingRepository.saveAll(List.of(drawing1, drawing2));
    runtimeRepository.saveAll(List.of(runtime3, runtime4));
    assertEquals(2L, drawingRepository.count());
    assertEquals(4L, runtimeRepository.count());

    mockMvc.perform(corsDelete(DELETE_FOR_DRAWING, DRAWING_ID_1))
      .andExpect(status().isOk())
      .andExpect(allowOrigin());

    assertEquals(2L, runtimeRepository.count());
  }

  @Test
  void testGetRuntimeById() throws Exception {
    drawingRepository.saveAll(List.of(drawing1, drawing2));
    runtimeRepository.saveAll(List.of(runtime3, runtime4));
    assertEquals(2L, drawingRepository.count());
    assertEquals(4L, runtimeRepository.count());

    RuntimeDto runtime1Dto = dtoService.convertEntityToDto(runtime1);
    ObjectMapper objectMapper = new ObjectMapper();
    String expectedResult = objectMapper.writeValueAsString(runtime1Dto);

    mockMvc.perform(corsGet(GET_RUNTIME, RUNTIME_ID_1))
      .andExpect(status().isOk())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(expectedResult))
      .andExpect(allowOrigin());

    mockMvc.perform(corsGet(GET_RUNTIME, 5))
      .andExpect(status().isNotFound())
      .andExpect(content().string(new RuntimeNotFoundException(5).getMessage()))
      .andExpect(allowOrigin());
  }

  @Test
  void testGetRuntimesByDrawingId() throws Exception {
    drawingRepository.saveAll(List.of(drawing1, drawing2));
    runtimeRepository.saveAll(List.of(runtime3, runtime4));
    assertEquals(2L, drawingRepository.count());
    assertEquals(4L, runtimeRepository.count());

    RuntimeDto runtime1Dto = dtoService.convertEntityToDto(runtime1);
    RuntimeDto runtime2Dto = dtoService.convertEntityToDto(runtime2);
    ObjectMapper objectMapper = new ObjectMapper();
    String expectedResult = objectMapper.writeValueAsString(List.of(runtime1Dto, runtime2Dto));

    mockMvc.perform(corsGet(GET_FOR_DRAWING, DRAWING_ID_1))
      .andExpect(status().isOk())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(expectedResult))
      .andExpect(allowOrigin());

    RuntimeDto runtime3Dto = dtoService.convertEntityToDto(runtime3);
    RuntimeDto runtime4Dto = dtoService.convertEntityToDto(runtime4);
    expectedResult = objectMapper.writeValueAsString(List.of(runtime3Dto, runtime4Dto));

    mockMvc.perform(corsGet(GET_FOR_DRAWING, DRAWING_ID_2))
      .andExpect(status().isOk())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(expectedResult))
      .andExpect(allowOrigin());

    mockMvc.perform(corsGet(GET_FOR_DRAWING, 3))
      .andExpect(status().isNotFound())
      .andExpect(content().string(new RuntimesNotFoundForDrawingException(3).getMessage()))
      .andExpect(allowOrigin());
  }

  @Test
  void testGetAllRuntimes() throws Exception {
    drawingRepository.saveAll(List.of(drawing1, drawing2));
    runtimeRepository.saveAll(List.of(runtime3, runtime4));
    assertEquals(2L, drawingRepository.count());
    assertEquals(4L, runtimeRepository.count());

    RuntimeDto runtime1Dto = dtoService.convertEntityToDto(runtime1);
    RuntimeDto runtime2Dto = dtoService.convertEntityToDto(runtime2);
    RuntimeDto runtime3Dto = dtoService.convertEntityToDto(runtime3);
    RuntimeDto runtime4Dto = dtoService.convertEntityToDto(runtime4);
    ObjectMapper objectMapper = new ObjectMapper();
    String expected = objectMapper.writeValueAsString(List.of(runtime1Dto, runtime2Dto, runtime3Dto, runtime4Dto));

    mockMvc.perform(corsGet(GET_RUNTIMES))
      .andExpect(status().isOk())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(expected))
      .andExpect(allowOrigin());
  }
}
