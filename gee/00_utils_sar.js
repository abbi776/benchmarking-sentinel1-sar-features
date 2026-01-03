/**
 * @name 00_utils_sar
 * @description Core utilities for Sentinel-1 backscatter conversion.
 * Includes safeguards against numerical instability (log10 of 0).
 */

/**
 * Converts dB (Decibels) to Linear Power.
 * Formula: 10 ^ (dB / 10)
 * * Crucially preserves the 'angle' band required for RTC.
 */
exports.dbToLin = function (image) {
  var vv = ee.Image(10).pow(image.select('VV').divide(10)).rename('VV');
  var vh = ee.Image(10).pow(image.select('VH').divide(10)).rename('VH');

  // We explicitly re-attach the 'angle' band here so the next steps 
  // (Border Noise & RTC) have the geometry data they need.
  return ee.Image.cat([vv, vh, image.select('angle')])
    .copyProperties(image, image.propertyNames());
};

/**
 * Converts Linear Power to dB.
 * Formula: 10 * log10(Linear)
 * * Includes an epsilon clamp to prevent -Infinity errors on 0 values.
 */
exports.linToDb = function (image) {
  // Define a small number (epsilon) to avoid log10(0)
  // 1e-5 corresponds to -50 dB, which is well below the S1 noise floor (~-25dB).
  // Any pixel 0 or smaller becomes 1e-5, preventing math errors.
  var eps = 1e-5; 

  var vv = image.select('VV')
    .max(eps)
    .log10()
    .multiply(10)
    .rename('VV');

  var vh = image.select('VH')
    .max(eps)
    .log10()
    .multiply(10)
    .rename('VH');

  // Note: We usually do NOT need the 'angle' band for final visualization/export,
  // so we only return the backscatter bands here.
  return ee.Image.cat([vv, vh])
    .copyProperties(image, image.propertyNames());
};
