# modal-airsas
Should maybe have forked the og airsas repo:
    https://github.com/tblanford/airsas

## step 0
- get data (see download_to_volume.py)
- get single image pipeline hooked up [a la makeSasImage.m](https://github.com/tblanford/airsas/blob/main/makeSasImage.m)

## step 1
Scale out [MATLAB/Octave beamformer](https://github.com/tblanford/airsas/blob/main/utilities/reconstructImage.m)

Show beamforming whole dataset can take around the same time as beamforming one image

## bonus
- re-implement GPU acceled differentiable torch former
- image beamforming speed maxxing