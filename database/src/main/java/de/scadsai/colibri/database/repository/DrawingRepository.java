package de.scadsai.colibri.database.repository;

import de.scadsai.colibri.database.entity.Drawing;
import org.springframework.data.repository.CrudRepository;

public interface DrawingRepository extends CrudRepository<Drawing, Integer> {
}
