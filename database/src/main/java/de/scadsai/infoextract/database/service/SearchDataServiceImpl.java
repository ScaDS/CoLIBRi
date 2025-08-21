package de.scadsai.infoextract.database.service;

import de.scadsai.infoextract.database.entity.SearchData;
import de.scadsai.infoextract.database.entity.Drawing;
import de.scadsai.infoextract.database.exception.DrawingNotFoundException;
import de.scadsai.infoextract.database.exception.SearchDataNotFoundException;
import de.scadsai.infoextract.database.repository.DrawingRepository;
import de.scadsai.infoextract.database.repository.SearchDataRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataAccessException;
import org.springframework.data.util.Streamable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class SearchDataServiceImpl implements SearchDataService {

  /**
   * The autowired repository for the search data
   */
  private final SearchDataRepository searchDataRepository;

  /**
   * The autowired repository for the drawing
   */
  private final DrawingRepository drawingRepository;

  @Autowired
  public SearchDataServiceImpl(SearchDataRepository searchDataRepository,
    DrawingRepository drawingRepository) {
    this.searchDataRepository = searchDataRepository;
    this.drawingRepository = drawingRepository;
  }

  @Override
  public SearchData saveSearchData(SearchData searchData) {
    try {
      return searchDataRepository.save(searchData);
    } catch (DataAccessException dae) {
      throw new DrawingNotFoundException(dae.getMessage(), dae);
    }
  }

  @Override
  public List<SearchData> saveSearchDataList(List<SearchData> searchDataList) {
    try {
      Iterable<SearchData> searchDataIterable = searchDataRepository.saveAll(searchDataList);
      return Streamable.of(searchDataIterable).stream().toList();
    } catch (DataAccessException dae) {
      throw new DrawingNotFoundException(dae.getMessage(), dae);
    }
  }

  @Override
  public SearchData findSearchDataById(int id) {
    return searchDataRepository.findById(id).orElse(null);
  }

  @Override
  public SearchData findSearchDataByDrawingId(int id) {
    return searchDataRepository.findSearchDataByDrawing_DrawingId(id).orElse(null);
  }

  @Override
  public List<SearchData> findAllSearchData() {
    Iterable<SearchData> searchDataIterable = searchDataRepository.findAll();
    return Streamable.of(searchDataIterable).stream().toList();
  }

  @Override
  @Transactional
  public void deleteSearchDataById(int id) {
    SearchData searchData = searchDataRepository.findById(id).orElse(null);
    if (searchData != null) {
      Drawing drawing = searchData.getDrawing();
      if (drawing != null) {
        drawing.setSearchData(null);
        drawingRepository.save(drawing);
      }
      searchDataRepository.deleteById(id);
    } else {
      throw new SearchDataNotFoundException(id);
    }
  }

  @Override
  @Transactional
  public void deleteSearchDataByDrawingId(int id) {
    Drawing drawing = drawingRepository.findById(id).orElse(null);
    if (drawing != null) {
      SearchData searchData = drawing.getSearchData();
      if (searchData != null) {
        drawing.setSearchData(null);
        drawingRepository.save(drawing);
        searchDataRepository.deleteSearchDataByDrawing_DrawingId(id);
      }
    } else {
      throw new DrawingNotFoundException(id);
    }
  }
}
