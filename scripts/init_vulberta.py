import json
import time
from app.infrastructure.ml.vulberta_trainer import VulBERTaTrainer
from app.shared.settings import settings

def main():
    print("Testing VulBERTa Trainer...")
    
    # We need a dummy dataset with raw_code to pass validation
    dummy_dataset = [
        {"raw_code": "int main() { char buf[10]; gets(buf); return 0; }", "is_vulnerable": 1},
        {"raw_code": "void test() { char *p = malloc(10); strcpy(p, \"1234567890123\"); }", "is_vulnerable": 1},
        {"raw_code": "void vuln1() { char buf[10]; scanf(\"%s\", buf); }", "is_vulnerable": 1},
        {"raw_code": "void vuln2() { char buf[10]; sprintf(buf, \"%s\", \"123456789012345\"); }", "is_vulnerable": 1},
        {"raw_code": "void vuln3() { system(\"rm -rf /\"); }", "is_vulnerable": 1},
        {"raw_code": "int main() { return 0; }", "is_vulnerable": 0},
        {"raw_code": "void test() { printf(\"hello\"); }", "is_vulnerable": 0},
        {"raw_code": "void safe1() { char buf[10]; strncpy(buf, \"hello\", sizeof(buf)-1); }", "is_vulnerable": 0},
        {"raw_code": "void safe2() { int x = 5; return x; }", "is_vulnerable": 0},
        {"raw_code": "void safe3() { FILE *f = fopen(\"test.txt\", \"r\"); if(f) fclose(f); }", "is_vulnerable": 0}
    ]
    
    trainer = VulBERTaTrainer(model_path=settings.model_path, report_path=settings.metrics_report_path, test_size=0.5)
    
    start_time = time.time()
    # Train (which for VulBERTa just initializes the pipeline, tests it, and saves it)
    metrics = trainer.train(dummy_dataset)
    print(f"Finished in {time.time() - start_time:.2f}s")
    
    print("Metrics:")
    print(json.dumps(metrics, indent=2))
    print(f"Model saved to {settings.model_path}")

if __name__ == "__main__":
    main()
