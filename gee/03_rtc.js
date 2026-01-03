/**
 * @name 03_rtc
 * @description Applies Radiometric Normalization to convert Sigma0 to Gamma0 (Ellipsoid).
 *
 * METHODOLOGY NOTE:
 * This script applies the "Ellipsoidal Correction" method:
 *
 *   Gamma0 = Sigma0 / cos(IncidenceAngle)
 *
 * Since the GEE environment does not provide precise orbit state vectors
 * required for rigorous Volumetric Terrain Flattening (which requires accurate look azimuth),
 * and the study area (floodplain) has low relief, this ellipsoidal correction is the most
 * scientifically robust and defensible approach. It avoids introducing artifacts
 * from static azimuth approximations.
 *
 * Reference:
 * Small, D. (2011). Flattening Gamma: Radiometric Terrain Correction for SAR Imagery.
 */

exports.applyRTC = function(image) {
  image = ee.Image(image);

  // 1. Incidence angle (convert degrees → radians)
  var theta_i = image.select('angle').multiply(Math.PI / 180);

  // 2. Gamma0 = Sigma0_linear / cos(theta_i)
  var gamma0 = image.select(['VV', 'VH']).divide(theta_i.cos());

  // 3. Return image with renamed bands + preserved angle
  return ee.Image.cat([gamma0, image.select('angle')])
    .rename(['VV', 'VH', 'angle'])
    .copyProperties(image, image.propertyNames());
};
