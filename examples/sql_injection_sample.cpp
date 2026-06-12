#include <iostream>
#include <string>
#include <sqlite3.h>

void executeQuery(sqlite3* db, const std::string& username) {
    // VULNERABILITY: SQL Injection via string concatenation
    std::string query = "SELECT * FROM users WHERE username = '" + username + "'";
    
    char* errMsg = 0;
    int rc = sqlite3_exec(db, query.c_str(), 0, 0, &errMsg);
    
    if (rc != SQLITE_OK) {
        std::cerr << "SQL error: " << errMsg << std::endl;
        sqlite3_free(errMsg);
    } else {
        std::cout << "Query executed successfully.\n";
    }
}

int main() {
    sqlite3* db;
    if (sqlite3_open("test.db", &db)) {
        return 1;
    }
    
    std::string userInput;
    std::cout << "Enter username to search: ";
    std::cin >> userInput;
    
    executeQuery(db, userInput);
    
    sqlite3_close(db);
    return 0;
}
