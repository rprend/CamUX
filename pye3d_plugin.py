"""
(*)~---------------------------------------------------------------------------
Pupil - eye tracking platform
Copyright (C) 2012-2020 Pupil Labs

Distributed under the terms of the GNU
Lesser General Public License (LGPL v3.0).
See COPYING and COPYING.LESSER for license details.
---------------------------------------------------------------------------~(*)
"""
import logging

import pye3d
from pye3d.detector_3d import Detector3D, CameraModel, DetectorMode
from methods import normalize

from .detector_base_plugin import PupilDetectorPlugin


class Pye3DPlugin():
    pupil_detection_identifier = "3d"
    # pupil_detection_method implemented as variable

    label = "Pye3D"
    icon_font = "pupil_icons"
    icon_chr = chr(0xEC19)
    order = 0.101

    @property
    def pupil_detector(self):
        return self.detector

    def __init__(
        self,
        g_pool=None,
    ):
        super().__init__(g_pool=g_pool)
        self.camera = CameraModel(
            focal_length=self.g_pool.capture.intrinsics.focal_length,
            resolution=self.g_pool.capture.intrinsics.resolution,
        )
        mode = (DetectorMode.blocking)
        self.detector = Detector3D(camera=self.camera, long_term_mode=mode)

        method_suffix = {
            DetectorMode.asynchronous: "real-time",
            DetectorMode.blocking: "post-hoc",
        }
        self.pupil_detection_method = f"pye3d {pye3d.__version__} {method_suffix[mode]}"

    def create_pupil_datum(self, norm_pos, diameter, confidence, timestamp) -> dict:
        """"""
        eye_id = self.g_pool.eye_id

        # TODO: Assert arguments are valid

        # Create basic pupil datum with required fields
        datum = {}
        datum["id"] = eye_id
        datum["topic"] = f"pupil.{eye_id}.{self.pupil_detection_identifier}"
        datum["method"] = f"{self.pupil_detection_method}"
        datum["norm_pos"] = norm_pos
        datum["diameter"] = diameter
        datum["confidence"] = confidence
        datum["timestamp"] = timestamp
        return datum


    def _process_camera_changes(self):
        camera = CameraModel(
            focal_length=self.g_pool.capture.intrinsics.focal_length,
            resolution=self.g_pool.capture.intrinsics.resolution,
        )
        if self.camera == camera:
            return

        logger.debug(f"Camera model change detected: {camera}. Resetting 3D detector.")
        self.camera = camera
        self.detector.reset_camera(self.camera)


    def detect(self, frame, **kwargs):
        self._process_camera_changes()

        previous_detection_results = kwargs.get("previous_detection_results", [])
        for datum in previous_detection_results:
            if datum.get("method", "") == "2d c++":
                datum_2d = datum
                break
        else:
            logger.warning(
                "Required 2d pupil detection input not available. "
                "Returning default pye3d datum."
            )
            return self.create_pupil_datum(
                norm_pos=[0.5, 0.5],
                diameter=0.0,
                confidence=0.0,
                timestamp=frame.timestamp,
            )

        result = self.detector.update_and_detect(
            datum_2d, frame.gray, debug=self.is_debug_window_open
        )

        norm_pos = normalize(
            result["location"], (frame.width, frame.height), flip_y=True
        )
        template = self.create_pupil_datum(
            norm_pos=norm_pos,
            diameter=result["diameter"],
            confidence=result["confidence"],
            timestamp=frame.timestamp,
        )
        template.update(result)

        return template

    @classmethod
    def parse_pretty_class_name(cls) -> str:
        return "Pye3D Detector"

    def reset_model(self):
        self.detector.reset()
