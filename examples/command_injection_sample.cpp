#include <iostream>
#include <string>
#include <cstdlib>

int main() {
    std::string ipAddress;
    std::cout << "Enter IP address to ping: ";
    std::cin >> ipAddress;

    // VULNERABILITY: Command Injection
    // If the user inputs "8.8.8.8; rm -rf /", it will execute the malicious command.
    std::string command = "ping -c 4 " + ipAddress;
    
    std::cout << "Executing: " << command << std::endl;
    int result = system(command.c_str());
    
    if (result == 0) {
        std::cout << "Host is reachable.\n";
    } else {
        std::cout << "Host is unreachable.\n";
    }

    return 0;
}
