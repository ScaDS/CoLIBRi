package de.scadsai.infoextract.database.service;

import de.scadsai.infoextract.database.dto.DrawingDto;
import de.scadsai.infoextract.database.dto.HistoryDto;
import de.scadsai.infoextract.database.dto.RuntimeDto;
import de.scadsai.infoextract.database.dto.SearchDataDto;
import de.scadsai.infoextract.database.dto.FeedbackDto;
import de.scadsai.infoextract.database.entity.Drawing;
import de.scadsai.infoextract.database.entity.History;
import de.scadsai.infoextract.database.entity.Runtime;
import de.scadsai.infoextract.database.entity.SearchData;
import de.scadsai.infoextract.database.entity.Feedback;

public interface DtoService {

  /**
   * Converts a drawing entity to its dto
   * @param drawing Entity
   * @return Dto
   */
  DrawingDto convertEntityToDto(Drawing drawing);

  /**
   * Converts a drawing dto to its entity
   * @param drawingDto Dto
   * @return Entity
   */
  Drawing convertDtoToEntity(DrawingDto drawingDto);

  /**
   * Converts a runtime entity to its dto
   * @param runtime Entity
   * @return Dto
   */
  RuntimeDto convertEntityToDto(Runtime runtime);

  /**
   * Converts a runtime dto to its entity
   * @param runtimeDto Dto
   * @return Entity
   */
  Runtime convertDtoToEntity(RuntimeDto runtimeDto);

  /**
   * Converts a search data entity to its dto
   * @param searchData Entity
   * @return Dto
   */
  SearchDataDto convertEntityToDto(SearchData searchData);

  /**
   * Converts a search data dto to its entity
   * @param searchDataDto Dto
   * @return Entity
   */
  SearchData convertDtoToEntity(SearchDataDto searchDataDto);

  /**
   * Converts a history entity to its dto
   * @param history Entity
   * @return Dto
   */
  HistoryDto convertEntityToDto(History history);

  /**
   * Converts a history dto to its entity
   * @param historyDto Dto
   * @return Entity
   */
  History convertDtoToEntity(HistoryDto historyDto);

  /**
   * Converts a feedback entity to its dto
   * @param feedback Entity
   * @return Dto
   */
  FeedbackDto convertEntityToDto(Feedback feedback);

  /**
   * Converts a feedback dto to its entity
   * @param feedbackDto Dto
   * @return Entity
   */
  Feedback convertDtoToEntity(FeedbackDto feedbackDto);
}
