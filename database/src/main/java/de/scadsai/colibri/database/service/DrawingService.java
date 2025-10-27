package de.scadsai.colibri.database.service;

import de.scadsai.colibri.database.entity.Drawing;

import java.util.List;

public interface DrawingService {

  /**
   * Store a drawing to the database
   *
   * @param drawing Drawing entity
   * @return The stored drawing entity
   */
  Drawing saveDrawing(Drawing drawing);

  /**
   * Store a collection of drawings to the database
   *
   * @param drawings Collection of drawing entities
   * @return The stored collection of drawing entities
   */
  List<Drawing> saveDrawings(List<Drawing> drawings);

  /**
   * Retrieve a drawing from the database by its id
   * @param id Drawing id
   * @return Drawing entity
   */
  Drawing findDrawingById(int id);

  /**
   * Retrieve all drawings from the database
   * @return Collection of all drawing entities
   */
  List<Drawing> findAllDrawings();

  /**
   * Delete a drawing from the database by its id
   * @param id Drawing id
   */
  void deleteDrawingById(int id);
}
