#include "Butterworth.h"

void Butterworth::calculateCoefficients(float frequency_ratio)
{
  //https://stackoverflow.com/questions/20924868/calculate-coefficients-of-2nd-order-butterworth-low-pass-filter
  const double ita = 1.0 / tan(M_PI * frequency_ratio);
  const double q = sqrt(2.0);
  b0 = 1.0 / (1.0 + q * ita + ita * ita);
  b1 = 2 * b0;
  b2 = b0;
  a1 = 2.0 * (ita * ita - 1.0) * b0;
  a2 = -(1.0 - q * ita + ita * ita) * b0;
}

float Butterworth::filter(float input)
{
  //https://www.hs-schmalkalden.de/fileadmin/portal/Dokumente/Fakult%C3%A4t_ET/Personal/Roppel/Buch/Realisierung_Digitaler_Filter_in_C.pdf
  float result;
  w0 = input + (a1 * w1) + (a2 * w2);
  result = (b0 * w0) + (b1 * w1) + (b2 * w2);
  w2 = w1;
  w1 = w0;
  return result;
}