package de.scadsai.colibri.database.controller;

import de.scadsai.colibri.database.DatabaseApplication;
import org.junit.jupiter.api.TestInstance;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.test.web.servlet.ResultMatcher;
import org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;

@ExtendWith(SpringExtension.class)
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.MOCK, classes = DatabaseApplication.class)
@AutoConfigureMockMvc
@TestPropertySource(locations = "classpath:application.properties")
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
public abstract class SpringIntegrationTest {

  protected static MockHttpServletRequestBuilder corsGet(String url, Object... args) {
    return cors(get(url, args));
  }

  protected static MockHttpServletRequestBuilder corsPost(String url, Object... args) {
    return cors(post(url, args));
  }

  protected static MockHttpServletRequestBuilder corsDelete(String url, Object... args) {
    return cors(delete(url, args));
  }

  protected static ResultMatcher allowOrigin() {
    return header().string("Access-Control-Allow-Origin", "*");
  }

  private static MockHttpServletRequestBuilder cors(MockHttpServletRequestBuilder mockHttpServletRequestBuilder) {
    return mockHttpServletRequestBuilder.header("Origin", "someotherdomain.local");
  }
}
