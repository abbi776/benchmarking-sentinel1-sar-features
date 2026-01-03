/**
 * @name 01_border_noise
 * @description Masks pixels with incidence angles outside the high-quality swath range.
 * This acts as a proxy for 'Border Noise Removal' in GEE.
 * * Thresholds (User-defined based on literature):
 * - Min Angle: 30.63993 degrees
 * - Max Angle: 45.23993 degrees
 */

/**
 * Adapted from:
 * A. Mullissa et al. (2021),
 * "Sentinel-1 SAR Backscatter Analysis Ready Data Preparation in Google Earth Engine"
 * Remote Sensing 13(10), 1954. doi:10.3390/rs13101954
 *
 * Original Refined-Lee implementation:
 * https://github.com/adugnag/gee_s1_ard
 *
 * Filter structure and directional statistics follow the ARD reference,
 * with modifications for WPE context, band handling, and gamma-0 workflow.
 */

/**
 * Masks pixels based on the 'angle' band to remove swath edge artifacts.
 * * @param {ee.Image} image - Sentinel-1 image (must contain 'angle' band).
 * @param {number} [minDeg=30.63993] - Minimum valid angle.
 * @param {number} [maxDeg=45.23993] - Maximum valid angle.
 * @returns {ee.Image} Masked image with properties preserved.
 */
exports.maskByIncidenceAngle = function(image, minDeg, maxDeg) {
  image = ee.Image(image);

  // Thresholds 
  minDeg = (minDeg === undefined) ? 30.63993 : minDeg;
  maxDeg = (maxDeg === undefined) ? 45.23993 : maxDeg;

  var ang = image.select('angle');

  // Create mask: Keep pixels strictly BETWEEN min and max
  var mask = ang.gt(minDeg).and(ang.lt(maxDeg));

  return ee.Image(image.updateMask(mask))
    .copyProperties(image, image.propertyNames());
};
