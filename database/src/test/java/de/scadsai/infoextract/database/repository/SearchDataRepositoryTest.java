package de.scadsai.infoextract.database.repository;

import com.fasterxml.jackson.core.json.JsonWriteFeature;
import de.scadsai.infoextract.database.entity.Drawing;
import de.scadsai.infoextract.database.entity.SearchData;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;

import java.io.IOException;
import java.util.List;
import java.util.Optional;

import static org.hamcrest.Matchers.samePropertyValuesAs;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertIterableEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.ObjectMapper;

@DataJpaTest
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class SearchDataRepositoryTest {

  @Autowired
  private TestEntityManager testEntityManager;
  @Autowired
  private SearchDataRepository searchDataRepository;
  @Autowired
  private DrawingRepository drawingRepository;

  private static final int searchData1Id = 1;
  private SearchData searchData1;
  private static final int searchData2Id = 2;
  private SearchData searchData2;
  private static final int searchData3Id = 3;
  private SearchData searchData3;
  private static final int searchData4Id = 4;
  private SearchData searchData4;
  private static final int drawing1Id = 1;
  private static final int drawing2Id = 2;
  private static final int drawing3Id = 3;
  private static final int drawing4Id = 4;

  @BeforeAll
  void initObjects() throws IOException {
    Drawing drawing1 = new Drawing();
    drawing1.setDrawingId(drawing1Id);

    Drawing drawing2 = new Drawing();
    drawing2.setDrawingId(drawing2Id);

    Drawing drawing3 = new Drawing();
    drawing3.setDrawingId(drawing3Id);

    Drawing drawing4 = new Drawing();
    drawing4.setDrawingId(drawing4Id);

    drawingRepository.saveAll(List.of(drawing1, drawing2, drawing3, drawing4));
    assertEquals(4L, drawingRepository.count());

    ObjectMapper objectMapper = new ObjectMapper();
    //deprecated: objectMapper.configure(JsonGenerator.Feature.ESCAPE_NON_ASCII, true);
    objectMapper.configure(JsonWriteFeature.ESCAPE_NON_ASCII.mappedFeature(), true);

    searchData1 = new SearchData();
    searchData1.setSearchDataId(searchData1Id);
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

    searchData3 = new SearchData();
    searchData3.setSearchDataId(searchData3Id);
    searchData3.setDrawing(drawing3);
    searchData3.setShape(new float[]{
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
    searchData3.setMaterial(material);
    searchData3.setGeneralTolerances(generalTolerances);
    searchData3.setSurfaces(new String[]{"Ra 0.5", "Ra 1.2"});
    searchData3.setGdts(gdts);
    searchData3.setThreads(new String[]{"M5x0.8", "NPT 1/2"});
    searchData3.setOuterDimensions(new float[]{10f, 20f, 30f});
    searchData3.setSearchVector(new float[]{
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

    searchData4 = new SearchData();
    searchData4.setSearchDataId(searchData4Id);
    searchData4.setDrawing(drawing4);
    searchData4.setShape(new float[]{});
    searchData4.setMaterial(new String[]{});
    searchData4.setGeneralTolerances(new String[]{});
    searchData4.setSurfaces(new String[]{});
    searchData4.setGdts(new String[]{});
    searchData4.setThreads(new String[]{});
    searchData4.setOuterDimensions(new float[]{});
    searchData4.setSearchVector(new float[]{});
  }

  @BeforeEach
  void populateRepository() {
    searchDataRepository.deleteAll();
    assertEquals(0L, searchDataRepository.count());

    testEntityManager.persist(searchData1);
    testEntityManager.persist(searchData2);
    assertEquals(2L, searchDataRepository.count());
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
    SearchData searchDataSaved = searchDataRepository.save(searchData3);
    assertNotNull(searchDataSaved);
    assertEquals(3L, searchDataRepository.count());
    assertTrue(searchDataRepository.existsById(searchData3Id));
  }

  @Test
  void testSaveSearchDataList() {
    Iterable<SearchData> searchDataListSaved = searchDataRepository.saveAll(List.of(searchData3, searchData4));
    assertNotNull(searchDataListSaved);
    assertEquals(4L, searchDataRepository.count());
    assertTrue(searchDataRepository.existsById(searchData3Id));
    assertTrue(searchDataRepository.existsById(searchData4Id));
  }

  @Test
  void testFindSearchDataById() {
    Optional<SearchData> result = searchDataRepository.findById(searchData1Id);
    assertTrue(result.isPresent());
    assertThat(searchData1, samePropertyValuesAs(result.get()));
  }

  @Test
  void testFindSearchDataByDrawingId() {
    Optional<SearchData> result = searchDataRepository.findSearchDataByDrawing_DrawingId(drawing1Id);
    assertTrue(result.isPresent());
    assertThat(searchData1, samePropertyValuesAs(result.get()));
  }

  @Test
  void testFindAllSearchData() {
    Iterable<SearchData> result = searchDataRepository.findAll();
    assertIterableEquals(result, List.of(searchData1, searchData2));
  }

  @Test
  void testDeleteSearchDataById() {
    searchDataRepository.deleteById(searchData1Id);
    assertEquals(1L, searchDataRepository.count());
    assertFalse(searchDataRepository.existsById(searchData1Id));
  }

  @Test
  void testDeleteSearchDataByDrawingId() {
    searchDataRepository.saveAll(List.of(searchData3, searchData4));
    assertEquals(4L, searchDataRepository.count());

    searchDataRepository.deleteSearchDataByDrawing_DrawingId(drawing1Id);
    assertEquals(3L, searchDataRepository.count());
    assertFalse(searchDataRepository.existsById(searchData1Id));

    searchDataRepository.deleteSearchDataByDrawing_DrawingId(drawing3Id);
    assertEquals(2L, searchDataRepository.count());
    assertFalse(searchDataRepository.existsById(searchData3Id));
  }
}
