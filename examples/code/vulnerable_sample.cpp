// Vulnerable C++ function: Buffer overflow via strcpy
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

void process_user_input(const char *user_data) {
    char buffer[64];
    // VULNERABLE: No bounds checking, buffer overflow possible
    strcpy(buffer, user_data);
    printf("Processed: %s\n", buffer);
}

char* read_config(const char *filename) {
    FILE *fp = fopen(filename, "r");
    if (!fp) return NULL;

    // VULNERABLE: Fixed-size buffer, no length check
    char *config = (char*)malloc(128);
    fgets(config, 512, fp);  // reads up to 512 bytes into 128-byte buffer
    fclose(fp);
    return config;
}

int authenticate(const char *password) {
    char stored_hash[32];
    // VULNERABLE: Format string vulnerability
    printf(password);

    // VULNERABLE: Use of gets() - always unsafe
    char input[100];
    gets(input);

    return strcmp(input, stored_hash) == 0;
}
