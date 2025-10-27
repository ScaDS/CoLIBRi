package de.scadsai.colibri.database.service;

import de.scadsai.colibri.database.dto.DrawingDto;
import de.scadsai.colibri.database.dto.HistoryDto;
import de.scadsai.colibri.database.dto.RuntimeDto;
import de.scadsai.colibri.database.dto.SearchDataDto;
import de.scadsai.colibri.database.dto.FeedbackDto;
import de.scadsai.colibri.database.entity.Drawing;
import de.scadsai.colibri.database.entity.History;
import de.scadsai.colibri.database.entity.Runtime;
import de.scadsai.colibri.database.entity.SearchData;
import de.scadsai.colibri.database.entity.Feedback;
import de.scadsai.colibri.database.repository.DrawingRepository;
import de.scadsai.colibri.database.exception.DrawingNotFoundException;
import de.scadsai.colibri.database.repository.HistoryRepository;
import de.scadsai.colibri.database.exception.HistoryNotFoundException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Base64;
import java.util.List;

@Service
public class DtoServiceImpl implements DtoService {

  /**
   * The autowired repository for the drawings
   */
  private final DrawingRepository drawingRepository;

  /**
   * The autowired repository for the histories
   */
  private final HistoryRepository historyRepository;

  @Autowired
  public DtoServiceImpl(DrawingRepository drawingRepository, HistoryRepository historyRepository) {
    this.drawingRepository = drawingRepository;
    this.historyRepository = historyRepository;
  }

  @Override
  public DrawingDto convertEntityToDto(Drawing drawing) {
    SearchDataDto searchDataDto = drawing.getSearchData() == null ? null :
      new SearchDataDto(
        drawing.getSearchData().getSearchDataId(),
        drawing.getSearchData().getDrawing().getDrawingId(),
        drawing.getSearchData().getShape(),
        drawing.getSearchData().getMaterial(),
        drawing.getSearchData().getGeneralTolerances(),
        drawing.getSearchData().getSurfaces(),
        drawing.getSearchData().getGdts(),
        drawing.getSearchData().getThreads(),
        drawing.getSearchData().getOuterDimensions(),
        drawing.getSearchData().getSearchVector(),
        drawing.getSearchData().getPartNumber(),
        drawing.getSearchData().getOcrText(),
        drawing.getSearchData().getRuntimeText(),
        drawing.getSearchData().getLlmText(),
        drawing.getSearchData().getLlmVector()
      );

    List<RuntimeDto> runtimeDtos = drawing.getRuntimes() == null ? null :
      drawing.getRuntimes().stream().map(runtime ->
        new RuntimeDto(
          runtime.getRuntimeId(),
          runtime.getDrawing().getDrawingId(),
          runtime.getMachine(),
          runtime.getMachineRuntime()
        )
      ).toList();

    List<FeedbackDto> feedbackDtos = drawing.getFeedbacks() == null ? null :
      drawing.getFeedbacks().stream().map(feedback ->
        new FeedbackDto(
          feedback.getFeedbackId(),
          feedback.getHistory().getHistoryId(),
          feedback.getDrawing().getDrawingId(),
          feedback.getFeedbackDesc(),
          feedback.getFeedbackValue()
        )
      ).toList();

    return new DrawingDto(
      drawing.getDrawingId(),
      Base64.getEncoder().encodeToString(drawing.getOriginalDrawing()),
      runtimeDtos,
      searchDataDto,
      feedbackDtos
    );
  }

  @Override
  public Drawing convertDtoToEntity(DrawingDto drawingDto) {
    SearchData searchData = drawingDto.getSearchData() == null ? null :
      new SearchData(
        drawingDto.getSearchData().getSearchDataId(),
        null, // Note: The drawing will be set later in the Drawing entity
        drawingDto.getSearchData().getShape(),
        drawingDto.getSearchData().getMaterial(),
        drawingDto.getSearchData().getGeneralTolerances(),
        drawingDto.getSearchData().getSurfaces(),
        drawingDto.getSearchData().getGdts(),
        drawingDto.getSearchData().getThreads(),
        drawingDto.getSearchData().getOuterDimensions(),
        drawingDto.getSearchData().getSearchVector(),
        drawingDto.getSearchData().getPartNumber(),
        drawingDto.getSearchData().getOcrText(),
        drawingDto.getSearchData().getRuntimeText(),
        drawingDto.getSearchData().getLlmText(),
        drawingDto.getSearchData().getLlmVector()
      );

    List<Runtime> runtimes = drawingDto.getRuntimes() == null ? null :
      drawingDto.getRuntimes().stream().map(runtimeDto -> {
        Runtime runtime = new Runtime();
        runtime.setRuntimeId(runtimeDto.getRuntimeId());
        // Note: The drawing will be set later in the Drawing entity
        runtime.setMachine(runtimeDto.getMachine());
        runtime.setMachineRuntime(runtimeDto.getMachineRuntime());
        return runtime;
      }).toList();

    List<Feedback> feedbacks = drawingDto.getFeedbacks() == null ? null :
      drawingDto.getFeedbacks().stream().map(feedbackDto -> {
        Feedback feedback = new Feedback();
        feedback.setFeedbackId(feedback.getFeedbackId());
        feedback.setHistory(feedback.getHistory());
        // Note: The drawing will be set later in the Drawing entity
        feedback.setFeedbackDesc(feedback.getFeedbackDesc());
        feedback.setFeedbackValue(feedback.getFeedbackValue());
        return feedback;
      }).toList();

    Drawing drawing = new Drawing(
      drawingDto.getDrawingId(),
      Base64.getDecoder().decode(drawingDto.getOriginalDrawing()),
      runtimes,
      searchData,
      feedbacks
    );
    if (drawing.getRuntimes() != null) {
      drawing.getRuntimes().forEach(runtime -> runtime.setDrawing(drawing));
    }
    if (drawing.getSearchData() != null) {
      drawing.getSearchData().setDrawing(drawing);
    }
    if (drawing.getFeedbacks() != null) {
      drawing.getFeedbacks().forEach(feedback -> feedback.setDrawing(drawing));
    }

    return drawing;
  }

  @Override
  public RuntimeDto convertEntityToDto(Runtime runtime) {
    return new RuntimeDto(
      runtime.getRuntimeId(),
      runtime.getDrawing().getDrawingId(),
      runtime.getMachine(),
      runtime.getMachineRuntime()
    );
  }

  @Override
  public Runtime convertDtoToEntity(RuntimeDto runtimeDto) {
    int drawingId = runtimeDto.getDrawingId();
    Drawing drawing = drawingRepository.findById(drawingId).orElseThrow(
        () -> new DrawingNotFoundException(drawingId)
    );

    return new Runtime(
      runtimeDto.getRuntimeId(),
      drawing,
      runtimeDto.getMachine(),
      runtimeDto.getMachineRuntime()
    );
  }

  @Override
  public SearchDataDto convertEntityToDto(SearchData searchData) {
    return new SearchDataDto(
      searchData.getSearchDataId(),
      searchData.getDrawing().getDrawingId(),
      searchData.getShape(),
      searchData.getMaterial(),
      searchData.getGeneralTolerances(),
      searchData.getSurfaces(),
      searchData.getGdts(),
      searchData.getThreads(),
      searchData.getOuterDimensions(),
      searchData.getSearchVector(),
      searchData.getPartNumber(),
      searchData.getOcrText(),
      searchData.getRuntimeText(),
      searchData.getLlmText(),
      searchData.getLlmVector()
    );
  }

  @Override
  public SearchData convertDtoToEntity(SearchDataDto searchDataDto) {
    int drawingId = searchDataDto.getDrawingId();
    Drawing drawing = drawingRepository.findById(drawingId).orElseThrow(
      () -> new DrawingNotFoundException(drawingId)
    );

    return new SearchData(
      searchDataDto.getSearchDataId(),
      drawing,
      searchDataDto.getShape(),
      searchDataDto.getMaterial(),
      searchDataDto.getGeneralTolerances(),
      searchDataDto.getSurfaces(),
      searchDataDto.getGdts(),
      searchDataDto.getThreads(),
      searchDataDto.getOuterDimensions(),
      searchDataDto.getSearchVector(),
      searchDataDto.getPartNumber(),
      searchDataDto.getOcrText(),
      searchDataDto.getRuntimeText(),
      searchDataDto.getLlmText(),
      searchDataDto.getLlmVector()
    );
  }

  @Override
  public HistoryDto convertEntityToDto(History history) {
    List<FeedbackDto> feedbackDtos = history.getFeedbacks() == null ? null :
      history.getFeedbacks().stream().map(feedback ->
        new FeedbackDto(
          feedback.getFeedbackId(),
          feedback.getHistory().getHistoryId(),
          feedback.getDrawing().getDrawingId(),
          feedback.getFeedbackDesc(),
          feedback.getFeedbackValue()
        )
      ).toList();

    return new HistoryDto(
      history.getHistoryId(),
      Base64.getEncoder().encodeToString(history.getQueryDrawing()),
      history.getQueryPath(),
      history.getTimestamp(),
      feedbackDtos
    );
  }

  @Override
  public History convertDtoToEntity(HistoryDto historyDto) {
    List<Feedback> feedbacks = historyDto.getFeedbacks() == null ? null :
      historyDto.getFeedbacks().stream().map(feedbackDto -> {
        Feedback feedback = new Feedback();
        feedback.setFeedbackId(feedback.getFeedbackId());
        // Note: The history will be set later in the History entity
        feedback.setDrawing(feedback.getDrawing());
        feedback.setFeedbackDesc(feedback.getFeedbackDesc());
        feedback.setFeedbackValue(feedback.getFeedbackValue());
        return feedback;
      }).toList();

    History history = new History(
      historyDto.getHistoryId(),
      Base64.getDecoder().decode(historyDto.getQueryDrawing()),
      historyDto.getQueryPath(),
      historyDto.getTimestamp(),
      feedbacks
    );
    if (history.getFeedbacks() != null) {
      history.getFeedbacks().forEach(feedback -> feedback.setHistory(history));
    }

    return history;
  }

  @Override
  public FeedbackDto convertEntityToDto(Feedback feedback) {
    return new FeedbackDto(
      feedback.getFeedbackId(),
      feedback.getHistory().getHistoryId(),
      feedback.getDrawing().getDrawingId(),
      feedback.getFeedbackDesc(),
      feedback.getFeedbackValue()
    );
  }

  @Override
  public Feedback convertDtoToEntity(FeedbackDto feedbackDto) {
    int drawingId = feedbackDto.getDrawingId();
    Drawing drawing = drawingRepository.findById(drawingId).orElseThrow(
      () -> new DrawingNotFoundException(drawingId)
    );
    int historyId = feedbackDto.getHistoryId();
    History history = historyRepository.findById(historyId).orElseThrow(
      () -> new HistoryNotFoundException(historyId)
    );

    return new Feedback(
      feedbackDto.getFeedbackId(),
      history,
      drawing,
      feedbackDto.getFeedbackDesc(),
      feedbackDto.getFeedbackValue()
    );
  }
}
