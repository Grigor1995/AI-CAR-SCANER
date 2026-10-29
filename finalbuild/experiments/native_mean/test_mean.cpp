#include <cassert>
#include <cmath>
#include <cstddef>
#include <limits>
extern "C" int telemetry_mean(const double*, std::size_t, double*) noexcept;
int main() {
    double out=42; const double xs[]={1,2,3};
    assert(telemetry_mean(xs,3,&out)==0 && out==2);
    assert(telemetry_mean(nullptr,3,&out)==1);
    assert(telemetry_mean(xs,0,&out)==1);
    assert(telemetry_mean(xs,3,nullptr)==1);
    const double nan[]={std::numeric_limits<double>::quiet_NaN()};
    assert(telemetry_mean(nan,1,&out)==2);
    const double inf[]={std::numeric_limits<double>::infinity()};
    assert(telemetry_mean(inf,1,&out)==2);
    const double cancel[]={1e16,1,-1e16};
    assert(telemetry_mean(cancel,3,&out)==0 && std::abs(out-1.0/3)<1e-15);
    const double huge[]={1e308,1e308};
    assert(telemetry_mean(huge,2,&out)==0 && out==1e308);
}
