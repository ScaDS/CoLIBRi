package de.scadsai.infoextract.database.controller;

import de.scadsai.infoextract.database.exception.RuntimeNotFoundException;
import de.scadsai.infoextract.database.dto.RuntimeDto;
import de.scadsai.infoextract.database.entity.Runtime;
import de.scadsai.infoextract.database.exception.RuntimesNotFoundForDrawingException;
import de.scadsai.infoextract.database.service.RuntimeService;
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
class RuntimeControllerTest {

  @Mock
  RuntimeService runtimeService;
  @Mock
  DtoService dtoService;
  @Mock
  Runtime runtime;
  @Mock
  Runtime runtimeSaved;
  @Mock
  RuntimeDto runtimeDto;
  @InjectMocks
  RuntimeController runtimeController;

  @Test
  void testSaveRuntime() {
    Mockito.when(dtoService.convertDtoToEntity(runtimeDto)).thenReturn(runtime);
    Mockito.when(dtoService.convertEntityToDto(runtimeSaved)).thenReturn(runtimeDto);
    Mockito.when(runtimeService.saveRuntime(runtime)).thenReturn(runtimeSaved);
    assertSame(runtimeDto, runtimeController.save(runtimeDto));
  }

  @Test
  void testSaveRuntimes() {
    Mockito.when(dtoService.convertDtoToEntity(runtimeDto)).thenReturn(runtime);
    Mockito.when(dtoService.convertEntityToDto(runtimeSaved)).thenReturn(runtimeDto);
    Mockito.when(runtimeService.saveRuntimes(List.of(runtime, runtime))).thenReturn(List.of(runtimeSaved, runtimeSaved));
    assertArrayEquals(List.of(runtimeDto, runtimeDto).toArray(), runtimeController.save(List.of(runtimeDto, runtimeDto)).toArray());
  }

  @Test
  void testDeleteRuntimeById() {
    runtimeController.deleteRuntimeById(1);
    Mockito.verify(runtimeService).deleteRuntimeById(1);
  }

  @Test
  void testDeleteRuntimesByDrawingId() {
    runtimeController.deleteRuntimesByDrawingId(1);
    Mockito.verify(runtimeService).deleteRuntimesByDrawingId(1);
  }

  @Test
  void testGetRuntimeById() {
    Mockito.when(dtoService.convertEntityToDto(runtime)).thenReturn(runtimeDto);
    Mockito.when(runtimeService.findRuntimeById(1)).thenReturn(runtime);
    assertSame(runtimeDto, runtimeController.getRuntimeById(1));

    Mockito.when(runtimeService.findRuntimeById(not(eq(1)))).thenReturn(null);
    assertThrows(RuntimeNotFoundException.class, () -> runtimeController.getRuntimeById(2));
  }

  @Test
  void testGetRuntimesByDrawingId() {
    Mockito.when(dtoService.convertEntityToDto(runtime)).thenReturn(runtimeDto);
    Mockito.when(runtimeService.findRuntimesByDrawingId(1)).thenReturn(List.of(runtime, runtime));
    assertArrayEquals(List.of(runtimeDto, runtimeDto).toArray(), runtimeController.getRuntimesByDrawingId(1).toArray());

    Mockito.when(runtimeService.findRuntimesByDrawingId(not(eq(1)))).thenReturn(null);
    assertThrows(RuntimesNotFoundForDrawingException.class, () -> runtimeController.getRuntimesByDrawingId(2));
  }

  @Test
  void testGetAllRuntimes() {
    Mockito.when(dtoService.convertEntityToDto(runtime)).thenReturn(runtimeDto);
    Mockito.when(runtimeService.findAllRuntimes()).thenReturn(List.of(runtime, runtime));
    assertArrayEquals(List.of(runtimeDto, runtimeDto).toArray(), runtimeController.getAllRuntimes().toArray());
  }
}
