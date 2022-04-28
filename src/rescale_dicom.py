from pydicom import dcmread
from pydicom.pixel_data_handlers import util
import numpy as np


def rescale_dicom(file, data_dir, target_dir=None, replace=False):
    if not replace:
        if target_dir is None:
            raise AttributeError("Please provide the target directory")
    # Reading the DICOM file
    dcm = dcmread(data_dir + file)

    # Will skip if the Rescale Intercept not present
    if 'RescaleIntercept' in dcm:
        print('Skipping file - doesn\'t have rescale')
        return

    # extract the darkest and brightest pixel intensities in the rescale domain
    # darkest_pixel = window_center - 0.5*window_width
    # brightest_pixel = window_center + 0.5*window_width
    c1, c2 = dcm.WindowCenter
    w1, w2 = dcm.WindowWidth
    darkest = c1 - w1 / 2
    brightest = c1 + w1 / 2

    # calcuate the darkest and brightest pixel in the no-scale domain
    # using pixel_intensity = slope * stored_value + Intercept
    slope = dcm.RescaleSlope
    intercept = dcm.RescaleIntercept
    xd = (darkest - intercept) // slope
    xb = (brightest - intercept) // slope

    # calculate the new center and width
    # using previous equation
    new_c = (xd + xb) // 2
    new_w = (xb - xd)

    # update dicom file keys
    del dcm.RescaleSlope
    del dcm.RescaleIntercept
    del dcm.RescaleType
    dcm.WindowCenter = new_c
    dcm.WindowWidth = new_w

    img = dcm.pixel_array
    # yields the same result as img, since no transformation
    mod = util.apply_modality_lut(img, dcm)
    # yields the windowed transformation with pixel intensities doubled
    voi = util.apply_voi_lut(mod, dcm, index=0)

    # halving the data to fit in the appropriate data range
    new_data = voi // 2
    dcm.PixelData = new_data.astype(np.ushort).tobytes()

    # saving the file
    if replace:
        dcm.save_as(data_dir + file)
    else:
        dcm.save(target_dir + file)

