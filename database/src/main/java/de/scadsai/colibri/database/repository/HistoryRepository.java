package de.scadsai.colibri.database.repository;

import de.scadsai.colibri.database.entity.History;
import org.springframework.data.repository.CrudRepository;

public interface HistoryRepository extends CrudRepository<History, Integer> {
}
