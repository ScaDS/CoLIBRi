package de.scadsai.infoextract.database.service;

import com.fasterxml.jackson.core.json.JsonWriteFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import de.scadsai.infoextract.database.dto.DrawingDto;
import de.scadsai.infoextract.database.dto.RuntimeDto;
import de.scadsai.infoextract.database.entity.Drawing;
import de.scadsai.infoextract.database.dto.SearchDataDto;
import de.scadsai.infoextract.database.entity.SearchData;
import de.scadsai.infoextract.database.entity.Runtime;
import de.scadsai.infoextract.database.dto.FeedbackDto;
import de.scadsai.infoextract.database.exception.DrawingNotFoundException;
import de.scadsai.infoextract.database.repository.DrawingRepository;
import de.scadsai.infoextract.database.repository.HistoryRepository;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;

import java.io.IOException;
import java.util.Base64;
import java.util.Collections;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class DtoServiceImplTest {

  @Mock
  private DrawingRepository drawingRepository;
  // @InjectMock will fail here for unknown reason, probably in combination with static @BeforeAll
  // It will create multiple mocks for drawingRepository, failing to reference the currently used one
  // We use @BeforeEach to set up the dtoService with the  single mock properly
  private DtoServiceImpl dtoService;

  @Autowired
  ResourceLoader resourceLoader;

  private byte[] imageByteArray;
  private SearchData searchData;
  @Autowired
  private HistoryRepository historyRepository;

  @BeforeAll
  void initObjects() throws IOException {
    // load image byte array
    Resource imageFileResource = resourceLoader.getResource("classpath:data/example_drawing.pdf");
    assertNotNull(imageFileResource);
    assertTrue(imageFileResource.getFile().exists());
    imageByteArray = imageFileResource.getInputStream().readAllBytes();
    assertTrue(imageByteArray.length > 0);

    // init search data
    ObjectMapper objectMapper = new ObjectMapper();
    //deprecated: objectMapper.configure(JsonGenerator.Feature.ESCAPE_NON_ASCII, true);
    objectMapper.configure(JsonWriteFeature.ESCAPE_NON_ASCII.mappedFeature(), true);

    Drawing drawing = new Drawing();
    drawing.setDrawingId(1);
    drawing.setOriginalDrawing(imageByteArray);

    searchData = new SearchData();
    searchData.setSearchDataId(1);
    searchData.setDrawing(drawing);
    searchData.setShape(new float[]{
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
    searchData.setMaterial(material);
    String[][] generalTolerances2d = new String[][]{{"f", "h"}, {"m", "k"}};
    String[] generalTolerances = new String[generalTolerances2d.length];
    for (int i = 0; i < generalTolerances2d.length; i++) {
      generalTolerances[i] = objectMapper.writeValueAsString(generalTolerances2d[i]);
    }
    searchData.setGeneralTolerances(generalTolerances);
    searchData.setSurfaces(new String[]{"Ra 0.5", "Ra 1.2"});
    String[] gdts = new String[]{"⌾ 0.02 A", "◯0.1BC"};
    for (int i = 0; i < gdts.length; i++) {
      gdts[i] = objectMapper.writeValueAsString(gdts[i]);
    }
    searchData.setGdts(gdts);
    searchData.setThreads(new String[]{"M5x0.8", "NPT 1/2"});
    searchData.setOuterDimensions(new float[]{10f, 20f, 30f});
    searchData.setSearchVector(new float[]{
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
  }

  @BeforeEach
  void setUp() {
    dtoService = new DtoServiceImpl(drawingRepository, historyRepository);
  }

  @Test
  void testConvertEntityToDtoForDrawing() {
    Drawing drawing = new Drawing();
    drawing.setDrawingId(1);
    drawing.setOriginalDrawing(imageByteArray);

    Runtime runtime = new Runtime();
    runtime.setRuntimeId(1);
    runtime.setDrawing(drawing);
    runtime.setMachine("machine1");
    runtime.setMachineRuntime(1f);
    drawing.setRuntimes(Collections.singletonList(runtime));

    SearchData searchData2 = new SearchData();
    searchData2.setSearchDataId(1);
    searchData2.setDrawing(drawing);
    searchData2.setShape(new float[]{});
    searchData2.setMaterial(new String[]{});
    searchData2.setGeneralTolerances(new String[]{});
    searchData2.setSurfaces(new String[]{});
    searchData2.setGdts(new String[]{});
    searchData2.setThreads(new String[]{});
    searchData2.setOuterDimensions(new float[]{});
    searchData2.setSearchVector(new float[]{});
    drawing.setSearchData(searchData2);

    DrawingDto drawingDto = dtoService.convertEntityToDto(drawing);

    assertEquals(drawing.getDrawingId(), drawingDto.getDrawingId());
    assertEquals(Base64.getEncoder().encodeToString(imageByteArray), drawingDto.getOriginalDrawing());
    // compare runtimes to drawings' runtimes dto
    assertFalse(drawingDto.getRuntimes().isEmpty());
    assertNotNull(drawingDto.getRuntimes().getFirst());
    RuntimeDto runtimeDto = drawingDto.getRuntimes().getFirst();
    assertEquals(runtime.getRuntimeId(), runtimeDto.getRuntimeId());
    assertEquals(drawing.getDrawingId(), runtimeDto.getDrawingId());
    assertEquals(runtime.getMachine(), runtimeDto.getMachine());
    assertEquals(runtime.getMachineRuntime(), runtimeDto.getMachineRuntime());
    // compare searchdata to drawings' searchdata dto
    assertNotNull(drawingDto.getSearchData());
    SearchDataDto searchDataDto = drawingDto.getSearchData();
    assertEquals(searchData2.getSearchDataId(), searchDataDto.getSearchDataId());
    assertEquals(drawing.getDrawingId(), searchDataDto.getDrawingId());
    assertArrayEquals(searchData2.getShape(), searchDataDto.getShape());
    assertArrayEquals(searchData2.getMaterial(), searchDataDto.getMaterial());
    assertArrayEquals(searchData2.getGeneralTolerances(), searchDataDto.getGeneralTolerances());
    assertArrayEquals(searchData2.getSurfaces(), searchDataDto.getSurfaces());
    assertArrayEquals(searchData2.getGdts(), searchDataDto.getGdts());
    assertArrayEquals(searchData2.getThreads(), searchDataDto.getThreads());
    assertArrayEquals(searchData2.getOuterDimensions(), searchDataDto.getOuterDimensions());
    assertArrayEquals(searchData2.getSearchVector(), searchDataDto.getSearchVector());
  }

  @Test
  void testConvertDtoToEntityForDrawing() {
    RuntimeDto runtimeDto = new RuntimeDto(
      1,
      1,
      "machine1",
      1f
    );

    SearchDataDto searchDataDto = new SearchDataDto(
      1,
      1,
      new float[]{},
      new String[]{},
      new String[]{},
      new String[]{},
      new String[]{},
      new String[]{},
      new float[]{},
      new float[]{},
      "",
      new String[]{},
      ""
    );

    FeedbackDto feedbackDto = new FeedbackDto(
      1,
      1,
      1,
      "",
      1
    );

    DrawingDto drawingDto = new DrawingDto(
      1,
      Base64.getEncoder().encodeToString(imageByteArray),
      Collections.singletonList(runtimeDto),
      searchDataDto,
      Collections.singletonList(feedbackDto)
    );

    Drawing drawing = dtoService.convertDtoToEntity(drawingDto);

    assertEquals(drawingDto.getDrawingId(), drawing.getDrawingId());
    assertArrayEquals(imageByteArray, drawing.getOriginalDrawing());
    // compare runtimes dto for drawings' runtimes
    assertFalse(drawing.getRuntimes().isEmpty());
    assertNotNull(drawing.getRuntimes().getFirst());
    Runtime runtime = drawing.getRuntimes().getFirst();
    assertEquals(runtimeDto.getRuntimeId(), runtime.getRuntimeId());
    assertEquals(drawingDto.getDrawingId(), runtime.getDrawing().getDrawingId());
    assertEquals(runtimeDto.getMachine(), runtime.getMachine());
    assertEquals(runtimeDto.getMachineRuntime(), runtime.getMachineRuntime());
    // compare searchdata dto to drawings' searchdata
    assertNotNull(drawing.getSearchData());
    SearchData searchData2 = drawing.getSearchData();
    assertEquals(searchDataDto.getSearchDataId(), searchData2.getSearchDataId());
    assertEquals(searchDataDto.getDrawingId(), searchData2.getDrawing().getDrawingId());
    assertArrayEquals(searchDataDto.getShape(), searchData2.getShape());
    assertArrayEquals(searchDataDto.getMaterial(), searchData2.getMaterial());
    assertArrayEquals(searchDataDto.getGeneralTolerances(), searchData2.getGeneralTolerances());
    assertArrayEquals(searchDataDto.getSurfaces(), searchData2.getSurfaces());
    assertArrayEquals(searchDataDto.getGdts(), searchData2.getGdts());
    assertArrayEquals(searchDataDto.getThreads(), searchData2.getThreads());
    assertArrayEquals(searchDataDto.getOuterDimensions(), searchData2.getOuterDimensions());
    assertArrayEquals(searchDataDto.getSearchVector(), searchData2.getSearchVector());
  }

  @Test
  void testConvertEntityToDtoForRuntime() {
    Drawing drawing = new Drawing();
    drawing.setDrawingId(1);
    drawing.setOriginalDrawing(imageByteArray);

    Runtime runtime = new Runtime();
    runtime.setRuntimeId(1);
    runtime.setDrawing(drawing);
    runtime.setMachine("machine1");
    runtime.setMachineRuntime(1f);

    drawing.setRuntimes(Collections.singletonList(runtime));

    RuntimeDto runtimeDto = dtoService.convertEntityToDto(runtime);

    assertEquals(runtime.getRuntimeId(), runtimeDto.getRuntimeId());
    assertEquals(runtime.getDrawing().getDrawingId(), runtimeDto.getDrawingId());
    assertEquals(runtime.getMachine(), runtimeDto.getMachine());
    assertEquals(runtime.getMachineRuntime(), runtimeDto.getMachineRuntime());
  }

  @Test
  void testConvertDtoToEntityForRuntime() {
    Drawing drawing = new Drawing();
    drawing.setDrawingId(1);
    drawing.setOriginalDrawing(imageByteArray);

    RuntimeDto runtimeDto = new RuntimeDto(
      1,
      1,
      "machine1",
      1f
    );

    Mockito.when(drawingRepository.findById(1)).thenReturn(Optional.of(drawing));
    Runtime runtime = dtoService.convertDtoToEntity(runtimeDto);

    assertEquals(runtimeDto.getRuntimeId(), runtime.getRuntimeId());
    assertEquals(drawing, runtime.getDrawing());
    assertEquals(runtimeDto.getMachine(), runtime.getMachine());
    assertEquals(runtimeDto.getMachineRuntime(), runtime.getMachineRuntime());

    Mockito.when(drawingRepository.findById(Mockito.anyInt())).thenReturn(Optional.empty());
    assertThrows(DrawingNotFoundException.class, () -> dtoService.convertDtoToEntity(runtimeDto));
  }

  @Test
  void testConvertEntityToDtoForSearchData() {
    SearchDataDto searchDataDto = dtoService.convertEntityToDto(searchData);

    assertEquals(searchData.getSearchDataId(), searchDataDto.getSearchDataId());
    assertEquals(searchData.getDrawing().getDrawingId(), searchDataDto.getDrawingId());
    assertArrayEquals(searchData.getShape(), searchDataDto.getShape());
    assertArrayEquals(searchData.getMaterial(), searchDataDto.getMaterial());
    assertArrayEquals(searchData.getGeneralTolerances(), searchDataDto.getGeneralTolerances());
    assertArrayEquals(searchData.getSurfaces(), searchDataDto.getSurfaces());
    assertArrayEquals(searchData.getGdts(), searchDataDto.getGdts());
    assertArrayEquals(searchData.getThreads(), searchDataDto.getThreads());
    assertArrayEquals(searchData.getOuterDimensions(), searchDataDto.getOuterDimensions());
    assertArrayEquals(searchData.getSearchVector(), searchDataDto.getSearchVector());
  }

  @Test
  void testConvertDtoToEntityForSearchData() {
    Drawing drawing = new Drawing();
    drawing.setDrawingId(1);
    drawing.setOriginalDrawing(imageByteArray);

    SearchDataDto searchDataDto = new SearchDataDto(
      1,
      1,
      new float[]{},
      new String[]{},
      new String[]{},
      new String[]{},
      new String[]{},
      new String[]{},
      new float[]{},
      new float[]{},
      "",
      new String[]{},
      ""
    );

    Mockito.when(drawingRepository.findById(1)).thenReturn(Optional.of(drawing));
    SearchData searchData2 = dtoService.convertDtoToEntity(searchDataDto);

    assertEquals(searchDataDto.getSearchDataId(), searchData2.getSearchDataId());
    assertEquals(drawing, searchData2.getDrawing());
    assertArrayEquals(searchDataDto.getShape(), searchData2.getShape());
    assertArrayEquals(searchDataDto.getMaterial(), searchData2.getMaterial());
    assertArrayEquals(searchDataDto.getGeneralTolerances(), searchData2.getGeneralTolerances());
    assertArrayEquals(searchDataDto.getSurfaces(), searchData2.getSurfaces());
    assertArrayEquals(searchDataDto.getGdts(), searchData2.getGdts());
    assertArrayEquals(searchDataDto.getThreads(), searchData2.getThreads());
    assertArrayEquals(searchDataDto.getOuterDimensions(), searchData2.getOuterDimensions());
    assertArrayEquals(searchDataDto.getSearchVector(), searchData2.getSearchVector());

    Mockito.when(drawingRepository.findById(Mockito.anyInt())).thenReturn(Optional.empty());
    assertThrows(DrawingNotFoundException.class, () -> dtoService.convertDtoToEntity(searchDataDto));
  }
}
