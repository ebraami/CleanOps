package com.cleanops.controller;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
public class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @DisplayName("FLUTTER-01: Create profile returns 201 with strictly hardcoded CITIZEN role")
    public void testCreateProfileSuccess() throws Exception {
        String testToken = "dev-user:flutter_test_uid_1";
        String payload = """
            {
                "name": "Flutter Citizen",
                "email": "flutter1@cleanops.org",
                "role": "ADMIN"
            }
            """;

        mockMvc.perform(post("/api/v1/users/me")
                .header("Authorization", "Bearer " + testToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(payload))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").isNotEmpty())
                .andExpect(jsonPath("$.firebaseUid").value("flutter_test_uid_1"))
                .andExpect(jsonPath("$.name").value("Flutter Citizen"))
                .andExpect(jsonPath("$.email").value("flutter1@cleanops.org"))
                .andExpect(jsonPath("$.role").value("CITIZEN")); // Client-supplied "ADMIN" must be ignored!
    }

    @Test
    @DisplayName("FLUTTER-02: Get my profile returns 200 for existing user")
    public void testGetProfileSuccess() throws Exception {
        String testToken = "dev-user:flutter_test_uid_2";
        String payload = """
            {
                "name": "Jane Flutter",
                "email": "jane.flutter@cleanops.org"
            }
            """;

        // 1. Create profile
        mockMvc.perform(post("/api/v1/users/me")
                .header("Authorization", "Bearer " + testToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(payload))
                .andExpect(status().isCreated());

        // 2. Retrieve profile
        mockMvc.perform(get("/api/v1/users/me")
                .header("Authorization", "Bearer " + testToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Jane Flutter"))
                .andExpect(jsonPath("$.email").value("jane.flutter@cleanops.org"))
                .andExpect(jsonPath("$.role").value("CITIZEN"));
    }

    @Test
    @DisplayName("FLUTTER-03: Duplicate registration returns 409 Conflict")
    public void testDuplicateRegistration() throws Exception {
        String testToken = "dev-user:flutter_test_uid_3";
        String payload = """
            {
                "name": "Duplicate User",
                "email": "dup@cleanops.org"
            }
            """;

        // First creation -> 201
        mockMvc.perform(post("/api/v1/users/me")
                .header("Authorization", "Bearer " + testToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(payload))
                .andExpect(status().isCreated());

        // Second creation with same uid -> 409
        mockMvc.perform(post("/api/v1/users/me")
                .header("Authorization", "Bearer " + testToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(payload))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.message").value("Profile already exists for this account"));
    }

    @Test
    @DisplayName("FLUTTER-04: Invalid body validation returns 400 Bad Request")
    public void testInvalidBody() throws Exception {
        String testToken = "dev-user:flutter_test_uid_4";
        String invalidPayload = """
            {
                "name": "",
                "email": "not-an-email"
            }
            """;

        mockMvc.perform(post("/api/v1/users/me")
                .header("Authorization", "Bearer " + testToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(invalidPayload))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.message").isNotEmpty());
    }

    @Test
    @DisplayName("FLUTTER-05: Non-existent profile returns 404 Not Found")
    public void testProfileNotFound() throws Exception {
        String nonExistentToken = "dev-user:unknown_uid_999";

        mockMvc.perform(get("/api/v1/users/me")
                .header("Authorization", "Bearer " + nonExistentToken))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404));
    }
}
