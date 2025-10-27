package de.scadsai.colibri.database.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.tomakehurst.wiremock.WireMockServer;
import com.github.tomakehurst.wiremock.core.Options;
import de.scadsai.colibri.database.entity.Runtime;
import de.scadsai.colibri.database.exception.DrawingNotFoundException;
import de.scadsai.colibri.database.dto.DrawingDto;
import de.scadsai.colibri.database.entity.Drawing;
import de.scadsai.colibri.database.entity.SearchData;
import de.scadsai.colibri.database.repository.DrawingRepository;
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
import java.util.List;
import java.util.Collections;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class DrawingControllerIntegrationTest extends SpringIntegrationTest {

  private static final String SAVE_DRAWING = "/drawing/save";
  private static final String SAVE_DRAWINGS = "/drawing/save-all";
  private static final String DELETE_DRAWING = "/drawing/delete/{id}";
  private static final String GET_DRAWING = "/drawing/get/{id}";
  private static final String GET_DRAWINGS = "/drawing/get-all";
  private static final int DRAWING_ID_1 = 1;
  private static final int DRAWING_ID_2 = 2;
  private static final int DRAWING_ID_3 = 3;
  private static final int RUNTIME_ID_1 = 1;
  private static final int RUNTIME_ID_2 = 2;
  private static final int RUNTIME_ID_3 = 3;
  private static final String MACHINE_ID_1 = "machine1";
  private static final String MACHINE_ID_2 = "machine2";
  private static final float MACHINE_RUNTIME_1 = 1f;
  private static final float MACHINE_RUNTIME_2 = 2f;

  @Autowired
  private MockMvc mockMvc;
  @Autowired
  private DrawingRepository drawingRepository;
  @Autowired
  private RuntimeRepository runtimeRepository;
  @Autowired
  private DtoService dtoService;
  @Autowired
  ResourceLoader resourceLoader;

  private WireMockServer wireMockServer;
  private Drawing drawing1;
  private Drawing drawing2;
  private Drawing drawing3;
  private Runtime runtime1;
  private Runtime runtime2;
  private Runtime runtime3;
  private SearchData searchData1;
  private SearchData searchData2;

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

    searchData1 = new SearchData();
    searchData1.setSearchDataId(1);
    searchData1.setDrawing(drawing1);
    searchData1.setShape(new float[]{});
    searchData1.setMaterial(new String[]{});
    searchData1.setGeneralTolerances(new String[]{});
    searchData1.setSurfaces(new String[]{});
    searchData1.setGdts(new String[]{});
    searchData1.setThreads(new String[]{});
    searchData1.setOuterDimensions(new float[]{});
    searchData1.setSearchVector(new float[]{});

    drawing1.setRuntimes(List.of(runtime1, runtime2));
    drawing1.setSearchData(searchData1);

    drawing2 = new Drawing();
    drawing2.setDrawingId(DRAWING_ID_2);
    drawing2.setOriginalDrawing(imageByteArray);

    runtime3 = new Runtime();
    runtime3.setRuntimeId(RUNTIME_ID_3);
    runtime3.setDrawing(drawing2);
    runtime3.setMachine(MACHINE_ID_1);
    runtime3.setMachineRuntime(MACHINE_RUNTIME_1);

    searchData2 = new SearchData();
    searchData2.setSearchDataId(2);
    searchData2.setDrawing(drawing2);
    searchData2.setShape(new float[]{});
    searchData2.setMaterial(new String[]{});
    searchData2.setGeneralTolerances(new String[]{});
    searchData2.setSurfaces(new String[]{});
    searchData2.setGdts(new String[]{});
    searchData2.setThreads(new String[]{});
    searchData2.setOuterDimensions(new float[]{});
    searchData2.setSearchVector(new float[]{});

    drawing2.setRuntimes(List.of(runtime3));
    drawing2.setSearchData(searchData2);

    drawing3 = new Drawing();
    drawing3.setDrawingId(DRAWING_ID_3);
    drawing3.setOriginalDrawing(imageByteArray);
    drawing3.setRuntimes(Collections.emptyList());

    drawing1.setFeedbacks(Collections.emptyList());
    drawing2.setFeedbacks(Collections.emptyList());
    drawing3.setFeedbacks(Collections.emptyList());
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
    drawingRepository.deleteAll();
    assertEquals(0L, drawingRepository.count());
    runtimeRepository.deleteAll();
    assertEquals(0L, runtimeRepository.count());
  }

  @Test
  void testSaveDrawing() throws Exception {
    DrawingDto drawingDto = dtoService.convertEntityToDto(drawing1);
    ObjectMapper objectMapper = new ObjectMapper();
    String input = objectMapper.writeValueAsString(drawingDto);

    mockMvc.perform(corsPost(SAVE_DRAWING).contentType(MediaType.APPLICATION_JSON).content(input))
      .andExpect(status().isCreated())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(input))
      .andExpect(allowOrigin());

    assertEquals(1L, drawingRepository.count());
    assertEquals(2L, runtimeRepository.count());
  }

  @Test
  void testSaveDrawings() throws Exception {
    DrawingDto drawing1Dto = dtoService.convertEntityToDto(drawing1);
    DrawingDto drawing2Dto = dtoService.convertEntityToDto(drawing2);
    ObjectMapper objectMapper = new ObjectMapper();
    String input = objectMapper.writeValueAsString(List.of(drawing1Dto, drawing2Dto));

    mockMvc.perform(corsPost(SAVE_DRAWINGS).contentType(MediaType.APPLICATION_JSON).content(input))
      .andExpect(status().isCreated())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(input))
      .andExpect(allowOrigin());

    assertEquals(2L, drawingRepository.count());
    assertEquals(3L, runtimeRepository.count());
  }

  @Test
  void testDeleteDrawingById() throws Exception {
    drawingRepository.saveAll(List.of(drawing1, drawing2, drawing3));
    assertEquals(3L, drawingRepository.count());
    assertEquals(3L, runtimeRepository.count());

    mockMvc.perform(corsDelete(DELETE_DRAWING, DRAWING_ID_1))
      .andExpect(status().isOk())
      .andExpect(allowOrigin());

    assertEquals(2L, drawingRepository.count());
    assertEquals(1L, runtimeRepository.count());

    mockMvc.perform(corsDelete(DELETE_DRAWING, DRAWING_ID_3))
      .andExpect(status().isOk())
      .andExpect(allowOrigin());

    assertEquals(1L, drawingRepository.count());
    assertEquals(1L, runtimeRepository.count());
  }

  @Test
  void testGetDrawingById() throws Exception {
    drawingRepository.saveAll(List.of(drawing1, drawing2, drawing3));
    assertEquals(3L, drawingRepository.count());
    assertEquals(3L, runtimeRepository.count());

    DrawingDto drawing1Dto = dtoService.convertEntityToDto(drawing1);
    ObjectMapper objectMapper = new ObjectMapper();
    String expectedResult = objectMapper.writeValueAsString(drawing1Dto);

    mockMvc.perform(corsGet(GET_DRAWING, DRAWING_ID_1))
      .andExpect(status().isOk())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(expectedResult))
      .andExpect(allowOrigin());

    mockMvc.perform(corsGet(GET_DRAWING, 4))
      .andExpect(status().isNotFound())
      .andExpect(content().string(new DrawingNotFoundException(4).getMessage()))
      .andExpect(allowOrigin());
  }

  @Test
  void testGetAllDrawings() throws Exception {
    drawingRepository.saveAll(List.of(drawing1, drawing2, drawing3));
    assertEquals(3L, drawingRepository.count());
    assertEquals(3L, runtimeRepository.count());

    DrawingDto drawing1Dto = dtoService.convertEntityToDto(drawing1);
    DrawingDto drawing2Dto = dtoService.convertEntityToDto(drawing2);
    DrawingDto drawing3Dto = dtoService.convertEntityToDto(drawing3);
    ObjectMapper objectMapper = new ObjectMapper();
    String expected = objectMapper.writeValueAsString(List.of(drawing1Dto, drawing2Dto, drawing3Dto));

    mockMvc.perform(corsGet(GET_DRAWINGS))
      .andExpect(status().isOk())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(expected))
      .andExpect(allowOrigin());
  }
}
