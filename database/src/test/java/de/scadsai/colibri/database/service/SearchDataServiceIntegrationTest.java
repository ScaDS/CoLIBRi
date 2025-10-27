package de.scadsai.colibri.database.service;

import de.scadsai.colibri.database.entity.SearchData;
import de.scadsai.colibri.database.exception.DrawingNotFoundException;
import de.scadsai.colibri.database.exception.SearchDataNotFoundException;
import de.scadsai.colibri.database.repository.SearchDataRepository;
import de.scadsai.colibri.database.entity.Drawing;
import de.scadsai.colibri.database.repository.DrawingRepository;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.io.IOException;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

@SpringBootTest
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class SearchDataServiceIntegrationTest {

  @Autowired
  private SearchDataService searchDataService;
  @Autowired
  private SearchDataRepository searchDataRepository;
  @Autowired
  private DrawingRepository drawingRepository;

  private static final int searchData1Id = 1;
  private SearchData searchData1;
  private static final int searchData2Id = 2;
  private SearchData searchData2;

  private static final int drawing1Id = 1;
  private Drawing drawing1;
  private static final int drawing2Id = 2;
  private Drawing drawing2;

  @BeforeAll
  void initObjects() throws IOException {
    drawing1 = new Drawing();
    drawing1.setDrawingId(drawing1Id);
    drawing1.setOriginalDrawing(new byte[] {});
    drawing1.setRuntimes(Collections.emptyList());
    // Don't reference searchdata here

    drawing2 = new Drawing();
    drawing2.setDrawingId(drawing2Id);
    drawing2.setOriginalDrawing(new byte[] {});
    drawing2.setRuntimes(Collections.emptyList());
    // Don't reference searchdata here

    searchData1 = new SearchData();
    searchData1.setSearchDataId(searchData1Id);
    searchData1.setDrawing(drawing1);
    searchData1.setShape(new float[]{});
    searchData1.setMaterial(new String[]{});
    searchData1.setGeneralTolerances(new String[]{});
    searchData1.setSurfaces(new String[]{});
    searchData1.setGdts(new String[]{});
    searchData1.setThreads(new String[]{});
    searchData1.setOuterDimensions(new float[]{});
    searchData1.setSearchVector(new float[]{});

    searchData2 = new SearchData();
    searchData2.setSearchDataId(searchData2Id);
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

  @BeforeEach
  void initRepository() {
    // because of one-to-one relation for searchdata-drawing, we need to empty drawings, too
    drawingRepository.deleteAll();
    searchDataRepository.deleteAll();
    assertEquals(0L, searchDataRepository.count());
    // store drawings without referenced searchdata
    drawingRepository.saveAll(List.of(drawing1, drawing2));
    assertEquals(2L, drawingRepository.count());
    assertEquals(0L, searchDataRepository.count());
  }

  @AfterAll
  void cleanUp() {
    drawingRepository.deleteAll();
    assertEquals(0L, drawingRepository.count());
    searchDataRepository.deleteAll();
    assertEquals(0L, searchDataRepository.count());
  }

  @Test
  void testSaveSearchData() {
    searchDataService.saveSearchData(searchData1);
    assertEquals(1L, searchDataRepository.count());
  }

  @Test
  void testSaveSearchDataList() {
    searchDataService.saveSearchDataList(List.of(searchData1, searchData2));
    assertEquals(2L, searchDataRepository.count());
  }

  @Test
  void testSaveSearchDataForUnknownDrawing() {
    Drawing drawing = new Drawing();
    drawing.setDrawingId(10);

    SearchData invalidSearchData = new SearchData();
    invalidSearchData.setSearchDataId(5);
    invalidSearchData.setDrawing(drawing);
    invalidSearchData.setShape(new float[]{});
    invalidSearchData.setMaterial(new String[]{});
    invalidSearchData.setGeneralTolerances(new String[]{});
    invalidSearchData.setSurfaces(new String[]{});
    invalidSearchData.setGdts(new String[]{});
    invalidSearchData.setThreads(new String[]{});
    invalidSearchData.setOuterDimensions(new float[]{});
    invalidSearchData.setSearchVector(new float[]{});

    assertThrows(DrawingNotFoundException.class, () -> searchDataService.saveSearchData(invalidSearchData));
  }

  @Test
  void testFindSearchDataById() {
    searchDataRepository.save(searchData1);
    assertEquals(1L, searchDataRepository.count());

    SearchData searchDataFound = searchDataService.findSearchDataById(searchData1Id);
    assertNotNull(searchDataFound);
    assertEquals(searchData1.getSearchDataId(), searchDataFound.getSearchDataId());
    assertEquals(searchData1.getDrawing().getDrawingId(), searchDataFound.getDrawing().getDrawingId());
    assertArrayEquals(searchData1.getShape(), searchDataFound.getShape());
    assertArrayEquals(searchData1.getMaterial(), searchDataFound.getMaterial());
    assertArrayEquals(searchData1.getGeneralTolerances(), searchDataFound.getGeneralTolerances());
    assertArrayEquals(searchData1.getSurfaces(), searchDataFound.getSurfaces());
    assertArrayEquals(searchData1.getGdts(), searchDataFound.getGdts());
    assertArrayEquals(searchData1.getThreads(), searchDataFound.getThreads());
    assertArrayEquals(searchData1.getOuterDimensions(), searchDataFound.getOuterDimensions());
    assertArrayEquals(searchData1.getSearchVector(), searchDataFound.getSearchVector());
  }

  @Test
  void testFindSearchDataByDrawingId() {
    searchDataRepository.save(searchData2);
    assertEquals(1L, searchDataRepository.count());

    SearchData searchDataFound = searchDataService.findSearchDataByDrawingId(2);
    assertNotNull(searchDataFound);
    assertEquals(searchData2.getSearchDataId(), searchDataFound.getSearchDataId());
    assertEquals(searchData2.getDrawing().getDrawingId(), searchDataFound.getDrawing().getDrawingId());
    assertArrayEquals(searchData2.getShape(), searchDataFound.getShape());
    assertArrayEquals(searchData2.getMaterial(), searchDataFound.getMaterial());
    assertArrayEquals(searchData2.getGeneralTolerances(), searchDataFound.getGeneralTolerances());
    assertArrayEquals(searchData2.getSurfaces(), searchDataFound.getSurfaces());
    assertArrayEquals(searchData2.getGdts(), searchDataFound.getGdts());
    assertArrayEquals(searchData2.getThreads(), searchDataFound.getThreads());
    assertArrayEquals(searchData2.getOuterDimensions(), searchDataFound.getOuterDimensions());
    assertArrayEquals(searchData2.getSearchVector(), searchDataFound.getSearchVector());
  }

  @Test
  void testFindAllSearchData() {
    searchDataRepository.saveAll(List.of(searchData1, searchData2));
    assertEquals(2L, searchDataRepository.count());

    List<SearchData> searchDataListFound = searchDataService.findAllSearchData();
    assertNotNull(searchDataListFound);
    assertEquals(2, searchDataListFound.size());
  }

  @Test
  void testDeleteSearchDataById() {
    searchDataRepository.saveAll(List.of(searchData1, searchData2));
    assertEquals(2L, searchDataRepository.count());

    searchDataService.deleteSearchDataById(searchData1Id);
    assertEquals(1L, searchDataRepository.count());
    assertFalse(searchDataRepository.existsById(searchData1Id));

    assertThrows(SearchDataNotFoundException.class, () -> searchDataService.deleteSearchDataById(3));
  }

  @Test
  void testDeleteSearchDataByDrawingId() {
    searchDataRepository.saveAll(List.of(searchData1, searchData2));
    assertEquals(2L, searchDataRepository.count());

    searchDataService.deleteSearchDataByDrawingId(2);
    assertEquals(1L, searchDataRepository.count());
    assertFalse(searchDataRepository.existsById(searchData2Id));

    assertThrows(DrawingNotFoundException.class, () -> searchDataService.deleteSearchDataByDrawingId(3));
  }
}
