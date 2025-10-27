package de.scadsai.colibri.database.service;

import de.scadsai.colibri.database.entity.Runtime;
import de.scadsai.colibri.database.repository.RuntimeRepository;
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
class RuntimeServiceImplTest {

  @Mock
  private RuntimeRepository runtimeRepository;
  @Mock
  Runtime runtime1;
  @Mock
  Runtime runtime2;
  @InjectMocks
  private RuntimeServiceImpl runtimeService;

  @Test
  void testSaveRuntime() {
    Mockito.when(runtimeRepository.save(runtime1)).thenReturn(runtime1);
    Runtime runtimeSaved = runtimeService.saveRuntime(runtime1);

    assertNotNull(runtimeSaved);
    Mockito.verify(runtimeRepository).save(Mockito.same(runtime1));
    Mockito.verifyNoInteractions(runtime1);
    Mockito.verifyNoMoreInteractions(runtimeRepository);
  }

  @Test
  void testSaveRuntimes() {
    List<Runtime> runtimes = List.of(runtime1, runtime2);
    List<Runtime> spy = Mockito.spy(runtimes);
    Mockito.when(runtimeRepository.saveAll(spy)).thenReturn(spy);
    List<Runtime> runtimesSaved = runtimeService.saveRuntimes(spy);

    assertNotNull(runtimesSaved);
    assertFalse(runtimesSaved.isEmpty());
    Mockito.verify(runtimeRepository).saveAll(Mockito.same(spy));
    Mockito.verifyNoMoreInteractions(runtimeRepository);
  }

  @Test
  void testFindRuntimeById() {
    final int runtimeId = 1;
    Mockito.when(runtimeRepository.findById(runtimeId)).thenReturn(Optional.of(runtime1));

    assertSame(runtime1, runtimeService.findRuntimeById(runtimeId));
    Mockito.verify(runtimeRepository).findById(Mockito.same(runtimeId));
    Mockito.verifyNoInteractions(runtime1);
    Mockito.verifyNoMoreInteractions(runtimeRepository);
  }

  @Test
  void testFindRuntimeByUnknownId() {
    final int runtimeId = 0;
    Mockito.when(runtimeRepository.findById(runtimeId)).thenReturn(Optional.empty());

    assertNull(runtimeService.findRuntimeById(runtimeId));
    Mockito.verify(runtimeRepository).findById(Mockito.same(runtimeId));
    Mockito.verifyNoMoreInteractions(runtimeRepository);
  }

  @Test
  void testFindRuntimeByDrawingId() {
    final int drawingId = 1;
    List<Runtime> runtimes = List.of(runtime1);
    List<Runtime> spy = Mockito.spy(runtimes);
    Mockito.when(runtimeRepository.findRuntimesByDrawing_DrawingId(drawingId)).thenReturn(spy);

    assertIterableEquals(List.of(runtime1), runtimeService.findRuntimesByDrawingId(drawingId));
    Mockito.verify(runtimeRepository).findRuntimesByDrawing_DrawingId(drawingId);
    Mockito.verifyNoMoreInteractions(runtimeRepository);
  }

  @Test
  void testFindAllRuntimes() {
    List<Runtime> runtimes = List.of(runtime1, runtime2);
    List<Runtime> spy = Mockito.spy(runtimes);
    Mockito.when(runtimeRepository.findAll()).thenReturn(spy);

    assertIterableEquals(runtimes, runtimeService.findAllRuntimes());
    Mockito.verify(runtimeRepository).findAll();
    Mockito.verifyNoMoreInteractions(runtimeRepository);
  }

  @Test
  void testDeleteRuntimeById() {
    final int runtimeId = 1;
    runtimeService.deleteRuntimeById(runtimeId);

    Mockito.verify(runtimeRepository).deleteById(Mockito.same(runtimeId));
    Mockito.verifyNoMoreInteractions(runtimeRepository);
  }

  @Test
  void testDeleteRuntimeByDrawingId() {
    final int drawingId = 1;
    runtimeService.deleteRuntimesByDrawingId(drawingId);

    Mockito.verify(runtimeRepository).deleteRuntimesByDrawing_DrawingId(Mockito.same(drawingId));
    Mockito.verifyNoMoreInteractions(runtimeRepository);
  }
}
