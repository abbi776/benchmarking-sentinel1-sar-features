// ==============================
// main_workflow.js
// ==============================
//
// Copy the functions from:
//
//   00_utils_sar.js
//   01_border_noise.js
//   02_speckle_filter.js
//   03_rtc.js
//   04_feature_extraction.js
//
// ABOVE this block when running in GEE.
// ==============================


// ----------------------------------
// Study Area (edit for your project)
// ----------------------------------
var studyArea = ee.FeatureCollection(
  'projects/wpe-monitoring-sar-comparison/assets/ROI_boundary_n'
);
var geom = studyArea.geometry();
Map.centerObject(geom, 8);


// ----------------------------------
// Per-image preprocessing
// ----------------------------------
function preprocessImage(image) {

  var lin = dbToLin(image);
  var bn  = maskByIncidenceAngle(lin);
  var sp  = refinedLee(bn);
  var rtcImg = applyRTC(sp);

  return rtcImg;
}


// ----------------------------------
// Sentinel-1 Collection
// ----------------------------------
var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(geom)
  .filterDate('2025-07-06', '2025-07-15')
  .filter(ee.Filter.eq('instrumentMode', 'IW'))
  .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
  .map(preprocessImage);

print('Processed images count:', s1.size());


// ----------------------------------
// Mosaic + Clip
// ----------------------------------
var rtcMosaic = s1.mosaic().clip(geom);


// ----------------------------------
// Feature generation
// ----------------------------------
var withDb = ee.Image(linToDb(rtcMosaic))
  .select(['VV','VH'], ['VV_dB','VH_dB']);

var base = rtcMosaic
  .select(['VV','VH'])
  .addBands(withDb);

var withIndices  = computeIndices(base);
var withTextures = computeGLCM(withIndices, 32);

var finalImage = withTextures.toFloat();

print('Final bands:', finalImage.bandNames());


// ----------------------------------
// Visualization
// ----------------------------------
Map.addLayer(finalImage.select('VV_dB'), {min:-25, max:0}, 'VV dB');
Map.addLayer(finalImage.select('RVI'), {min:0,max:1,palette:['brown','yellow','green']}, 'RVI');


// ----------------------------------
// Export
// ----------------------------------
Export.image.toDrive({
  image: finalImage,
  description: 'S1_FEATURES_EXAMPLE',
  folder: 'GEE_Sentinel1',
  fileNamePrefix: 'S1_FEATURES_EXAMPLE',
  region: geom,
  scale: 10,
  crs: 'EPSG:3577',
  maxPixels: 1e13
});
