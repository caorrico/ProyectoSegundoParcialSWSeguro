#include <stdio.h>
#include <string.h>

void logMessage(char *userInput) {
    // VULNERABILITY: Format String Vulnerability
    // If the user inputs "%x %x %x %n", they can read/write memory addresses directly!
    // The correct way would be: printf("%s", userInput);
    printf(userInput);
    printf("\n");
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <message>\n", argv[0]);
        return 1;
    }
    
    // Pass user-controlled input directly to a vulnerable function
    logMessage(argv[1]);
    
    return 0;
}
