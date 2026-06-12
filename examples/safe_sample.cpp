#include <iostream>
#include <string>

// Safe function that calculates the factorial of a number
int calculateFactorial(int n) {
    if (n < 0) {
        return 0; // Error case
    }
    int result = 1;
    for (int i = 1; i <= n; ++i) {
        result *= i;
    }
    return result;
}

int main() {
    int number = 5;
    
    // Hardcoded logic, no user input, no memory allocation, completely safe
    int fact = calculateFactorial(number);
    
    std::cout << "The factorial of " << number << " is " << fact << std::endl;
    
    return 0;
}
