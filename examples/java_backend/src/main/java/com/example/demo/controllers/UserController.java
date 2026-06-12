package com.example.demo.controllers;

import org.springframework.web.bind.annotation.*;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private Connection getConnection() throws SQLException {
        return DriverManager.getConnection("jdbc:mysql://localhost:3306/mydb", "root", "root");
    }

    // Vulnerable endpoint: SQL Injection
    @GetMapping("/search")
    public List<String> searchUsers(@RequestParam("name") String name) {
        List<String> users = new ArrayList<>();
        try (Connection conn = getConnection()) {
            Statement stmt = conn.createStatement();
            // VULNERABLE: Direct string concatenation of user input
            String query = "SELECT username FROM users WHERE username = '" + name + "'";
            ResultSet rs = stmt.executeQuery(query);
            while (rs.next()) {
                users.add(rs.getString("username"));
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return users;
    }
}
