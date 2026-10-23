package com.cleanops.security;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
public class FirebaseAuthenticationFilterTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @DisplayName("SEC-01: Requests without Authorization header must return 401 Unauthorized")
    public void shouldRejectRequestWithoutToken() throws Exception {
        mockMvc.perform(get("/api/v1/users/me"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.status").value(401))
                .andExpect(jsonPath("$.error").value("Unauthorized"))
                .andExpect(jsonPath("$.message").value("Missing or invalid token"));
    }

    @Test
    @DisplayName("SEC-02: Requests with forged/invalid Bearer token must return 401 Unauthorized")
    public void shouldRejectRequestWithForgedToken() throws Exception {
        mockMvc.perform(get("/api/v1/users/me")
                .header("Authorization", "Bearer fake_forged_token_xyz"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.status").value(401))
                .andExpect(jsonPath("$.error").value("Unauthorized"))
                .andExpect(jsonPath("$.message").value("Invalid or expired token"));
    }
}
