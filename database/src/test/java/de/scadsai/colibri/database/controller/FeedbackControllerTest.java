package de.scadsai.colibri.database.controller;

import de.scadsai.colibri.database.dto.FeedbackDto;
import de.scadsai.colibri.database.entity.Feedback;
import de.scadsai.colibri.database.exception.FeedbackNotFoundException;
import de.scadsai.colibri.database.service.FeedbackService;
import de.scadsai.colibri.database.service.DtoService;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.AdditionalMatchers.not;
import static org.mockito.ArgumentMatchers.eq;

@SpringBootTest
class FeedbackControllerTest {

  @Mock
  FeedbackService feedbackService;
  @Mock
  DtoService dtoService;
  @Mock
  Feedback feedback;
  @Mock
  Feedback feedbackSaved;
  @Mock
  FeedbackDto feedbackDto;
  @InjectMocks
  FeedbackController feedbackController;

  @Test
  void testSaveFeedback() {
    Mockito.when(dtoService.convertDtoToEntity(feedbackDto)).thenReturn(feedback);
    Mockito.when(dtoService.convertEntityToDto(feedbackSaved)).thenReturn(feedbackDto);
    Mockito.when(feedbackService.saveFeedback(feedback)).thenReturn(feedbackSaved);
    assertSame(feedbackDto, feedbackController.save(feedbackDto));
  }

  @Test
  void testSaveFeedbacks() {
    Mockito.when(dtoService.convertDtoToEntity(feedbackDto)).thenReturn(feedback);
    Mockito.when(dtoService.convertEntityToDto(feedbackSaved)).thenReturn(feedbackDto);
    Mockito.when(feedbackService.saveFeedbacks(List.of(feedback, feedback))).thenReturn(List.of(feedbackSaved, feedbackSaved));
    assertArrayEquals(List.of(feedbackDto, feedbackDto).toArray(), feedbackController.save(List.of(feedbackDto, feedbackDto)).toArray());
  }

  @Test
  void testDeleteFeedbackById() {
    feedbackController.deleteFeedbackById(1);
    Mockito.verify(feedbackService).deleteFeedbackById(1);
  }

  @Test
  void testGetFeedbackById() {
    Mockito.when(dtoService.convertEntityToDto(feedback)).thenReturn(feedbackDto);
    Mockito.when(feedbackService.findFeedbackById(1)).thenReturn(feedback);
    assertSame(feedbackDto, feedbackController.getFeedbackById(1));

    Mockito.when(feedbackService.findFeedbackById(not(eq(1)))).thenReturn(null);
    assertThrows(FeedbackNotFoundException.class, () -> feedbackController.getFeedbackById(2));
  }

  @Test
  void testGetAllFeedbacks() {
    Mockito.when(dtoService.convertEntityToDto(feedback)).thenReturn(feedbackDto);
    Mockito.when(feedbackService.findAllFeedbacks()).thenReturn(List.of(feedback, feedback));
    assertArrayEquals(List.of(feedbackDto, feedbackDto).toArray(), feedbackController.getAllFeedbacks().toArray());
  }
}
