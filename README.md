# insightmri

Pipeline for MRI anonymization and preprocessing. The pipeline has the following steps
1. DICOM to NIFTI conversion
2. Skull Stripping and Registration

The pipeline can be configured using the `config.yml` file. This is a key-value pair file.
## 1. DICOM to NIfTI
The DICOM files are converted to NifTI using [dcm2niix utility](https://github.com/rordenlab/dcm2niix). We utilize the [nipype](https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.dcm2nii.html)
python wrapper which provides a programmatic interface for the dcm2niix utility. <br/>
### Rescaling DICOM files
DICOM files contain upto 12 bits of image information. To store higher resolution images, the DICOM  utilizes the `Rescale Slope`
`Rescale Intercept` and `Rescale Type`. Specialized DICOM viewers apply the necessary transformations to recover the correct image.
However, the Dcm2niix and FSL utilities do not apply necessary transformations. <br/>
For rescaling, we define 2 domains, with and without rescaling.
1. Using the Window Center and Length extract the Darkest and Brightest Pixel values in domain 1
2. Transforming these to the actual Pixel Intensities in domain 2 ( y = mx+b)
3. Find the new Window Center and Width
4. Modifying DICOM, deleting Rescales, Setting new Windows
5. Extracting pixel data from modified dicom
6. Applying windowed transformation
7. Halving the result ( result is 2 times bigger than pixel data)
8. Encoding pixel data explicitly as `np.ushort`
9. Saving encoded data

This results in 1 bit reduction of the resolution of the image (in most cases).

Configuring the `config.yml` the following command should be run from within the repo.<br/>
```python src/prepare.py```

## 2. Skull Stripping and Registration
Each converted `.nii.gz` file is now skull stripped using the [fsl](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/BET/UserGuide) skull stripping utility. We use the programmatic wrapper provided by [nipype](https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.fsl.preprocess.html). <br/>
The following command should be used from within the repo <br/>
```python src/process_mri.py --bet --reorient --registration```<br/>

Settings for the BET and Registration are defined in the `config.yml` and can be specified using `BET_FLAGS` and `FLIRT_FLAGS`. 
The template for registration can be found in `./templates`