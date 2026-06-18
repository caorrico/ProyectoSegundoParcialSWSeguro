#include <iostream>
#include <vector>
#include <numeric>

double calculateAverage(const std::vector<double>& values) {
    if (values.empty()) {
        return 0.0;
    }
    double sum = std::accumulate(values.begin(), values.end(), 0.0);
    return sum / values.size();
}

int main() {
    std::vector<double> data = {10.5, 20.3, 30.1, 40.7, 50.2};
    double avg = calculateAverage(data);
    std::cout << "Average: " << avg << std::endl;
    return 0;
}
