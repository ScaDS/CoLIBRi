package de.scadsai.infoextract.database.service;

import de.scadsai.infoextract.database.entity.History;
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
class HistoryServiceImplTest {

  @Mock
  private HistoryRepository historyRepository;
  @Mock
  History history1;
  @Mock
  History history2;
  @InjectMocks
  private HistoryServiceImpl historyService;

  @Test
  void testSaveHistory() {
    Mockito.when(historyRepository.save(history1)).thenReturn(history1);
    History historySaved = historyService.saveHistory(history1);

    assertNotNull(historySaved);
    Mockito.verify(historyRepository).save(Mockito.same(history1));
    Mockito.verifyNoInteractions(history1);
    Mockito.verifyNoMoreInteractions(historyRepository);
  }

  @Test
  void testSaveHistories() {
    List<History> histories = List.of(history1, history2);
    List<History> spy = Mockito.spy(histories);
    Mockito.when(historyRepository.saveAll(spy)).thenReturn(spy);
    List<History> historiesSaved = historyService.saveHistories(spy);

    assertNotNull(historiesSaved);
    assertFalse(historiesSaved.isEmpty());
    Mockito.verify(historyRepository).saveAll(Mockito.same(spy));
    Mockito.verifyNoMoreInteractions(historyRepository);
  }

  @Test
  void testFindHistoryById() {
    final int historyId = 1;
    Mockito.when(historyRepository.findById(historyId)).thenReturn(Optional.of(history1));

    assertSame(history1, historyService.findHistoryById(historyId));
    Mockito.verify(historyRepository).findById(Mockito.same(historyId));
    Mockito.verifyNoInteractions(history1);
    Mockito.verifyNoMoreInteractions(historyRepository);
  }

  @Test
  void testFindHistoryByUnknownId() {
    final int historyId = 0;
    Mockito.when(historyRepository.findById(historyId)).thenReturn(Optional.empty());

    assertNull(historyService.findHistoryById(historyId));
    Mockito.verify(historyRepository).findById(Mockito.same(historyId));
    Mockito.verifyNoMoreInteractions(historyRepository);
  }


  @Test
  void testFindAllHistories() {
    List<History> histories = List.of(history1, history2);
    List<History> spy = Mockito.spy(histories);
    Mockito.when(historyRepository.findAll()).thenReturn(spy);

    assertIterableEquals(histories, historyService.findAllHistories());
    Mockito.verify(historyRepository).findAll();
    Mockito.verifyNoMoreInteractions(historyRepository);
  }

  @Test
  void testDeleteHistoryById() {
    final int historyId = 1;
    historyService.deleteHistoryById(historyId);

    Mockito.verify(historyRepository).deleteById(Mockito.same(historyId));
    Mockito.verifyNoMoreInteractions(historyRepository);
  }
}
