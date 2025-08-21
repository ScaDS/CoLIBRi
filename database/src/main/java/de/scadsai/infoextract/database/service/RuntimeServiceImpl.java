package de.scadsai.infoextract.database.service;

import de.scadsai.infoextract.database.entity.Runtime;
import de.scadsai.infoextract.database.exception.DrawingNotFoundException;
import de.scadsai.infoextract.database.repository.RuntimeRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataAccessException;
import org.springframework.data.util.Streamable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class RuntimeServiceImpl implements RuntimeService {

  /**
   * The autowired repository for the runtime
   */
  private final RuntimeRepository runtimeRepository;

  @Autowired
  public RuntimeServiceImpl(RuntimeRepository runtimeRepository) {
    this.runtimeRepository = runtimeRepository;
  }

  @Override
  public Runtime saveRuntime(Runtime runtime) {
    try {
      return runtimeRepository.save(runtime);
    } catch (DataAccessException dae) {
      throw new DrawingNotFoundException(dae.getMessage(), dae);
    }
  }

  @Override
  public List<Runtime> saveRuntimes(List<Runtime> runtimes) {
    try {
      Iterable<Runtime> runtimeIterable = runtimeRepository.saveAll(runtimes);
      return Streamable.of(runtimeIterable).stream().toList();
    } catch (DataAccessException dae) {
      throw new DrawingNotFoundException(dae.getMessage(), dae);
    }
  }

  @Override
  public Runtime findRuntimeById(int id) {
    return runtimeRepository.findById(id).orElse(null);
  }

  @Override
  public List<Runtime> findRuntimesByDrawingId(int id) {
    Iterable<Runtime> runtimeIterable = runtimeRepository.findRuntimesByDrawing_DrawingId(id);
    return Streamable.of(runtimeIterable).stream().toList();
  }

  @Override
  public List<Runtime> findAllRuntimes() {
    Iterable<Runtime> runtimeIterable = runtimeRepository.findAll();
    return Streamable.of(runtimeIterable).stream().toList();
  }

  @Override
  public void deleteRuntimeById(int id) {
    runtimeRepository.deleteById(id);
  }

  @Override
  @Transactional
  public void deleteRuntimesByDrawingId(int id) {
    runtimeRepository.deleteRuntimesByDrawing_DrawingId(id);
  }
}
