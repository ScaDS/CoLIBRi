package de.scadsai.infoextract.database.controller;

import de.scadsai.infoextract.database.dto.HistoryDto;
import de.scadsai.infoextract.database.entity.History;
import de.scadsai.infoextract.database.exception.HistoryNotFoundException;
import de.scadsai.infoextract.database.service.HistoryService;
import de.scadsai.infoextract.database.service.DtoService;
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
class HistoryControllerTest {

  @Mock
  HistoryService historyService;
  @Mock
  DtoService dtoService;
  @Mock
  History history;
  @Mock
  History historySaved;
  @Mock
  HistoryDto historyDto;
  @InjectMocks
  HistoryController historyController;

  @Test
  void testSaveHistory() {
    Mockito.when(dtoService.convertDtoToEntity(historyDto)).thenReturn(history);
    Mockito.when(dtoService.convertEntityToDto(historySaved)).thenReturn(historyDto);
    Mockito.when(historyService.saveHistory(history)).thenReturn(historySaved);
    assertSame(historyDto, historyController.save(historyDto));
  }

  @Test
  void testSaveHistories() {
    Mockito.when(dtoService.convertDtoToEntity(historyDto)).thenReturn(history);
    Mockito.when(dtoService.convertEntityToDto(historySaved)).thenReturn(historyDto);
    Mockito.when(historyService.saveHistories(List.of(history, history))).thenReturn(List.of(historySaved, historySaved));
    assertArrayEquals(List.of(historyDto, historyDto).toArray(), historyController.save(List.of(historyDto, historyDto)).toArray());
  }

  @Test
  void testDeleteHistoryById() {
    historyController.deleteHistoryById(1);
    Mockito.verify(historyService).deleteHistoryById(1);
  }

  @Test
  void testGetHistoryById() {
    Mockito.when(dtoService.convertEntityToDto(history)).thenReturn(historyDto);
    Mockito.when(historyService.findHistoryById(1)).thenReturn(history);
    assertSame(historyDto, historyController.getHistoryById(1));

    Mockito.when(historyService.findHistoryById(not(eq(1)))).thenReturn(null);
    assertThrows(HistoryNotFoundException.class, () -> historyController.getHistoryById(2));
  }

  @Test
  void testGetAllHistories() {
    Mockito.when(dtoService.convertEntityToDto(history)).thenReturn(historyDto);
    Mockito.when(historyService.findAllHistories()).thenReturn(List.of(history, history));
    assertArrayEquals(List.of(historyDto, historyDto).toArray(), historyController.getAllHistories().toArray());
  }
}
