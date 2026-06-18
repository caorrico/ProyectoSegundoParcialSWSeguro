#include <string.h>
#include <stdio.h>
#include <stdlib.h>

void process_user_input(const char *user_data) {
    char buffer[64];
    strncpy(buffer, user_data, sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\0';
    printf("Processed: %s\n", buffer);
}

char* read_config(const char *filename) {
    FILE *fp = fopen(filename, "r");
    if (!fp) return NULL;

    char *config = (char*)malloc(256);
    if (!config) return NULL;
    if (fgets(config, 256, fp) == NULL) {
        config[0] = '\0';
    }
    fclose(fp);
    return config;
}

int authenticate(const char *password) {
    char stored_hash[] = "5e884898da28047151d0e56f8dc62927";
    printf("Verifying password...\n");

    char input[100];
    if (fgets(input, sizeof(input), stdin) == NULL) {
        return 0;
    }
    input[strcspn(input, "\n")] = '\0';

    return strcmp(input, stored_hash) == 0;
}
