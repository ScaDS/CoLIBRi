package de.scadsai.infoextract.database.repository;

import de.scadsai.infoextract.database.entity.Drawing;
import org.springframework.data.repository.CrudRepository;

public interface DrawingRepository extends CrudRepository<Drawing, Integer> {
}
