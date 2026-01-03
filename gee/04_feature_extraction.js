/**
 * @name 04_feature_extraction
 * @description Generates the final feature stack for Machine Learning.
 * 1. Computes 10 SAR Indices (using Linear Power).
 * 2. Computes GLCM Textures (using Quantized dB data).
 * @requires Input image must have bands: 'VV', 'VH' (Linear) and 'VV_dB', 'VH_dB' (Decibels).
 */

/**
 * Compute SAR Indices (Ratios and Differences).
 * Calculations are performed in LINEAR scale to preserve physical meaning.
 */
exports.computeIndices = function(image) {
  image = ee.Image(image);

  var VV    = image.select('VV');        // Linear Gamma0
  var VH    = image.select('VH');        // Linear Gamma0
  var VV_dB = image.select('VV_dB');     // Log Gamma0
  var VH_dB = image.select('VH_dB');     // Log Gamma0

  var NDPI  = VV.subtract(VH).divide(VV.add(VH)).rename('NDPI');
  var NRPB  = VH.subtract(VV).divide(VH.add(VV)).rename('NRPB');
  var PR    = VV.divide(VH).rename('PR');
  var XPR   = VH.divide(VV).rename('XPR');
  var RVI   = VH.multiply(4).divide(VV.add(VH)).rename('RVI');
  var SUM   = VV.add(VH).rename('SUM');
  var DIFF  = VV.subtract(VH).rename('DIFF');
  var PROD  = VV.multiply(VH).rename('PROD');
  var VDDPI = VV.add(VH).divide(VV).rename('VDDPI');
  var LOGR  = VV_dB.subtract(VH_dB).rename('LOG_RATIO');

  return ee.Image.cat([
    VV_dB, VH_dB,
    NDPI, NRPB, PR, XPR,
    RVI, SUM, DIFF, PROD,
    VDDPI, LOGR
  ]);
};

/**
 * Compute GLCM Textures from Quantized dB Data.
 * Window: 5x5
 * Levels: default 32
 */
exports.computeGLCM = function(image, levels) {
  image  = ee.Image(image);
  levels = (levels === undefined) ? 32 : levels;

  var VV_dB = image.select('VV_dB');
  var VH_dB = image.select('VH_dB');

  var VV_q = VV_dB
    .clamp(-25, 5)
    .unitScale(-25, 5)
    .multiply(levels - 1)
    .toInt()
    .rename('VV_q');

  var VH_q = VH_dB
    .clamp(-30, 0)
    .unitScale(-30, 0)
    .multiply(levels - 1)
    .toInt()
    .rename('VH_q');

  var glcmVV = VV_q.glcmTexture({size: 2});
  var glcmVH = VH_q.glcmTexture({size: 2});

  var metrics = ['asm', 'corr', 'var', 'idm', 'savg', 'ent', 'contrast'];
  
  var selectMetrics = function(glcmImg, polName, qName) {
    var oldNames = metrics.map(function(m) { return qName + '_' + m; });
    var newNames = metrics.map(function(m) { 
      var fancyName = m.toUpperCase();
      if (m === 'ent') fancyName = 'ENTROPY';
      if (m === 'savg') fancyName = 'SUMAVE';
      return 'GLCM_' + fancyName + '_' + polName; 
    });
    return glcmImg.select(oldNames, newNames);
  };

  var vvTex = selectMetrics(glcmVV, 'VV', 'VV_q');
  var vhTex = selectMetrics(glcmVH, 'VH', 'VH_q');

  return image.addBands(vvTex).addBands(vhTex);
};
