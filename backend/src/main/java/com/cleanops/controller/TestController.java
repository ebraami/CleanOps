package com.cleanops.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
public class TestController {

    @GetMapping("/users/me")
    public String getMe() {
        return "{\"status\": 200, \"message\": \"Token verified successfully!\"}";
    }
}
