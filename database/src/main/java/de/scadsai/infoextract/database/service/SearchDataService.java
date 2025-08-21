package de.scadsai.infoextract.database.service;

import de.scadsai.infoextract.database.entity.SearchData;

import java.util.List;

public interface SearchDataService {

  /**
   * Store a search data entity to the database
   *
   * @param searchData SearchData entity
   * @return The stored search data entity
   */
  SearchData saveSearchData(SearchData searchData);

  /**
   * Store a collection of search data entities to the database
   *
   * @param searchDataList Collection of search data entities
   * @return The stored collection of search data entities
   */
  List<SearchData> saveSearchDataList(List<SearchData> searchDataList);

  /**
   * Retrieve a search data entity from the database by its id
   * @param id SearchData id
   * @return SearchData entity
   */
  SearchData findSearchDataById(int id);

  /**
   * Retrieve a search data entity from the database by its referencing drawing id
   * @param id Drawing id
   * @return SearchData entity
   */
  SearchData findSearchDataByDrawingId(int id);

  /**
   * Retrieve all search data entities from the database
   * @return Collection of all search data entities
   */
  List<SearchData> findAllSearchData();

  /**
   * Delete a search data entity from the database by its id
   * @param id SearchData id
   */
  void deleteSearchDataById(int id);

  /**
   * Delete all search data entities from the database by its referencing drawing id
   * @param id Drawing id
   */
  void deleteSearchDataByDrawingId(int id);
}
