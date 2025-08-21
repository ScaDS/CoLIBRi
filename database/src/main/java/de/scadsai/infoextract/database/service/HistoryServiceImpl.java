package de.scadsai.infoextract.database.service;

import de.scadsai.infoextract.database.entity.History;
import de.scadsai.infoextract.database.repository.HistoryRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.util.Streamable;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class HistoryServiceImpl implements HistoryService {

  /**
   * The autowired repository for the history
   */
  private final HistoryRepository historyRepository;

  @Autowired
  public HistoryServiceImpl(HistoryRepository historyRepository) {
    this.historyRepository = historyRepository;
  }

  @Override
  public History saveHistory(History history) {
    return historyRepository.save(history);
  }

  @Override
  public List<History> saveHistories(List<History> histories) {
    Iterable<History> historyIterable = historyRepository.saveAll(histories);
    return Streamable.of(historyIterable).stream().toList();
  }

  @Override
  public History findHistoryById(int id) {
    return historyRepository.findById(id).orElse(null);
  }

  @Override
  public List<History> findAllHistories() {
    Iterable<History> historyIterable = historyRepository.findAll();
    return Streamable.of(historyIterable).stream().toList();
  }

  @Override
  public void deleteHistoryById(int id) {
    historyRepository.deleteById(id);
  }
}
