#include "math.h"


//not used yet, but intersting:
//http://www.exstrom.com/journal/sigproc/
class Butterworth
{
public:
	float filter(float input);
	void calculateCoefficients(float frequency_ratio);

private:
	float a0, a1, a2;
	float b0, b1, b2;
	float w0, w1, w2;
};