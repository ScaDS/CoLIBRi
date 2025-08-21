package de.scadsai.infoextract.database.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.github.tomakehurst.wiremock.WireMockServer;
import com.github.tomakehurst.wiremock.core.Options;
import de.scadsai.infoextract.database.dto.HistoryDto;
import de.scadsai.infoextract.database.entity.Drawing;
import de.scadsai.infoextract.database.entity.Feedback;
import de.scadsai.infoextract.database.entity.History;
import de.scadsai.infoextract.database.entity.SearchData;
import de.scadsai.infoextract.database.exception.HistoryNotFoundException;
import de.scadsai.infoextract.database.repository.HistoryRepository;
import de.scadsai.infoextract.database.repository.DrawingRepository;
import de.scadsai.infoextract.database.repository.FeedbackRepository;
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
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class HistoryControllerIntegrationTest extends SpringIntegrationTest {

  private static final String SAVE_HISTORY = "/history/save";
  private static final String SAVE_HISTORIES = "/history/save-all";
  private static final String DELETE_HISTORY = "/history/delete/{id}";
  private static final String GET_HISTORY = "/history/get/{id}";
  private static final String GET_HISTORIES = "/history/get-all";
  private static final int DRAWING_ID_1 = 1;

  @Autowired
  private MockMvc mockMvc;
  @Autowired
  private HistoryRepository historyRepository;
  @Autowired
  private DrawingRepository drawingRepository;
  @Autowired
  private FeedbackRepository feedbackRepository;
  @Autowired
  private DtoService dtoService;
  @Autowired
  ResourceLoader resourceLoader;

  private WireMockServer wireMockServer;
  private byte[] imageByteArray;
  private static final String IMAGE_PATH = "classpath:data/example_drawing.pdf";
  private Drawing drawing1;

  @BeforeAll
  void startServerAndInitObjects() throws IOException {
    wireMockServer = new WireMockServer(Options.DYNAMIC_PORT);
    wireMockServer.start();
    assertTrue(wireMockServer.isRunning());

    Resource imageFileResource = resourceLoader.getResource(IMAGE_PATH);
    assertNotNull(imageFileResource);
    assertTrue(imageFileResource.getFile().exists());
    imageByteArray = imageFileResource.getInputStream().readAllBytes();
    assertTrue(imageByteArray.length > 0);

    drawing1 = new Drawing();
    drawing1.setDrawingId(DRAWING_ID_1);
    drawing1.setOriginalDrawing(imageByteArray);

    SearchData searchData1 = new SearchData();
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

    drawing1.setRuntimes(Collections.emptyList());
    drawing1.setSearchData(searchData1);
  }

  @AfterAll
  void cleanUp() {
    wireMockServer.stop();
    historyRepository.deleteAll();
    assertEquals(0L, historyRepository.count());
    drawingRepository.deleteAll();
    assertEquals(0L, drawingRepository.count());
    feedbackRepository.deleteAll();
    assertEquals(0L, feedbackRepository.count());
  }

  @BeforeEach
  void clearRepository() {
    historyRepository.deleteAll();
    assertEquals(0L, historyRepository.count());
    drawingRepository.deleteAll();
    assertEquals(0L, drawingRepository.count());
    feedbackRepository.deleteAll();
    assertEquals(0L, feedbackRepository.count());
  }

  // Build new entities per test to avoid optimistic locking exceptions when reusing entities over test cases
  private History newHistory() {
    History h = new History();
    h.setQueryDrawing(imageByteArray);
    h.setQueryPath(IMAGE_PATH);
    h.setTimestamp(LocalDateTime.now().truncatedTo(ChronoUnit.MICROS));
    h.setFeedbacks(Collections.emptyList());
    return h;
  }

  private Feedback newFeedback(String desc, int value, Drawing d, History h) {
    Feedback f = new Feedback();
    f.setFeedbackDesc(desc);
    f.setFeedbackValue(value);
    f.setDrawing(d);
    f.setHistory(h);
    return f;
  }

  @Test
  void testSaveHistory() throws Exception {
    HistoryDto historyDto = dtoService.convertEntityToDto(newHistory());
    ObjectMapper objectMapper = new ObjectMapper();
    objectMapper.registerModule(new JavaTimeModule()); // Enables LocalDateTime serialization
    objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS); // Optional: formats as ISO-8601
    String input = objectMapper.writeValueAsString(historyDto);

    mockMvc.perform(corsPost(SAVE_HISTORY).contentType(MediaType.APPLICATION_JSON).content(input))
      .andExpect(status().isCreated())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(jsonPath("$.history_id").isNumber()) // Assert that the HistoryId is generated
      .andExpect(allowOrigin());

    assertEquals(1L, historyRepository.count());
    assertEquals(0L, feedbackRepository.count());
  }

  @Test
  void testSaveHistories() throws Exception {
    HistoryDto history1Dto = dtoService.convertEntityToDto(newHistory());
    HistoryDto history2Dto = dtoService.convertEntityToDto(newHistory());
    ObjectMapper objectMapper = new ObjectMapper();
    objectMapper.registerModule(new JavaTimeModule()); // Enables LocalDateTime serialization
    objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS); // Optional: formats as ISO-8601
    String input = objectMapper.writeValueAsString(List.of(history1Dto, history2Dto));

    mockMvc.perform(corsPost(SAVE_HISTORIES).contentType(MediaType.APPLICATION_JSON).content(input))
      .andExpect(status().isCreated())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(jsonPath("$[0].history_id").isNumber()) // Assert that the HistoryId is generated
      .andExpect(jsonPath("$[1].history_id").isNumber()) // Assert that the HistoryId is generated
      .andExpect(allowOrigin());

    assertEquals(2L, historyRepository.count());
    assertEquals(0L, feedbackRepository.count());
  }

  @Test
  void testDeleteHistoryById() throws Exception {
    History history1 = historyRepository.save(newHistory());
    History history2 = historyRepository.save(newHistory());
    historyRepository.save(newHistory());
    assertEquals(3L, historyRepository.count());

    drawingRepository.save(drawing1);
    assertEquals(1L, drawingRepository.count());

    Feedback feedback = newFeedback("feedback", 0, drawing1, history1);
    feedbackRepository.save(feedback);
    assertEquals(1L, feedbackRepository.count());

    mockMvc.perform(corsDelete(DELETE_HISTORY, history1.getHistoryId()))
      .andExpect(status().isOk())
      .andExpect(allowOrigin());

    assertEquals(2L, historyRepository.count());
    assertEquals(0L, feedbackRepository.count());

    mockMvc.perform(corsDelete(DELETE_HISTORY, history2.getHistoryId()))
      .andExpect(status().isOk())
      .andExpect(allowOrigin());

    assertEquals(1L, historyRepository.count());
    assertEquals(0L, feedbackRepository.count());
  }

  @Test
  void testGetHistoryById() throws Exception {
    History history1 = historyRepository.save(newHistory());
    History history2 = historyRepository.save(newHistory());
    History history3 = historyRepository.save(newHistory());
    assertEquals(3L, historyRepository.count());

    drawingRepository.save(drawing1);
    assertEquals(1L, drawingRepository.count());

    Feedback feedback1 = newFeedback("feedback1", 0, drawing1, history1);
    Feedback feedback2 = newFeedback("feedback2", 1, drawing1, history1);
    Feedback feedback3 = newFeedback("feedback3", 2, drawing1, history2);

    feedbackRepository.saveAll(List.of(feedback1, feedback2));
    assertEquals(2L, feedbackRepository.count());

    history1.setFeedbacks(List.of(feedback1, feedback2));
    historyRepository.save(history1);

    HistoryDto history1Dto = dtoService.convertEntityToDto(history1);
    ObjectMapper objectMapper = new ObjectMapper();
    objectMapper.registerModule(new JavaTimeModule()); // Enables LocalDateTime serialization
    objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS); // Optional: formats as ISO-8601
    String expectedResult = objectMapper.writeValueAsString(history1Dto);

    mockMvc.perform(corsGet(GET_HISTORY, history1.getHistoryId()))
      .andExpect(status().isOk())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(expectedResult))
      .andExpect(allowOrigin());

    mockMvc.perform(corsGet(GET_HISTORY, 10))
      .andExpect(status().isNotFound())
      .andExpect(content().string(new HistoryNotFoundException(10).getMessage()))
      .andExpect(allowOrigin());
  }

  @Test
  void testGetAllHistories() throws Exception {
    History history1 = historyRepository.save(newHistory());
    History history2 = historyRepository.save(newHistory());
    History history3 = historyRepository.save(newHistory());
    assertEquals(3L, historyRepository.count());

    drawingRepository.save(drawing1);
    assertEquals(1L, drawingRepository.count());

    Feedback feedback1 = newFeedback("feedback1", 0, drawing1, history1);
    Feedback feedback2 = newFeedback("feedback2", 1, drawing1, history1);
    Feedback feedback3 = newFeedback("feedback3", 2, drawing1, history2);

    feedback1 = feedbackRepository.save(feedback1);
    feedback2 = feedbackRepository.save(feedback2);
    feedback3 = feedbackRepository.save(feedback3);
    assertEquals(3L, feedbackRepository.count());

    history1.setFeedbacks(List.of(feedback1, feedback2));
    history2.setFeedbacks(List.of(feedback3));

    history1 = historyRepository.save(history1);
    history2 = historyRepository.save(history2);
    assertEquals(3L, historyRepository.count());

    HistoryDto history1Dto = dtoService.convertEntityToDto(history1);
    HistoryDto history2Dto = dtoService.convertEntityToDto(history2);
    HistoryDto history3Dto = dtoService.convertEntityToDto(history3);
    ObjectMapper objectMapper = new ObjectMapper();
    objectMapper.registerModule(new JavaTimeModule()); // Enables LocalDateTime serialization
    objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS); // Optional: formats as ISO-8601
    String expected = objectMapper.writeValueAsString(List.of(history1Dto, history2Dto, history3Dto));

    mockMvc.perform(corsGet(GET_HISTORIES))
      .andExpect(status().isOk())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(expected))
      .andExpect(allowOrigin());
  }
}
