"""
OWASP Top 10:2025 Specialized Dataset Generator

Generates realistic C/C++ code samples for each OWASP Top 10:2025 category:
  A01 - Broken Access Control
  A02 - Security Misconfiguration
  A03 - Software Supply Chain Failures
  A04 - Cryptographic Failures
  A05 - Injection
  A06 - Insecure Design
  A07 - Authentication Failures
  A08 - Software or Data Integrity Failures
  A09 - Security Logging & Alerting Failures
  A10 - Mishandling of Exceptional Conditions
"""
import json
import random
import itertools
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
RANDOM_VARS = ["buf", "data", "input", "payload", "msg", "str", "temp", "val"]
RANDOM_FUNCS = ["processData", "handleRequest", "doWork", "run", "execute"]

def _var():
    return random.choice(RANDOM_VARS) + str(random.randint(1, 99))

def _func():
    return random.choice(RANDOM_FUNCS) + str(random.randint(1, 20))

# ---------------------------------------------------------------------------
# A01:2025 - Broken Access Control
# ---------------------------------------------------------------------------
def a01_vulnerable():
    samples = []
    # Direct object reference without authorization check
    samples.append(f'''
void getUserData(int userId) {{
    char query[256];
    sprintf(query, "SELECT * FROM users WHERE id = %d", userId);
    sqlite3_exec(db, query, callback, 0, NULL);
    // No authorization check - any user can access any other user's data
}}
''')
    # Path traversal
    samples.append(f'''
void downloadFile(const char* filename) {{
    char filepath[512];
    snprintf(filepath, sizeof(filepath), "/uploads/%s", filename);
    // VULNERABLE: No sanitization - attacker can use ../../etc/passwd
    FILE* f = fopen(filepath, "rb");
    if (f) {{
        char {_var()}[4096];
        fread({_var()}, 1, 4096, f);
        fclose(f);
    }}
}}
''')
    # Missing function-level access control
    samples.append(f'''
void adminDeleteUser(int targetUserId) {{
    // VULNERABLE: No role check before performing admin action
    char query[256];
    sprintf(query, "DELETE FROM users WHERE id = %d", targetUserId);
    sqlite3_exec(db, query, NULL, NULL, NULL);
    printf("User %d deleted.\\n", targetUserId);
}}
''')
    # CORS misconfiguration
    samples.append(f'''
void setCORSHeaders(struct mg_connection* conn) {{
    // VULNERABLE: Allows any origin to access the API
    mg_printf(conn, "Access-Control-Allow-Origin: *\\r\\n");
    mg_printf(conn, "Access-Control-Allow-Methods: GET, POST, DELETE\\r\\n");
    mg_printf(conn, "Access-Control-Allow-Credentials: true\\r\\n");
}}
''')
    return samples

def a01_safe():
    samples = []
    samples.append(f'''
void getUserData(int requestingUserId, int targetUserId) {{
    // SAFE: Check authorization before accessing data
    if (requestingUserId != targetUserId && !isAdmin(requestingUserId)) {{
        printf("Access denied.\\n");
        return;
    }}
    char query[256];
    snprintf(query, sizeof(query), "SELECT * FROM users WHERE id = ?");
    sqlite3_stmt* stmt;
    sqlite3_prepare_v2(db, query, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, targetUserId);
    sqlite3_step(stmt);
    sqlite3_finalize(stmt);
}}
''')
    samples.append(f'''
void downloadFile(const char* filename) {{
    // SAFE: Validate filename to prevent path traversal
    if (strstr(filename, "..") != NULL || strchr(filename, '/') != NULL) {{
        printf("Invalid filename.\\n");
        return;
    }}
    char filepath[512];
    snprintf(filepath, sizeof(filepath), "/uploads/%s", filename);
    FILE* f = fopen(filepath, "rb");
    if (f) {{
        char buffer[4096];
        size_t bytesRead = fread(buffer, 1, sizeof(buffer), f);
        fclose(f);
    }}
}}
''')
    return samples

# ---------------------------------------------------------------------------
# A02:2025 - Security Misconfiguration
# ---------------------------------------------------------------------------
def a02_vulnerable():
    samples = []
    samples.append(f'''
void startServer() {{
    // VULNERABLE: Debug mode enabled in production
    #define DEBUG_MODE 1
    #define VERBOSE_ERRORS 1
    setenv("APP_ENV", "development", 1);
    printf("Starting server with debug mode ON\\n");
    // Stack traces exposed to users
    signal(SIGSEGV, printStackTrace);
}}
''')
    samples.append(f'''
void configureDatabase() {{
    // VULNERABLE: Default credentials
    const char* db_user = "admin";
    const char* db_pass = "admin123";
    const char* db_host = "0.0.0.0";
    mysql_real_connect(conn, db_host, db_user, db_pass, "mydb", 3306, NULL, 0);
}}
''')
    samples.append(f'''
void setupHTTPHeaders(struct mg_connection* conn) {{
    // VULNERABLE: Missing security headers
    // No X-Frame-Options, no Content-Security-Policy, no X-Content-Type-Options
    mg_printf(conn, "HTTP/1.1 200 OK\\r\\n");
    mg_printf(conn, "Content-Type: text/html\\r\\n\\r\\n");
}}
''')
    return samples

def a02_safe():
    samples = []
    samples.append(f'''
void startServer() {{
    // SAFE: Production configuration
    #define DEBUG_MODE 0
    const char* env = getenv("APP_ENV");
    if (env == NULL || strcmp(env, "production") != 0) {{
        fprintf(stderr, "Warning: APP_ENV not set to production\\n");
    }}
    // Generic error handler - no stack traces
    signal(SIGSEGV, genericErrorHandler);
}}
''')
    samples.append(f'''
void setupHTTPHeaders(struct mg_connection* conn) {{
    // SAFE: All security headers set
    mg_printf(conn, "X-Frame-Options: DENY\\r\\n");
    mg_printf(conn, "X-Content-Type-Options: nosniff\\r\\n");
    mg_printf(conn, "Content-Security-Policy: default-src 'self'\\r\\n");
    mg_printf(conn, "Strict-Transport-Security: max-age=31536000\\r\\n");
}}
''')
    return samples

# ---------------------------------------------------------------------------
# A03:2025 - Software Supply Chain Failures
# ---------------------------------------------------------------------------
def a03_vulnerable():
    samples = []
    samples.append(f'''
void downloadDependency(const char* url) {{
    char cmd[512];
    // VULNERABLE: Downloading dependency over HTTP without integrity check
    sprintf(cmd, "curl -o /tmp/lib.so %s", url);
    system(cmd);
    // Loading without signature verification
    dlopen("/tmp/lib.so", RTLD_NOW);
}}
''')
    samples.append(f'''
void runBuildScript() {{
    // VULNERABLE: Executing unverified build script from remote source
    system("curl -s https://example.com/install.sh | bash");
}}
''')
    samples.append(f'''
void loadPlugin(const char* pluginPath) {{
    // VULNERABLE: Loading arbitrary shared library without validation
    void* handle = dlopen(pluginPath, RTLD_LAZY);
    if (handle) {{
        void (*init)() = dlsym(handle, "plugin_init");
        if (init) init();
    }}
}}
''')
    return samples

def a03_safe():
    samples = []
    samples.append(f'''
void downloadDependency(const char* url, const char* expectedHash) {{
    // SAFE: Download over HTTPS and verify SHA-256 hash
    char cmd[512];
    snprintf(cmd, sizeof(cmd), "curl -o /tmp/lib.so %s", url);
    system(cmd);
    
    char actualHash[65];
    computeSHA256("/tmp/lib.so", actualHash);
    if (strcmp(actualHash, expectedHash) != 0) {{
        fprintf(stderr, "Integrity check failed!\\n");
        remove("/tmp/lib.so");
        return;
    }}
    dlopen("/tmp/lib.so", RTLD_NOW);
}}
''')
    return samples

# ---------------------------------------------------------------------------
# A04:2025 - Cryptographic Failures
# ---------------------------------------------------------------------------
def a04_vulnerable():
    samples = []
    samples.append(f'''
void encryptData(const char* plaintext, char* output) {{
    // VULNERABLE: Using deprecated DES algorithm with ECB mode
    DES_cblock key = {{0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF}};
    DES_key_schedule schedule;
    DES_set_key_unchecked(&key, &schedule);
    DES_ecb_encrypt((DES_cblock*)plaintext, (DES_cblock*)output, &schedule, DES_ENCRYPT);
}}
''')
    samples.append(f'''
void hashPassword(const char* password, char* output) {{
    // VULNERABLE: Using MD5 for password hashing (broken, fast to brute-force)
    MD5_CTX ctx;
    MD5_Init(&ctx);
    MD5_Update(&ctx, password, strlen(password));
    MD5_Final((unsigned char*)output, &ctx);
}}
''')
    samples.append(f'''
void generateToken(char* token) {{
    // VULNERABLE: Using predictable random number generator
    srand(time(NULL));
    for (int i = 0; i < 32; i++) {{
        token[i] = 'A' + (rand() % 26);
    }}
    token[32] = '\\0';
}}
''')
    samples.append(f'''
void storeCredentials(const char* username, const char* password) {{
    // VULNERABLE: Storing password in plaintext
    FILE* f = fopen("credentials.txt", "a");
    fprintf(f, "%s:%s\\n", username, password);
    fclose(f);
}}
''')
    return samples

def a04_safe():
    samples = []
    samples.append(f'''
void encryptData(const unsigned char* plaintext, int len, unsigned char* output) {{
    // SAFE: Using AES-256-GCM (authenticated encryption)
    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    unsigned char key[32], iv[12], tag[16];
    RAND_bytes(key, sizeof(key));
    RAND_bytes(iv, sizeof(iv));
    EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, key, iv);
    int outlen;
    EVP_EncryptUpdate(ctx, output, &outlen, plaintext, len);
    EVP_EncryptFinal_ex(ctx, output + outlen, &outlen);
    EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, 16, tag);
    EVP_CIPHER_CTX_free(ctx);
}}
''')
    samples.append(f'''
void hashPassword(const char* password, unsigned char* hash, unsigned char* salt) {{
    // SAFE: Using Argon2id for password hashing
    RAND_bytes(salt, 16);
    argon2id_hash_raw(2, (1 << 16), 1, password, strlen(password), salt, 16, hash, 32);
}}
''')
    return samples

# ---------------------------------------------------------------------------
# A05:2025 - Injection
# ---------------------------------------------------------------------------
def a05_vulnerable():
    samples = []
    # SQL Injection
    samples.append(f'''
void login(const char* username, const char* password) {{
    char query[512];
    // VULNERABLE: SQL Injection via string concatenation
    sprintf(query, "SELECT * FROM users WHERE username='%s' AND password='%s'", username, password);
    sqlite3_exec(db, query, callback, 0, NULL);
}}
''')
    # Command Injection
    samples.append(f'''
void pingHost(const char* host) {{
    char cmd[256];
    // VULNERABLE: OS Command Injection
    sprintf(cmd, "ping -c 4 %s", host);
    system(cmd);
}}
''')
    # XSS (reflected in a C web server)
    samples.append(f'''
void handleSearch(struct mg_connection* conn, const char* searchTerm) {{
    char response[1024];
    // VULNERABLE: Reflected XSS - user input embedded directly in HTML
    sprintf(response, "<html><body><h1>Results for: %s</h1></body></html>", searchTerm);
    mg_printf(conn, "HTTP/1.1 200 OK\\r\\nContent-Type: text/html\\r\\n\\r\\n%s", response);
}}
''')
    # LDAP Injection
    samples.append(f'''
void searchUser(const char* username) {{
    char filter[256];
    // VULNERABLE: LDAP Injection
    sprintf(filter, "(uid=%s)", username);
    ldap_search_s(ld, "dc=example,dc=com", LDAP_SCOPE_SUBTREE, filter, NULL, 0, &result);
}}
''')
    # Format String
    samples.append(f'''
void logUserInput(const char* userInput) {{
    // VULNERABLE: Format String attack
    printf(userInput);
}}
''')
    return samples

def a05_safe():
    samples = []
    samples.append(f'''
void login(const char* username, const char* password) {{
    // SAFE: Parameterized query prevents SQL Injection
    const char* query = "SELECT * FROM users WHERE username=? AND password=?";
    sqlite3_stmt* stmt;
    sqlite3_prepare_v2(db, query, -1, &stmt, NULL);
    sqlite3_bind_text(stmt, 1, username, -1, SQLITE_STATIC);
    sqlite3_bind_text(stmt, 2, password, -1, SQLITE_STATIC);
    sqlite3_step(stmt);
    sqlite3_finalize(stmt);
}}
''')
    samples.append(f'''
void logUserInput(const char* userInput) {{
    // SAFE: Using format specifier prevents format string attacks
    printf("%s", userInput);
}}
''')
    return samples

# ---------------------------------------------------------------------------
# A06:2025 - Insecure Design
# ---------------------------------------------------------------------------
def a06_vulnerable():
    samples = []
    samples.append(f'''
void resetPassword(const char* email) {{
    // VULNERABLE: Predictable reset token (4-digit code)
    int resetCode = rand() % 10000;
    char msg[256];
    sprintf(msg, "Your reset code is: %04d", resetCode);
    sendEmail(email, msg);
    // No rate limiting on reset attempts
}}
''')
    samples.append(f'''
bool verifyOTP(int userCode, int expectedCode) {{
    // VULNERABLE: No rate limiting, no lockout, no expiration
    return userCode == expectedCode;
}}
''')
    samples.append(f'''
void processPayment(int userId, double amount) {{
    // VULNERABLE: No server-side validation of price
    // Client sends the price, server trusts it blindly
    deductBalance(userId, amount);
    completeOrder(userId);
}}
''')
    return samples

def a06_safe():
    samples = []
    samples.append(f'''
void resetPassword(const char* email) {{
    // SAFE: Cryptographically random token + expiration + rate limiting
    unsigned char token[32];
    RAND_bytes(token, sizeof(token));
    char hexToken[65];
    for (int i = 0; i < 32; i++) sprintf(hexToken + i*2, "%02x", token[i]);
    
    // Store token with 15-minute expiration
    storeResetToken(email, hexToken, time(NULL) + 900);
    
    // Rate limit: max 3 resets per hour
    if (getResetCount(email, 3600) >= 3) {{
        printf("Too many reset requests.\\n");
        return;
    }}
    sendEmail(email, hexToken);
}}
''')
    return samples

# ---------------------------------------------------------------------------
# A07:2025 - Authentication Failures
# ---------------------------------------------------------------------------
def a07_vulnerable():
    samples = []
    samples.append(f'''
bool authenticate(const char* username, const char* password) {{
    // VULNERABLE: Hardcoded credentials
    if (strcmp(username, "admin") == 0 && strcmp(password, "P@ssw0rd") == 0) {{
        return true;
    }}
    return false;
}}
''')
    samples.append(f'''
void createSession(int userId, char* sessionId) {{
    // VULNERABLE: Predictable session ID
    sprintf(sessionId, "session_%d_%ld", userId, time(NULL));
}}
''')
    samples.append(f'''
bool loginAttempt(const char* user, const char* pass) {{
    // VULNERABLE: No brute force protection, no account lockout
    return checkCredentials(user, pass);
}}
''')
    samples.append(f'''
void setSessionCookie(struct mg_connection* conn, const char* sessionId) {{
    // VULNERABLE: Cookie without Secure, HttpOnly, SameSite flags
    char cookie[256];
    sprintf(cookie, "Set-Cookie: sid=%s; Path=/", sessionId);
    mg_printf(conn, "%s\\r\\n", cookie);
}}
''')
    return samples

def a07_safe():
    samples = []
    samples.append(f'''
bool authenticate(const char* username, const char* password) {{
    // SAFE: Hash comparison with constant-time comparison
    unsigned char storedHash[32], salt[16];
    if (!getUserHashAndSalt(username, storedHash, salt)) return false;
    
    unsigned char computedHash[32];
    argon2id_hash_raw(2, (1<<16), 1, password, strlen(password), salt, 16, computedHash, 32);
    return CRYPTO_memcmp(storedHash, computedHash, 32) == 0;
}}
''')
    samples.append(f'''
void createSession(int userId, char* sessionId) {{
    // SAFE: Cryptographically random session ID
    unsigned char random[32];
    RAND_bytes(random, sizeof(random));
    for (int i = 0; i < 32; i++) sprintf(sessionId + i*2, "%02x", random[i]);
}}
''')
    return samples

# ---------------------------------------------------------------------------
# A08:2025 - Software or Data Integrity Failures
# ---------------------------------------------------------------------------
def a08_vulnerable():
    samples = []
    samples.append(f'''
void processUpdate(const char* updateUrl) {{
    char cmd[512];
    // VULNERABLE: Auto-update without signature verification
    sprintf(cmd, "wget -q %s -O /tmp/update.bin && chmod +x /tmp/update.bin && /tmp/update.bin", updateUrl);
    system(cmd);
}}
''')
    samples.append(f'''
void* deserializeObject(const char* data, int len) {{
    // VULNERABLE: Insecure deserialization - no type checking or validation
    void* obj = malloc(len);
    memcpy(obj, data, len);
    return obj;
}}
''')
    samples.append(f'''
void loadConfig(const char* configPath) {{
    // VULNERABLE: Loading config from user-writable directory without integrity check
    FILE* f = fopen(configPath, "r");
    char line[256];
    while (fgets(line, sizeof(line), f)) {{
        parseConfigLine(line);
    }}
    fclose(f);
}}
''')
    return samples

def a08_safe():
    samples = []
    samples.append(f'''
void processUpdate(const char* updatePath, const char* signaturePath) {{
    // SAFE: Verify digital signature before applying update
    EVP_PKEY* pubkey = loadPublicKey("update_signing_key.pem");
    if (!verifySignature(updatePath, signaturePath, pubkey)) {{
        fprintf(stderr, "Update signature verification failed!\\n");
        EVP_PKEY_free(pubkey);
        return;
    }}
    EVP_PKEY_free(pubkey);
    applyUpdate(updatePath);
}}
''')
    return samples

# ---------------------------------------------------------------------------
# A09:2025 - Security Logging & Alerting Failures
# ---------------------------------------------------------------------------
def a09_vulnerable():
    samples = []
    samples.append(f'''
void handleLogin(const char* username, const char* password) {{
    if (!authenticate(username, password)) {{
        // VULNERABLE: No logging of failed login attempt
        printf("Login failed.\\n");
        return;
    }}
    printf("Login successful.\\n");
}}
''')
    samples.append(f'''
void processTransaction(int userId, double amount) {{
    // VULNERABLE: Financial transaction with no audit trail
    deductBalance(userId, amount);
    // No log of who did what, when, or from where
}}
''')
    samples.append(f'''
void logSensitiveData(const char* username, const char* password) {{
    // VULNERABLE: Logging passwords in plaintext
    printf("[LOGIN] user=%s password=%s\\n", username, password);
    FILE* f = fopen("app.log", "a");
    fprintf(f, "[LOGIN] user=%s password=%s\\n", username, password);
    fclose(f);
}}
''')
    return samples

def a09_safe():
    samples = []
    samples.append(f'''
void handleLogin(const char* username, const char* password, const char* ipAddr) {{
    if (!authenticate(username, password)) {{
        // SAFE: Log failed attempts with context (without the password)
        logSecurityEvent("LOGIN_FAILED", username, ipAddr);
        incrementFailedAttempts(username);
        if (getFailedAttempts(username) >= 5) {{
            lockAccount(username);
            alertSecurityTeam("Account locked due to brute force", username);
        }}
        return;
    }}
    resetFailedAttempts(username);
    logSecurityEvent("LOGIN_SUCCESS", username, ipAddr);
}}
''')
    return samples

# ---------------------------------------------------------------------------
# A10:2025 - Mishandling of Exceptional Conditions
# ---------------------------------------------------------------------------
def a10_vulnerable():
    samples = []
    samples.append(f'''
void readFile(const char* filename) {{
    FILE* f = fopen(filename, "r");
    // VULNERABLE: No NULL check after fopen
    char buffer[1024];
    fread(buffer, 1, 1024, f);
    fclose(f);
}}
''')
    samples.append(f'''
void processRequest(const char* data) {{
    int* ptr = (int*)malloc(sizeof(int) * 1000);
    // VULNERABLE: No check if malloc returned NULL
    ptr[0] = 42;
    memcpy(ptr, data, 4000);
    free(ptr);
}}
''')
    samples.append(f'''
void divideValues(int a, int b) {{
    // VULNERABLE: No division by zero check
    int result = a / b;
    printf("Result: %d\\n", result);
}}
''')
    samples.append(f'''
void handleError(int errorCode) {{
    // VULNERABLE: Exposing internal state in error messages
    char errorMsg[512];
    sprintf(errorMsg, "Error %d at address 0x%p in module %s, stack: %s",
            errorCode, __builtin_return_address(0), __FILE__, getStackTrace());
    sendToClient(errorMsg);
}}
''')
    return samples

def a10_safe():
    samples = []
    samples.append(f'''
void readFile(const char* filename) {{
    // SAFE: Proper error handling
    FILE* f = fopen(filename, "r");
    if (f == NULL) {{
        logError("Failed to open file", filename);
        return;
    }}
    char buffer[1024];
    size_t bytesRead = fread(buffer, 1, sizeof(buffer), f);
    if (ferror(f)) {{
        logError("Failed to read file", filename);
    }}
    fclose(f);
}}
''')
    samples.append(f'''
void processRequest(const char* data, size_t dataLen) {{
    // SAFE: Check allocation and bounds
    if (dataLen > 4000) {{
        logError("Data too large", NULL);
        return;
    }}
    int* ptr = (int*)malloc(sizeof(int) * 1000);
    if (ptr == NULL) {{
        logError("Memory allocation failed", NULL);
        return;
    }}
    memcpy(ptr, data, dataLen);
    free(ptr);
}}
''')
    return samples

# ---------------------------------------------------------------------------
# Dataset Assembly
# ---------------------------------------------------------------------------
OWASP_CATEGORIES = {
    "A01_Broken_Access_Control":        (a01_vulnerable, a01_safe),
    "A02_Security_Misconfiguration":    (a02_vulnerable, a02_safe),
    "A03_Supply_Chain_Failures":        (a03_vulnerable, a03_safe),
    "A04_Cryptographic_Failures":       (a04_vulnerable, a04_safe),
    "A05_Injection":                    (a05_vulnerable, a05_safe),
    "A06_Insecure_Design":             (a06_vulnerable, a06_safe),
    "A07_Authentication_Failures":      (a07_vulnerable, a07_safe),
    "A08_Data_Integrity_Failures":      (a08_vulnerable, a08_safe),
    "A09_Logging_Alerting_Failures":    (a09_vulnerable, a09_safe),
    "A10_Exceptional_Conditions":       (a10_vulnerable, a10_safe),
}

def _augment(code: str, n: int = 5) -> list:
    """Create slight variations of a code sample to multiply the dataset."""
    variants = [code]
    for i in range(n - 1):
        v = code
        # Rename variables randomly
        old_var = random.choice(["buf", "data", "ptr", "result", "output", "input", "buffer"])
        new_var = old_var + str(random.randint(10, 99))
        v = v.replace(old_var, new_var, 1)
        # Add random whitespace / comments
        lines = v.split("\n")
        insert_pos = random.randint(1, max(1, len(lines) - 2))
        comment = f"    // step {random.randint(1,100)}: {random.choice(['validate', 'process', 'check', 'handle', 'transform'])} {random.choice(['input', 'data', 'request', 'payload'])}"
        lines.insert(insert_pos, comment)
        variants.append("\n".join(lines))
    return variants


def generate_dataset():
    records = []
    
    for category, (vuln_fn, safe_fn) in OWASP_CATEGORIES.items():
        vuln_samples = vuln_fn()
        safe_samples = safe_fn()
        
        for sample in vuln_samples:
            for variant in _augment(sample.strip(), n=8):
                records.append({
                    "raw_code": variant,
                    "is_vulnerable": 1,
                    "owasp_category": category
                })
        
        for sample in safe_samples:
            for variant in _augment(sample.strip(), n=8):
                records.append({
                    "raw_code": variant,
                    "is_vulnerable": 0,
                    "owasp_category": category
                })
    
    random.shuffle(records)
    return records


def main():
    output_dir = Path("data/owasp2025")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating OWASP Top 10:2025 specialized dataset...")
    records = generate_dataset()
    
    # Split train/test (80/20)
    split = int(len(records) * 0.8)
    train = records[:split]
    test = records[split:]
    
    train_path = output_dir / "train.jsonl"
    test_path = output_dir / "test.jsonl"
    
    with open(train_path, "w", encoding="utf-8") as f:
        for r in train:
            f.write(json.dumps(r) + "\n")
    
    with open(test_path, "w", encoding="utf-8") as f:
        for r in test:
            f.write(json.dumps(r) + "\n")
    
    # Stats
    vuln = sum(1 for r in records if r["is_vulnerable"] == 1)
    safe = sum(1 for r in records if r["is_vulnerable"] == 0)
    
    print(f"\nDataset generated successfully!")
    print(f"  Total samples  : {len(records)}")
    print(f"  Vulnerable     : {vuln}")
    print(f"  Safe           : {safe}")
    print(f"  Train samples  : {len(train)}")
    print(f"  Test samples   : {len(test)}")
    print(f"\n  Categories covered:")
    
    for cat in OWASP_CATEGORIES:
        count = sum(1 for r in records if r["owasp_category"] == cat)
        print(f"    {cat}: {count} samples")
    
    print(f"\n  Files:")
    print(f"    {train_path}")
    print(f"    {test_path}")


if __name__ == "__main__":
    main()
