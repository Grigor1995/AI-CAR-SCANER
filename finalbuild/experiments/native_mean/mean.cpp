// Experimental ONLY: not imported by application code. No ECU or I/O access.
#include <cmath>
#include <cstddef>
#include <limits>
#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT __attribute__((visibility("default")))
#endif
extern "C" EXPORT int telemetry_mean(const double* values, std::size_t count, double* output) noexcept {
    if (!values || !output || !count) return 1;
    long double sum = 0, correction = 0;
    for (std::size_t i = 0; i < count; ++i) {
        if (!std::isfinite(values[i])) return 2;
        const long double value = values[i];
        const long double next = sum + value;
        correction += std::abs(sum) >= std::abs(value) ? (sum-next)+value : (value-next)+sum;
        sum = next;
    }
    const long double result = (sum+correction)/count;
    if (!std::isfinite(result) || std::abs(result) > std::numeric_limits<double>::max()) return 3;
    *output = static_cast<double>(result);
    return 0;
}
