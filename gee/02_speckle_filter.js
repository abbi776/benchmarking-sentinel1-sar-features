/**
 * @name 02_speckle_filter
 * @description Applies the Refined Lee Speckle Filter (Lee et al., 1999).
 * This adaptive filter preserves edges while reducing speckle in homogeneous areas.
 * * @requires Image must be in LINEAR power (not dB).
 * @requires Image must contain 'VV', 'VH', and 'angle' bands.
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


exports.refinedLee = function(image) {
  image = ee.Image(image);

  // We explicitly filter only the polarization bands.
  // The 'angle' band is preserved but excluded from filtering to avoid artifacts.
  var bandNames = ee.List(['VV', 'VH']);

  // Map the filter over the two bands
  var result = ee.ImageCollection(bandNames.map(function(b) {
    b = ee.String(b);
    var img = image.select([b]);

    // --- 1. Local Statistics (3x3) ---
    var weights3 = ee.List.repeat(ee.List.repeat(1, 3), 3);
    var kernel3 = ee.Kernel.fixed(3, 3, weights3, 1, 1, false);

    var mean3 = img.reduceNeighborhood(ee.Reducer.mean(), kernel3);
    var variance3 = img.reduceNeighborhood(ee.Reducer.variance(), kernel3);

    // --- 2. Edge Detection (7x7) ---
    var sample_weights = ee.List([
      [0,0,0,0,0,0,0], [0,1,0,1,0,1,0], [0,0,0,0,0,0,0],
      [0,1,0,1,0,1,0], [0,0,0,0,0,0,0], [0,1,0,1,0,1,0], [0,0,0,0,0,0,0]
    ]);
    var sample_kernel = ee.Kernel.fixed(7, 7, sample_weights, 3, 3, false);

    var sample_mean = mean3.neighborhoodToBands(sample_kernel);
    var sample_var  = variance3.neighborhoodToBands(sample_kernel);

    // Calculate Gradients
    var gradients = sample_mean.select(1).subtract(sample_mean.select(7)).abs();
    gradients = gradients.addBands(sample_mean.select(6).subtract(sample_mean.select(2)).abs());
    gradients = gradients.addBands(sample_mean.select(3).subtract(sample_mean.select(5)).abs());
    gradients = gradients.addBands(sample_mean.select(0).subtract(sample_mean.select(8)).abs());

    var max_gradient = gradients.reduce(ee.Reducer.max());
    var gradmask = gradients.eq(max_gradient);
    gradmask = gradmask.addBands(gradmask);

    // --- 3. Determine Orientation (8 directions) ---
    var directions = sample_mean.select(1).subtract(sample_mean.select(4))
      .gt(sample_mean.select(4).subtract(sample_mean.select(7))).multiply(1);
    directions = directions.addBands(sample_mean.select(6).subtract(sample_mean.select(4))
      .gt(sample_mean.select(4).subtract(sample_mean.select(2))).multiply(2));
    directions = directions.addBands(sample_mean.select(3).subtract(sample_mean.select(4))
      .gt(sample_mean.select(4).subtract(sample_mean.select(5))).multiply(3));
    directions = directions.addBands(sample_mean.select(0).subtract(sample_mean.select(4))
      .gt(sample_mean.select(4).subtract(sample_mean.select(8))).multiply(4));

    directions = directions.addBands(directions.select(0).not().multiply(5));
    directions = directions.addBands(directions.select(1).not().multiply(6));
    directions = directions.addBands(directions.select(2).not().multiply(7));
    directions = directions.addBands(directions.select(3).not().multiply(8));

    directions = directions.updateMask(gradmask);
    directions = directions.reduce(ee.Reducer.sum());

    // --- 4. Filtering Statistics ---
    var sample_stats = sample_var.divide(sample_mean.multiply(sample_mean));
    var sigmaV = sample_stats.toArray()
      .arraySort()
      .arraySlice(0, 0, 5)
      .arrayReduce(ee.Reducer.mean(), [0]);

    // Directional Kernels
    var rect_weights = ee.List.repeat(ee.List.repeat(0, 7), 3)
      .cat(ee.List.repeat(ee.List.repeat(1, 7), 4));
    var diag_weights = ee.List([
      [1,0,0,0,0,0,0], [1,1,0,0,0,0,0], [1,1,1,0,0,0,0],
      [1,1,1,1,0,0,0], [1,1,1,1,1,0,0], [1,1,1,1,1,1,0], [1,1,1,1,1,1,1]
    ]);

    var rect_kernel = ee.Kernel.fixed(7, 7, rect_weights, 3, 3, false);
    var diag_kernel = ee.Kernel.fixed(7, 7, diag_weights, 3, 3, false);

    var dir_mean = img.reduceNeighborhood(ee.Reducer.mean(), rect_kernel).updateMask(directions.eq(1));
    var dir_var  = img.reduceNeighborhood(ee.Reducer.variance(), rect_kernel).updateMask(directions.eq(1));

    dir_mean = dir_mean.addBands(img.reduceNeighborhood(ee.Reducer.mean(), diag_kernel).updateMask(directions.eq(2)));
    dir_var  = dir_var.addBands(img.reduceNeighborhood(ee.Reducer.variance(), diag_kernel).updateMask(directions.eq(2)));

    for (var i = 1; i < 4; i++) {
      dir_mean = dir_mean.addBands(img.reduceNeighborhood(ee.Reducer.mean(), rect_kernel.rotate(i)).updateMask(directions.eq(2*i+1)));
      dir_var  = dir_var.addBands(img.reduceNeighborhood(ee.Reducer.variance(), rect_kernel.rotate(i)).updateMask(directions.eq(2*i+1)));
      dir_mean = dir_mean.addBands(img.reduceNeighborhood(ee.Reducer.mean(), diag_kernel.rotate(i)).updateMask(directions.eq(2*i+2)));
      dir_var  = dir_var.addBands(img.reduceNeighborhood(ee.Reducer.variance(), diag_kernel.rotate(i)).updateMask(directions.eq(2*i+2)));
    }

    dir_mean = dir_mean.reduce(ee.Reducer.sum());
    dir_var  = dir_var.reduce(ee.Reducer.sum());

    // --- 5. Final Calculation ---
    var varX = dir_var.subtract(dir_mean.multiply(dir_mean).multiply(sigmaV))
      .divide(sigmaV.add(1.0));
    var bWeight = varX.divide(dir_var);

    var filt = dir_mean.add(bWeight.multiply(img.subtract(dir_mean)))
      .arrayProject([0])
      .arrayFlatten([['f']])
      .rename([b]);

    return ee.Image(filt);
  })).toBands().rename(['VV','VH']); // Ensure output bands are named correctly

  // Re-attach the angle band (Critical for the next RTC step)
  var out = ee.Image.cat([result, image.select('angle')]);
  
  return ee.Image(out).copyProperties(image, image.propertyNames());
};
