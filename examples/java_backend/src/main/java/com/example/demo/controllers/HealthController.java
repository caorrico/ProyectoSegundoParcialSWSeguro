package com.example.demo.controllers;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/health")
public class HealthController {

    @GetMapping("/status")
    public String getStatus() {
        // SAFE: No user input used, no database access, perfectly safe endpoint
        return "{\"status\": \"UP\", \"uptime\": \"99.99%\"}";
    }
    
    @GetMapping("/ping")
    public String ping() {
        return "pong";
    }
}
