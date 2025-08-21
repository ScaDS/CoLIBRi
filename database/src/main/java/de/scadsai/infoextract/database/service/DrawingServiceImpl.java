package de.scadsai.infoextract.database.service;

import de.scadsai.infoextract.database.entity.Drawing;
import de.scadsai.infoextract.database.repository.DrawingRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.util.Streamable;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class DrawingServiceImpl implements DrawingService {

  /**
   * The autowired repository for the drawings
   */
  private final DrawingRepository drawingRepository;

  @Autowired
  public DrawingServiceImpl(DrawingRepository drawingRepository) {
    this.drawingRepository = drawingRepository;
  }

  @Override
  public Drawing saveDrawing(Drawing drawing) {
    return drawingRepository.save(drawing);
  }

  @Override
  public List<Drawing> saveDrawings(List<Drawing> drawings) {
    Iterable<Drawing> drawingIterable = drawingRepository.saveAll(drawings);
    return Streamable.of(drawingIterable).stream().toList();
  }

  @Override
  public Drawing findDrawingById(int id) {
    return drawingRepository.findById(id).orElse(null);
  }

  @Override
  public List<Drawing> findAllDrawings() {
    Iterable<Drawing> drawingIterable = drawingRepository.findAll();
    return Streamable.of(drawingIterable).stream().toList();
  }

  @Override
  public void deleteDrawingById(int id) {
    drawingRepository.deleteById(id);
  }
}
