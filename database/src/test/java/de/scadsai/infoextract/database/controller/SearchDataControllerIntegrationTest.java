package de.scadsai.infoextract.database.controller;

import com.fasterxml.jackson.core.json.JsonWriteFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.tomakehurst.wiremock.WireMockServer;
import com.github.tomakehurst.wiremock.core.Options;
import de.scadsai.infoextract.database.exception.SearchDataNotFoundException;
import de.scadsai.infoextract.database.dto.SearchDataDto;
import de.scadsai.infoextract.database.entity.SearchData;
import de.scadsai.infoextract.database.exception.SearchDataNotFoundForDrawingException;
import de.scadsai.infoextract.database.repository.SearchDataRepository;
import de.scadsai.infoextract.database.service.DtoService;
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

import de.scadsai.infoextract.database.entity.Drawing;
import de.scadsai.infoextract.database.repository.DrawingRepository;

class SearchDataControllerIntegrationTest extends SpringIntegrationTest {

  private static final String SAVE_SEARCHDATA = "/searchdata/save";
  private static final String SAVE_SEARCHDATALIST = "/searchdata/save-all";
  private static final String DELETE_SEARCHDATA = "/searchdata/delete/{id}";
  private static final String DELETE_FOR_DRAWING = "/searchdata/delete-for-drawing/{id}";
  private static final String GET_SEARCHDATA = "/searchdata/get/{id}";
  private static final String GET_FOR_DRAWING = "/searchdata/get-for-drawing/{id}";
  private static final String GET_SEARCHDATALIST = "/searchdata/get-all";

  private static final int DRAWING_ID_1 = 1;
  private static final int DRAWING_ID_2 = 2;
  private static final int SEARCHDATA_ID_1 = 1;
  private static final int SEARCHDATA_ID_2 = 2;

  @Autowired
  private MockMvc mockMvc;
  @Autowired
  private SearchDataRepository searchDataRepository;
  @Autowired
  private DrawingRepository drawingRepository;
  @Autowired
  private DtoService dtoService;
  @Autowired
  ResourceLoader resourceLoader;

  private WireMockServer wireMockServer;
  private SearchData searchData1;
  private SearchData searchData2;
  private Drawing drawing1;
  private Drawing drawing2;

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
    drawing1.setRuntimes(Collections.emptyList());
    // Don't reference searchdata here

    drawing2 = new Drawing();
    drawing2.setDrawingId(DRAWING_ID_2);
    drawing2.setOriginalDrawing(imageByteArray);
    drawing2.setRuntimes(Collections.emptyList());
    // Don't reference searchdata here

    // init search data
    ObjectMapper objectMapper = new ObjectMapper();
    //deprecated: objectMapper.configure(JsonGenerator.Feature.ESCAPE_NON_ASCII, true);
    objectMapper.configure(JsonWriteFeature.ESCAPE_NON_ASCII.mappedFeature(), true);

    searchData1 = new SearchData();
    searchData1.setSearchDataId(SEARCHDATA_ID_1);
    searchData1.setDrawing(drawing1);
    searchData1.setShape(new float[]{
      0.36298543f,
      0.21438452f,
      0.36298543f,
      0.00000000f,
      0.00000000f,
      0.00000000f,
      0.00000000f,
      0.00000000f,
      0.36298543f,
      0.21438452f,
      0.00000000f,
      0.00000000f,
      0.27605971f,
      0.36298543f,
      0.00000000f,
      0.55211943f
    });
    String[][] material2d = new String[][]{{"CuZn39Pb3", "2.0401"}, {"Reineisen"}};
    String[] material = new String[material2d.length];
    for (int i = 0; i < material2d.length; i++) {
      material[i] = objectMapper.writeValueAsString(material2d[i]);
    }
    searchData1.setMaterial(material);
    String[][] generalTolerances2d = new String[][]{{"f", "h"}, {"m", "k"}};
    String[] generalTolerances = new String[generalTolerances2d.length];
    for (int i = 0; i < generalTolerances2d.length; i++) {
      generalTolerances[i] = objectMapper.writeValueAsString(generalTolerances2d[i]);
    }
    searchData1.setGeneralTolerances(generalTolerances);
    searchData1.setSurfaces(new String[]{"Ra 0.5", "Ra 1.2"});
    String[] gdts = new String[]{"⌾ 0.02 A", "◯0.1BC"};
    for (int i = 0; i < gdts.length; i++) {
      gdts[i] = objectMapper.writeValueAsString(gdts[i]);
    }
    searchData1.setGdts(gdts);
    searchData1.setThreads(new String[]{"M5x0.8", "NPT 1/2"});
    searchData1.setOuterDimensions(new float[]{10f, 20f, 30f});
    searchData1.setSearchVector(new float[]{
      0.36298543f,
      0.21438452f,
      0.36298543f,
      0.00000000f,
      0.00000000f,
      0.00000000f,
      0.00000000f,
      0.00000000f,
      0.36298543f,
      0.21438452f,
      0.00000000f,
      0.00000000f,
      0.27605971f,
      0.36298543f,
      0.00000000f,
      0.55211943f
    });

    searchData2 = new SearchData();
    searchData2.setSearchDataId(SEARCHDATA_ID_2);
    searchData2.setDrawing(drawing2);
    searchData2.setShape(new float[]{});
    searchData2.setMaterial(new String[]{});
    searchData2.setGeneralTolerances(new String[]{});
    searchData2.setSurfaces(new String[]{});
    searchData2.setGdts(new String[]{});
    searchData2.setThreads(new String[]{});
    searchData2.setOuterDimensions(new float[]{});
    searchData2.setSearchVector(new float[]{});
  }

  @AfterAll
  void cleanUp() {
    wireMockServer.stop();
    drawingRepository.deleteAll();
    assertEquals(0L, drawingRepository.count());
    searchDataRepository.deleteAll();
    assertEquals(0L, searchDataRepository.count());
  }

  @BeforeEach
  void clearRepository() {
    // because of one-to-one relation for searchdata-drawing, we need to empty drawings, too
    drawingRepository.deleteAll();
    searchDataRepository.deleteAll();
    assertEquals(0L, searchDataRepository.count());
  }

  @Test
  void testSaveSearchData() throws Exception {
    // store drawings without referenced searchdata
    drawingRepository.saveAll(List.of(drawing1, drawing2));
    assertEquals(2L, drawingRepository.count());
    assertEquals(0L, searchDataRepository.count());

    SearchDataDto searchDataDto = dtoService.convertEntityToDto(searchData1);
    ObjectMapper objectMapper = new ObjectMapper();
    String input = objectMapper.writeValueAsString(searchDataDto);

    mockMvc.perform(corsPost(SAVE_SEARCHDATA).contentType(MediaType.APPLICATION_JSON).content(input))
      .andExpect(status().isCreated())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(input))
      .andExpect(allowOrigin());

    assertEquals(1L, searchDataRepository.count());
  }

  @Test
  void testSaveSearchDataList() throws Exception {
    // store drawings without referenced searchdata
    drawingRepository.saveAll(List.of(drawing1, drawing2));
    assertEquals(2L, drawingRepository.count());
    assertEquals(0L, searchDataRepository.count());

    SearchDataDto searchData1Dto = dtoService.convertEntityToDto(searchData1);
    SearchDataDto searchData2Dto = dtoService.convertEntityToDto(searchData2);

    ObjectMapper objectMapper = new ObjectMapper();
    String input = objectMapper.writeValueAsString(List.of(searchData1Dto, searchData2Dto));

    mockMvc.perform(corsPost(SAVE_SEARCHDATALIST).contentType(MediaType.APPLICATION_JSON).content(input))
      .andExpect(status().isCreated())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(input))
      .andExpect(allowOrigin());

    assertEquals(2L, searchDataRepository.count());
  }

  @Test
  void testDeleteSearchDataById() throws Exception {
    drawingRepository.saveAll(List.of(drawing1, drawing2));
    searchDataRepository.saveAll(List.of(searchData1, searchData2));
    assertEquals(2L, drawingRepository.count());
    assertEquals(2L, searchDataRepository.count());

    mockMvc.perform(corsDelete(DELETE_SEARCHDATA, SEARCHDATA_ID_1))
      .andExpect(status().isOk())
      .andExpect(allowOrigin());

    assertEquals(1L, searchDataRepository.count());
  }

  @Test
  void testDeleteSearchDataByDrawingId() throws Exception {
    drawingRepository.saveAll(List.of(drawing1, drawing2));
    searchDataRepository.saveAll(List.of(searchData1, searchData2));
    assertEquals(2L, drawingRepository.count());
    assertEquals(2L, searchDataRepository.count());

    mockMvc.perform(corsDelete(DELETE_FOR_DRAWING, DRAWING_ID_1))
      .andExpect(status().isOk())
      .andExpect(allowOrigin());

    assertEquals(1L, searchDataRepository.count());
  }

  @Test
  void testGetSearchDataById() throws Exception {
    drawingRepository.saveAll(List.of(drawing1, drawing2));
    searchDataRepository.saveAll(List.of(searchData1, searchData2));
    assertEquals(2L, drawingRepository.count());
    assertEquals(2L, searchDataRepository.count());

    SearchDataDto searchData1Dto = dtoService.convertEntityToDto(searchData1);
    ObjectMapper objectMapper = new ObjectMapper();
    String expectedResult = objectMapper.writeValueAsString(searchData1Dto);

    mockMvc.perform(corsGet(GET_SEARCHDATA, SEARCHDATA_ID_1))
      .andExpect(status().isOk())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(expectedResult))
      .andExpect(allowOrigin());

    mockMvc.perform(corsGet(GET_SEARCHDATA, 3))
      .andExpect(status().isNotFound())
      .andExpect(content().string(new SearchDataNotFoundException(3).getMessage()))
      .andExpect(allowOrigin());
  }

  @Test
  void testGetSearchDataByDrawingId() throws Exception {
    drawingRepository.saveAll(List.of(drawing1, drawing2));
    searchDataRepository.saveAll(List.of(searchData1, searchData2));
    assertEquals(2L, drawingRepository.count());
    assertEquals(2L, searchDataRepository.count());

    SearchDataDto searchData1Dto = dtoService.convertEntityToDto(searchData1);
    ObjectMapper objectMapper = new ObjectMapper();
    String expectedResult = objectMapper.writeValueAsString(searchData1Dto);

    mockMvc.perform(corsGet(GET_FOR_DRAWING, DRAWING_ID_1))
      .andExpect(status().isOk())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(expectedResult))
      .andExpect(allowOrigin());

    SearchDataDto searchData2Dto = dtoService.convertEntityToDto(searchData2);
    expectedResult = objectMapper.writeValueAsString(searchData2Dto);

    mockMvc.perform(corsGet(GET_FOR_DRAWING, DRAWING_ID_2))
      .andExpect(status().isOk())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(expectedResult))
      .andExpect(allowOrigin());

    mockMvc.perform(corsGet(GET_FOR_DRAWING, 3))
      .andExpect(status().isNotFound())
      .andExpect(content().string(new SearchDataNotFoundForDrawingException(3).getMessage()))
      .andExpect(allowOrigin());
  }

  @Test
  void testGetAllSearchData() throws Exception {
    drawingRepository.saveAll(List.of(drawing1, drawing2));
    searchDataRepository.saveAll(List.of(searchData1, searchData2));
    assertEquals(2L, drawingRepository.count());
    assertEquals(2L, searchDataRepository.count());

    SearchDataDto searchData1Dto = dtoService.convertEntityToDto(searchData1);
    SearchDataDto searchData2Dto = dtoService.convertEntityToDto(searchData2);
    ObjectMapper objectMapper = new ObjectMapper();
    String expected = objectMapper.writeValueAsString(List.of(searchData1Dto, searchData2Dto));

    mockMvc.perform(corsGet(GET_SEARCHDATALIST))
      .andExpect(status().isOk())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(expected))
      .andExpect(allowOrigin());
  }
}
