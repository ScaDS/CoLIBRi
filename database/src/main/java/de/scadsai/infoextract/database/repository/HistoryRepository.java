package de.scadsai.infoextract.database.repository;

import de.scadsai.infoextract.database.entity.History;
import org.springframework.data.repository.CrudRepository;

public interface HistoryRepository extends CrudRepository<History, Integer> {
}
