package de.scadsai.infoextract.database.controller;

import de.scadsai.infoextract.database.exception.DrawingNotFoundException;
import de.scadsai.infoextract.database.dto.DrawingDto;
import de.scadsai.infoextract.database.entity.Drawing;
import de.scadsai.infoextract.database.service.DrawingService;
import de.scadsai.infoextract.database.service.DtoService;
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
class DrawingControllerTest {

  @Mock
  DrawingService drawingService;
  @Mock
  DtoService dtoService;
  @Mock
  Drawing drawing;
  @Mock
  Drawing drawingSaved;
  @Mock
  DrawingDto drawingDto;
  @InjectMocks
  DrawingController drawingController;

  @Test
  void testSaveDrawing() {
    Mockito.when(dtoService.convertDtoToEntity(drawingDto)).thenReturn(drawing);
    Mockito.when(dtoService.convertEntityToDto(drawingSaved)).thenReturn(drawingDto);
    Mockito.when(drawingService.saveDrawing(drawing)).thenReturn(drawingSaved);
    assertSame(drawingDto, drawingController.save(drawingDto));
  }

  @Test
  void testSaveDrawings() {
    Mockito.when(dtoService.convertDtoToEntity(drawingDto)).thenReturn(drawing);
    Mockito.when(dtoService.convertEntityToDto(drawingSaved)).thenReturn(drawingDto);
    Mockito.when(drawingService.saveDrawings(List.of(drawing, drawing))).thenReturn(List.of(drawingSaved, drawingSaved));
    assertArrayEquals(List.of(drawingDto, drawingDto).toArray(), drawingController.save(List.of(drawingDto, drawingDto)).toArray());
  }

  @Test
  void testDeleteDrawingById() {
    drawingController.deleteDrawingById(1);
    Mockito.verify(drawingService).deleteDrawingById(1);
  }

  @Test
  void testGetDrawingById() {
    Mockito.when(dtoService.convertEntityToDto(drawing)).thenReturn(drawingDto);
    Mockito.when(drawingService.findDrawingById(1)).thenReturn(drawing);
    assertSame(drawingDto, drawingController.getDrawingById(1));

    Mockito.when(drawingService.findDrawingById(not(eq(1)))).thenReturn(null);
    assertThrows(DrawingNotFoundException.class, () -> drawingController.getDrawingById(2));
  }

  @Test
  void testGetAllDrawings() {
    Mockito.when(dtoService.convertEntityToDto(drawing)).thenReturn(drawingDto);
    Mockito.when(drawingService.findAllDrawings()).thenReturn(List.of(drawing, drawing));
    assertArrayEquals(List.of(drawingDto, drawingDto).toArray(), drawingController.getAllDrawings().toArray());
  }
}
