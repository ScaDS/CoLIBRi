package de.scadsai.infoextract.database.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.tomakehurst.wiremock.WireMockServer;
import com.github.tomakehurst.wiremock.core.Options;
import de.scadsai.infoextract.database.dto.FeedbackDto;
import de.scadsai.infoextract.database.entity.Drawing;
import de.scadsai.infoextract.database.entity.Feedback;
import de.scadsai.infoextract.database.entity.History;
import de.scadsai.infoextract.database.exception.FeedbackNotFoundException;
import de.scadsai.infoextract.database.exception.FeedbacksNotFoundForHistoryException;
import de.scadsai.infoextract.database.repository.DrawingRepository;
import de.scadsai.infoextract.database.repository.HistoryRepository;
import de.scadsai.infoextract.database.repository.FeedbackRepository;
import de.scadsai.infoextract.database.service.FeedbackService;
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
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class FeedbackControllerIntegrationTest extends SpringIntegrationTest {

  private static final String SAVE_FEEDBACK = "/feedback/save";
  private static final String SAVE_FEEDBACKS = "/feedback/save-all";
  private static final String DELETE_FEEDBACK = "/feedback/delete/{id}";
  private static final String GET_FEEDBACK = "/feedback/get/{id}";
  private static final String GET_FOR_HISTORY = "/feedback/get-for-history/{id}";
  private static final String GET_FEEDBACKS = "/feedback/get-all";

  private static final int DRAWING_ID_1 = 1;
  private static final int DRAWING_ID_2 = 2;

  @Autowired
  private MockMvc mockMvc;
  @Autowired
  private FeedbackRepository feedbackRepository;
  @Autowired
  private FeedbackService feedbackService;
  @Autowired
  private HistoryRepository historyRepository;
  @Autowired
  private DrawingRepository drawingRepository;
  @Autowired
  private DtoService dtoService;
  @Autowired
  ResourceLoader resourceLoader;

  private WireMockServer wireMockServer;
  private byte[] imageByteArray;
  private static final String IMAGE_PATH = "classpath:data/example_drawing.pdf";

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
    feedbackRepository.deleteAll();
    assertEquals(0L, feedbackRepository.count());
    drawingRepository.deleteAll();
    assertEquals(0L, drawingRepository.count());
  }

  // Build new entities per test to avoid optimistic locking exceptions when reusing entities over test cases
  private Drawing newDrawing(int id) {
    Drawing d = new Drawing();
    d.setDrawingId(id);
    d.setOriginalDrawing(imageByteArray);
    return d;
  }

  private History newHistory() {
    History h = new History();
    h.setQueryDrawing(imageByteArray);
    h.setQueryPath(IMAGE_PATH);
    h.setTimestamp(LocalDateTime.now());
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
  @Transactional
  void testSaveFeedbackUpdatesHistory() throws Exception {
    History history = newHistory();
    history = historyRepository.save(history);
    assertTrue(history.getFeedbacks().isEmpty());

    Feedback feedback = newFeedback("", 1, null, history);
    feedback = feedbackService.saveFeedback(feedback);

    History updatedHistory = historyRepository.findById(history.getHistoryId()).orElseThrow();
    assertTrue(updatedHistory.getFeedbacks().contains(feedback));

    assertEquals(1, historyRepository.count());
    assertEquals(1, feedbackRepository.count());
  }

  @Test
  void testSaveFeedback() throws Exception {
    Drawing drawing1 = newDrawing(DRAWING_ID_1);
    Drawing drawing2 = newDrawing(DRAWING_ID_2);
    drawingRepository.saveAll(List.of(drawing1, drawing2));

    History history1 = newHistory();
    history1 = historyRepository.save(history1);

    FeedbackDto inputDto = new FeedbackDto(
      history1.getHistoryId(),
      drawing1.getDrawingId(),
      "feedback",
      1
    );

    ObjectMapper objectMapper = new ObjectMapper();
    String input = objectMapper.writeValueAsString(inputDto);

    mockMvc.perform(corsPost(SAVE_FEEDBACK).contentType(MediaType.APPLICATION_JSON).content(input))
      .andExpect(status().isCreated())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(jsonPath("$.feedback_id").isNumber())
      .andExpect(allowOrigin());

    assertEquals(1L, feedbackRepository.count());
  }

  @Test
  void testSaveFeedbacks() throws Exception {
    Drawing drawing1 = newDrawing(DRAWING_ID_1);
    Drawing drawing2 = newDrawing(DRAWING_ID_2);
    drawingRepository.saveAll(List.of(drawing1, drawing2));

    History history1 = newHistory();
    history1 = historyRepository.save(history1);

    Feedback feedback1 = newFeedback("feedback1", 1, drawing1, history1);
    Feedback feedback2 = newFeedback("feedback2", 2, drawing1, history1);

    FeedbackDto feedback1Dto = dtoService.convertEntityToDto(feedback1);
    FeedbackDto feedback2Dto = dtoService.convertEntityToDto(feedback2);
    ObjectMapper objectMapper = new ObjectMapper();
    String input = objectMapper.writeValueAsString(List.of(feedback1Dto, feedback2Dto));

    mockMvc.perform(corsPost(SAVE_FEEDBACKS).contentType(MediaType.APPLICATION_JSON).content(input))
      .andExpect(status().isCreated())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(jsonPath("$[0].feedback_id").isNumber()) // Assert that the feedbackId is generated
      .andExpect(jsonPath("$[1].feedback_id").isNumber()) // Assert that the feedbackId is generated
      .andExpect(allowOrigin());

    assertEquals(2L, feedbackRepository.count());
  }

  @Test
  void testDeleteFeedbackById() throws Exception {
    Drawing drawing1 = newDrawing(DRAWING_ID_1);
    Drawing drawing2 = newDrawing(DRAWING_ID_2);
    drawingRepository.saveAll(List.of(drawing1, drawing2));

    History history1 = newHistory();
    history1 = historyRepository.save(history1);

    Feedback feedback1 = newFeedback("feedback1", 1, drawing1, history1);
    Feedback feedback2 = newFeedback("feedback2", 2, drawing1, history1);
    Feedback feedback3 = newFeedback("feedback3", 1, drawing2, history1);

    feedbackRepository.saveAll(List.of(feedback1, feedback2, feedback3));

    mockMvc.perform(corsDelete(DELETE_FEEDBACK, feedback3.getFeedbackId()))
      .andExpect(status().isOk())
      .andExpect(allowOrigin());

    assertEquals(2L, feedbackRepository.count());
  }

  @Test
  void testGetFeedbackById() throws Exception {
    Drawing drawing1 = newDrawing(DRAWING_ID_1);
    Drawing drawing2 = newDrawing(DRAWING_ID_2);
    drawingRepository.saveAll(List.of(drawing1, drawing2));

    History history1 = newHistory();
    history1 = historyRepository.save(history1);

    Feedback feedback1 = feedbackRepository.save(newFeedback("feedback1", 1, drawing1, history1));
    feedbackRepository.save(newFeedback("feedback2", 2, drawing1, history1));

    FeedbackDto feedback1Dto = dtoService.convertEntityToDto(feedback1);
    ObjectMapper objectMapper = new ObjectMapper();
    String expectedResult = objectMapper.writeValueAsString(feedback1Dto);

    mockMvc.perform(corsGet(GET_FEEDBACK, feedback1.getFeedbackId()))
      .andExpect(status().isOk())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(expectedResult))
      .andExpect(allowOrigin());

    mockMvc.perform(corsGet(GET_FEEDBACK, 5))
      .andExpect(status().isNotFound())
      .andExpect(content().string(new FeedbackNotFoundException(5).getMessage()))
      .andExpect(allowOrigin());
  }

  @Test
  void testGetFeedbacksByHistoryId() throws Exception {
    Drawing drawing1 = newDrawing(DRAWING_ID_1);
    drawingRepository.save(drawing1);

    History history1 = historyRepository.save(newHistory());
    History history2 = historyRepository.save(newHistory());
    History history3 = historyRepository.save(newHistory());

    Feedback feedback1 = feedbackRepository.save(newFeedback("feedback1", 1, drawing1, history1));
    Feedback feedback2 = feedbackRepository.save(newFeedback("feedback2", 2, drawing1, history1));
    Feedback feedback3 = feedbackRepository.save(newFeedback("feedback3", 1, drawing1, history2));

    feedbackRepository.saveAll(List.of(feedback1, feedback2, feedback3));

    FeedbackDto feedback1Dto = dtoService.convertEntityToDto(feedback1);
    FeedbackDto feedback2Dto = dtoService.convertEntityToDto(feedback2);
    ObjectMapper objectMapper = new ObjectMapper();
    String expectedResult = objectMapper.writeValueAsString(List.of(feedback1Dto, feedback2Dto));

    mockMvc.perform(corsGet(GET_FOR_HISTORY, history1.getHistoryId()))
      .andExpect(status().isOk())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(expectedResult))
      .andExpect(allowOrigin());

    mockMvc.perform(corsGet(GET_FOR_HISTORY, history3.getHistoryId()))
      .andExpect(status().isNotFound())
      .andExpect(content().string(new FeedbacksNotFoundForHistoryException(history3.getHistoryId()).getMessage()))
      .andExpect(allowOrigin());
  }

  @Test
  void testGetAllFeedbacks() throws Exception {
    Drawing drawing1 = newDrawing(DRAWING_ID_1);
    drawingRepository.save(drawing1);

    History history1 = newHistory();
    history1 = historyRepository.save(history1);

    Feedback feedback1 = feedbackRepository.save(newFeedback("feedback1", 1, drawing1, history1));
    Feedback feedback2 = feedbackRepository.save(newFeedback("feedback2", 2, drawing1, history1));
    Feedback feedback3 = feedbackRepository.save(newFeedback("feedback3", 1, drawing1, history1));

    feedbackRepository.saveAll(List.of(feedback1, feedback2, feedback3));

    FeedbackDto feedback1Dto = dtoService.convertEntityToDto(feedback1);
    FeedbackDto feedback2Dto = dtoService.convertEntityToDto(feedback2);
    FeedbackDto feedback3Dto = dtoService.convertEntityToDto(feedback3);
    ObjectMapper objectMapper = new ObjectMapper();
    String expectedResult = objectMapper.writeValueAsString(List.of(feedback1Dto, feedback2Dto, feedback3Dto));

    mockMvc.perform(corsGet(GET_FEEDBACKS))
      .andExpect(status().isOk())
      .andExpect(content().contentType(MediaType.APPLICATION_JSON))
      .andExpect(content().string(expectedResult))
      .andExpect(allowOrigin());
  }
}
