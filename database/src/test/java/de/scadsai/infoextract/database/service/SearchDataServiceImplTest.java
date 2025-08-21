package de.scadsai.infoextract.database.service;

import de.scadsai.infoextract.database.entity.SearchData;
import de.scadsai.infoextract.database.entity.Drawing;
import de.scadsai.infoextract.database.repository.SearchDataRepository;
import de.scadsai.infoextract.database.repository.DrawingRepository;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertIterableEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;

@SpringBootTest
class SearchDataServiceImplTest {

  @Mock
  private SearchDataRepository searchDataRepository;
  @Mock
  private DrawingRepository drawingRepository;
  @Mock
  SearchData searchData1;
  @Mock
  SearchData searchData2;
  @Mock
  Drawing drawing1;
  @InjectMocks
  private SearchDataServiceImpl searchDataService;

  @Test
  void testSaveSearchData() {
    Mockito.when(searchDataRepository.save(searchData1)).thenReturn(searchData1);
    SearchData searchDataSaved = searchDataService.saveSearchData(searchData1);

    assertNotNull(searchDataSaved);
    Mockito.verify(searchDataRepository).save(Mockito.same(searchData1));
    Mockito.verifyNoInteractions(searchData1);
    Mockito.verifyNoMoreInteractions(searchDataRepository);
  }

  @Test
  void testSaveSearchDataList() {
    List<SearchData> searchDataList = List.of(searchData1, searchData2);
    List<SearchData> spy = Mockito.spy(searchDataList);
    Mockito.when(searchDataRepository.saveAll(spy)).thenReturn(spy);
    List<SearchData> searchDataListSaved = searchDataService.saveSearchDataList(spy);

    assertNotNull(searchDataListSaved);
    assertFalse(searchDataListSaved.isEmpty());
    Mockito.verify(searchDataRepository).saveAll(Mockito.same(spy));
    Mockito.verifyNoMoreInteractions(searchDataRepository);
  }

  @Test
  void testFindSearchDataById() {
    final int searchDataId = 1;
    Mockito.when(searchDataRepository.findById(searchDataId)).thenReturn(Optional.of(searchData1));

    assertSame(searchData1, searchDataService.findSearchDataById(searchDataId));
    Mockito.verify(searchDataRepository).findById(Mockito.same(searchDataId));
    Mockito.verifyNoInteractions(searchData1);
    Mockito.verifyNoMoreInteractions(searchDataRepository);
  }

  @Test
  void testFindSearchDataByUnknownId() {
    final int searchDataId = 0;
    Mockito.when(searchDataRepository.findById(searchDataId)).thenReturn(Optional.empty());

    assertNull(searchDataService.findSearchDataById(searchDataId));
    Mockito.verify(searchDataRepository).findById(Mockito.same(searchDataId));
    Mockito.verifyNoMoreInteractions(searchDataRepository);
  }

  @Test
  void testFindSearchDataByDrawingId() {
    final int drawingId = 1;
    Mockito.when(searchDataRepository.findSearchDataByDrawing_DrawingId(drawingId)).thenReturn(Optional.of(searchData1));

    assertSame(searchData1, searchDataService.findSearchDataByDrawingId(drawingId));
    Mockito.verify(searchDataRepository).findSearchDataByDrawing_DrawingId(Mockito.same(drawingId));
    Mockito.verifyNoInteractions(searchData1);
    Mockito.verifyNoMoreInteractions(searchDataRepository);
  }

  @Test
  void testFindAllSearchData() {
    List<SearchData> searchDataList = List.of(searchData1, searchData2);
    List<SearchData> spy = Mockito.spy(searchDataList);
    Mockito.when(searchDataRepository.findAll()).thenReturn(spy);

    assertIterableEquals(searchDataList, searchDataService.findAllSearchData());
    Mockito.verify(searchDataRepository).findAll();
    Mockito.verifyNoMoreInteractions(searchDataRepository);
  }

  @Test
  void testDeleteSearchDataById() {
    final int searchDataId = 1;

    Mockito.when(searchDataRepository.findById(searchDataId)).thenReturn(Optional.of(searchData1));
    Mockito.when(searchData1.getDrawing()).thenReturn(drawing1);

    searchDataService.deleteSearchDataById(searchDataId);

    Mockito.verify(searchDataRepository).findById(Mockito.same(searchDataId));
    Mockito.verify(drawing1).setSearchData(null);
    Mockito.verify(drawingRepository).save(drawing1);
    Mockito.verify(searchDataRepository).deleteById(Mockito.same(searchDataId));
    Mockito.verifyNoMoreInteractions(drawingRepository);
    Mockito.verifyNoMoreInteractions(searchDataRepository);
  }

  @Test
  void testDeleteSearchDataByDrawingId() {
    final int drawingId = 1;

    Mockito.when(drawingRepository.findById(drawingId)).thenReturn(Optional.of(drawing1));
    Mockito.when(drawing1.getSearchData()).thenReturn(searchData1);
    Mockito.when(searchData1.getSearchDataId()).thenReturn(1);

    searchDataService.deleteSearchDataByDrawingId(drawingId);

    Mockito.verify(drawingRepository).findById(drawingId);
    Mockito.verify(drawing1).setSearchData(null);
    Mockito.verify(drawingRepository).save(drawing1);
    Mockito.verify(searchDataRepository).deleteSearchDataByDrawing_DrawingId(Mockito.same(drawingId));
    Mockito.verifyNoMoreInteractions(drawingRepository);
    Mockito.verifyNoMoreInteractions(searchDataRepository);
  }
}
