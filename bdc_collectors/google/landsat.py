#
# This file is part of BDC-Collectors.
# Copyright (C) 2020 INPE.
#
# BDC-Collectors is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Define the data set of Google for Landsat products."""

import shutil
import tarfile
from pathlib import Path

import rasterio

from ..usgs.base import BaseLandsat, LandsatScene
from ..usgs.landsat5 import Landsat5
from ..usgs.landsat7 import Landsat7
from ..usgs.landsat8 import Landsat8
from ..utils import working_directory


class GoogleLandsat(BaseLandsat):
    """Define the Landsat product definition."""

    bucket = 'gcp-public-data-landsat'

    def __init__(self, scene_id: str):
        """Create the GoogleLandsat instance."""
        self.parser = self.parser_class(scene_id)

    @property
    def folder(self):
        """Retrieve base folder of Landsat."""
        return self.parser.scene_id

    def get_url(self) -> str:
        """Get the relative URL path in the Landsat bucket."""
        source = self.parser.source()
        tile = self.parser.tile_id()
        scene_id = self.parser.scene_id

        return f'{source}/01/{tile[:3]}/{tile[3:]}/{scene_id}'

    def apply_processing(self, file_path: Path):
        """Apply a function in post download processing.

        This function basically removes the file compression of Tile files
        to be similar USGS scene.
        """
        if file_path.suffix.lower() == '.tif':
            with rasterio.open(str(file_path), 'r') as source_data_set:
                profile = source_data_set.profile
                raster = source_data_set.read(1)

            profile.pop('compress', '')
            profile.update(dict(
                tiled=False
            ))

            with rasterio.open(str(file_path), 'w', **profile) as target_data_set:
                target_data_set.write_band(1, raster)

    def process(self, downloaded_files: list, output: str) -> str:
        """Compress the downloaded files into scene.tar.gz."""
        compressed_file_path = Path(output) / f'{self.parser.scene_id}.tar.gz'

        with tarfile.open(compressed_file_path, 'w:gz') as compressed_file:
            relative = str(Path(output) / self.parser.scene_id)
            with working_directory(relative):
                for f in downloaded_files:
                    compressed_file.add(str(Path(f).relative_to(relative)))

        shutil.rmtree(str(Path(output) / self.parser.scene_id))

        return str(compressed_file_path)
