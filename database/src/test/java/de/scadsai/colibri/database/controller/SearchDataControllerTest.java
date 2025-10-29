package de.scadsai.colibri.database.controller;

import de.scadsai.colibri.database.exception.SearchDataNotFoundException;
import de.scadsai.colibri.database.dto.SearchDataDto;
import de.scadsai.colibri.database.entity.SearchData;
import de.scadsai.colibri.database.exception.SearchDataNotFoundForDrawingException;
import de.scadsai.colibri.database.service.SearchDataService;
import de.scadsai.colibri.database.service.DtoService;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.AdditionalMatchers.not;
import static org.mockito.ArgumentMatchers.eq;

@SpringBootTest
class SearchDataControllerTest {

  @Mock
  SearchDataService searchDataService;
  @Mock
  DtoService dtoService;
  @Mock
  SearchData searchData;
  @Mock
  SearchData searchDataSaved;
  @Mock
  SearchDataDto searchDataDto;
  @InjectMocks
  SearchDataController searchDataController;

  @Test
  void testSaveSearchData() {
    Mockito.when(dtoService.convertDtoToEntity(searchDataDto)).thenReturn(searchData);
    Mockito.when(dtoService.convertEntityToDto(searchDataSaved)).thenReturn(searchDataDto);
    Mockito.when(searchDataService.saveSearchData(searchData)).thenReturn(searchDataSaved);
    assertSame(searchDataDto, searchDataController.save(searchDataDto));
  }

  @Test
  void testSaveSearchDataList() {
    Mockito.when(dtoService.convertDtoToEntity(searchDataDto)).thenReturn(searchData);
    Mockito.when(dtoService.convertEntityToDto(searchDataSaved)).thenReturn(searchDataDto);
    Mockito.when(searchDataService.saveSearchDataList(List.of(searchData, searchData))).thenReturn(List.of(searchDataSaved, searchDataSaved));
    assertArrayEquals(List.of(searchDataDto, searchDataDto).toArray(), searchDataController.save(List.of(searchDataDto, searchDataDto)).toArray());
  }

  @Test
  void testDeleteSearchDataById() {
    searchDataController.deleteSearchDataById(1);
    Mockito.verify(searchDataService).deleteSearchDataById(1);
  }

  @Test
  void testDeleteSearchDataByDrawingId() {
    searchDataController.deleteSearchDataByDrawingId(1);
    Mockito.verify(searchDataService).deleteSearchDataByDrawingId(1);
  }

  @Test
  void testGetSearchDataById() {
    Mockito.when(dtoService.convertEntityToDto(searchData)).thenReturn(searchDataDto);
    Mockito.when(searchDataService.findSearchDataById(1)).thenReturn(searchData);
    assertSame(searchDataDto, searchDataController.getSearchDataById(1));

    Mockito.when(searchDataService.findSearchDataById(not(eq(1)))).thenReturn(null);
    assertThrows(SearchDataNotFoundException.class, () -> searchDataController.getSearchDataById(2));
  }

  @Test
  void testGetSearchDataByDrawingId() {
    Mockito.when(dtoService.convertEntityToDto(searchData)).thenReturn(searchDataDto);
    Mockito.when(searchDataService.findSearchDataByDrawingId(1)).thenReturn(searchData);
    assertSame(searchDataDto, searchDataController.getSearchDataByDrawingId(1));

    Mockito.when(searchDataService.findSearchDataByDrawingId(not(eq(1)))).thenReturn(null);
    assertThrows(SearchDataNotFoundForDrawingException.class, () -> searchDataController.getSearchDataByDrawingId(2));
  }

  @Test
  void testGetAllSearchData() {
    Mockito.when(dtoService.convertEntityToDto(searchData)).thenReturn(searchDataDto);
    Mockito.when(searchDataService.findAllSearchData()).thenReturn(List.of(searchData, searchData));
    assertArrayEquals(List.of(searchDataDto, searchDataDto).toArray(), searchDataController.getAllSearchData().toArray());
  }
}
