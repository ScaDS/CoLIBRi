package de.scadsai.infoextract.database.service;

import de.scadsai.infoextract.database.entity.Feedback;
import de.scadsai.infoextract.database.entity.History;
import de.scadsai.infoextract.database.repository.FeedbackRepository;
import de.scadsai.infoextract.database.repository.HistoryRepository;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
class FeedbackServiceImplTest {

  @Mock
  private FeedbackRepository feedbackRepository;
  @Mock
  private HistoryRepository historyRepository;
  @Mock
  private Feedback feedback1;
  @Mock
  private Feedback feedback2;
  @Mock
  private History historyMock;
  @InjectMocks
  private FeedbackServiceImpl feedbackService;

  @Test
  void testSaveFeedback() {
    Mockito.when(feedback1.getHistory()).thenReturn(historyMock);
    Mockito.when(historyMock.getHistoryId()).thenReturn(1);
    Mockito.when(historyRepository.findById(1)).thenReturn(Optional.of(historyMock));
    Mockito.doNothing().when(historyMock).addFeedback(feedback1);
    Mockito.when(feedbackRepository.save(feedback1)).thenReturn(feedback1);

    Feedback feedbackSaved = feedbackService.saveFeedback(feedback1);
    assertNotNull(feedbackSaved);

    Mockito.verify(historyRepository).findById(1);
    Mockito.verify(historyMock).getHistoryId();
    Mockito.verify(historyMock).addFeedback(feedback1);
    Mockito.verify(feedbackRepository).save(Mockito.same(feedback1));
    Mockito.verifyNoMoreInteractions(historyRepository, feedbackRepository, historyMock);
  }

  @Test
  void testSaveFeedbacks() {
    List<Feedback> feedbacks = List.of(feedback1, feedback2);
    List<Feedback> spy = Mockito.spy(feedbacks);
    Mockito.when(feedbackRepository.saveAll(spy)).thenReturn(spy);
    List<Feedback> feedbacksSaved = feedbackService.saveFeedbacks(spy);

    assertNotNull(feedbacksSaved);
    assertFalse(feedbacksSaved.isEmpty());
    Mockito.verify(feedbackRepository).saveAll(Mockito.same(spy));
    Mockito.verifyNoMoreInteractions(feedbackRepository);
  }

  @Test
  void testFindFeedbackById() {
    final int feedbackId = 1;
    Mockito.when(feedbackRepository.findById(feedbackId)).thenReturn(Optional.of(feedback1));

    assertSame(feedback1, feedbackService.findFeedbackById(feedbackId));
    Mockito.verify(feedbackRepository).findById(Mockito.same(feedbackId));
    Mockito.verifyNoInteractions(feedback1);
    Mockito.verifyNoMoreInteractions(feedbackRepository);
  }

  @Test
  void testFindFeedbackByUnknownId() {
    final int feedbackId = 0;
    Mockito.when(feedbackRepository.findById(feedbackId)).thenReturn(Optional.empty());

    assertNull(feedbackService.findFeedbackById(feedbackId));
    Mockito.verify(feedbackRepository).findById(Mockito.same(feedbackId));
    Mockito.verifyNoMoreInteractions(feedbackRepository);
  }

  @Test
  void testFindFeedbackByHistoryId() {
    final int historyId = 1;
    List<Feedback> feedbacks = List.of(feedback1);
    List<Feedback> spy = Mockito.spy(feedbacks);
    Mockito.when(feedbackRepository.findFeedbacksByHistoryHistoryId(historyId)).thenReturn(spy);

    assertIterableEquals(List.of(feedback1), feedbackService.findFeedbacksByHistoryId(historyId));
    Mockito.verify(feedbackRepository).findFeedbacksByHistoryHistoryId(historyId);
    Mockito.verifyNoMoreInteractions(feedbackRepository);
  }

  @Test
  void testFindAllFeedbacks() {
    List<Feedback> feedbacks = List.of(feedback1, feedback2);
    List<Feedback> spy = Mockito.spy(feedbacks);
    Mockito.when(feedbackRepository.findAll()).thenReturn(spy);

    assertIterableEquals(feedbacks, feedbackService.findAllFeedbacks());
    Mockito.verify(feedbackRepository).findAll();
    Mockito.verifyNoMoreInteractions(feedbackRepository);
  }

  @Test
  void testDeleteFeedbackById() {
    final int feedbackId = 1;
    feedbackService.deleteFeedbackById(feedbackId);

    Mockito.verify(feedbackRepository).deleteById(Mockito.same(feedbackId));
    Mockito.verifyNoMoreInteractions(feedbackRepository);
  }
}
