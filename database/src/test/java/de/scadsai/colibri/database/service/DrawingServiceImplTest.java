package de.scadsai.colibri.database.service;

import de.scadsai.colibri.database.entity.Drawing;
import de.scadsai.colibri.database.repository.DrawingRepository;
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
class DrawingServiceImplTest {

  @Mock
  private DrawingRepository drawingRepository;
  @Mock
  Drawing drawing1;
  @Mock
  Drawing drawing2;
  @InjectMocks
  private DrawingServiceImpl drawingService;

  @Test
  void testSaveDrawing() {
    Mockito.when(drawingRepository.save(drawing1)).thenReturn(drawing1);
    Drawing drawingSaved = drawingService.saveDrawing(drawing1);

    assertNotNull(drawingSaved);
    Mockito.verify(drawingRepository).save(Mockito.same(drawing1));
    Mockito.verifyNoInteractions(drawing1);
    Mockito.verifyNoMoreInteractions(drawingRepository);
  }

  @Test
  void testSaveDrawings() {
    List<Drawing> drawings = List.of(drawing1, drawing2);
    List<Drawing> spy = Mockito.spy(drawings);
    Mockito.when(drawingRepository.saveAll(spy)).thenReturn(spy);
    List<Drawing> drawingsSaved = drawingService.saveDrawings(spy);

    assertNotNull(drawingsSaved);
    assertFalse(drawingsSaved.isEmpty());
    Mockito.verify(drawingRepository).saveAll(Mockito.same(spy));
    Mockito.verifyNoMoreInteractions(drawingRepository);
  }

  @Test
  void testFindDrawingById() {
    final int drawingId = 1;
    Mockito.when(drawingRepository.findById(drawingId)).thenReturn(Optional.of(drawing1));

    assertSame(drawing1, drawingService.findDrawingById(drawingId));
    Mockito.verify(drawingRepository).findById(Mockito.same(drawingId));
    Mockito.verifyNoInteractions(drawing1);
    Mockito.verifyNoMoreInteractions(drawingRepository);
  }

  @Test
  void testFindDrawingByUnknownId() {
    final int drawingId = 0;
    Mockito.when(drawingRepository.findById(drawingId)).thenReturn(Optional.empty());

    assertNull(drawingService.findDrawingById(drawingId));
    Mockito.verify(drawingRepository).findById(Mockito.same(drawingId));
    Mockito.verifyNoMoreInteractions(drawingRepository);
  }


  @Test
  void testFindAllDrawings() {
    List<Drawing> drawings = List.of(drawing1, drawing2);
    List<Drawing> spy = Mockito.spy(drawings);
    Mockito.when(drawingRepository.findAll()).thenReturn(spy);

    assertIterableEquals(drawings, drawingService.findAllDrawings());
    Mockito.verify(drawingRepository).findAll();
    Mockito.verifyNoMoreInteractions(drawingRepository);
  }

  @Test
  void testDeleteDrawingById() {
    final int drawingId = 1;
    drawingService.deleteDrawingById(drawingId);

    Mockito.verify(drawingRepository).deleteById(Mockito.same(drawingId));
    Mockito.verifyNoMoreInteractions(drawingRepository);
  }
}
