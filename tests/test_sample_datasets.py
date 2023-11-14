# the inclusion of the tests module is not meant to offer best practices for
# testing in general, but rather to support the `find_packages` example in
# setup.py that excludes installing the "tests" package
import shutil
import unittest

import aptosconnector
from aptosconnector.validate import DatasetValidator
import os.path as osp
import tempfile
import logging as log
import json

class TestSimple(unittest.TestCase):

    def test_classification(self):

        pkg_path = osp.dirname(aptosconnector.__file__)
        ds_path = osp.join(pkg_path, '..', '..', 'sample_datasets', 'aptos_classification_sample')

        with tempfile.TemporaryDirectory() as tmp:
            dsv = DatasetValidator(ds_path, tmp)
            msgs, _ = dsv.validate_dataset()
            log.info(msgs)
            # assert that there are not warning/error messages
            self.assertEqual(len(msgs), 0)
            
    def test_object_detection(self):

        pkg_path = osp.dirname(aptosconnector.__file__)
        ds_path = osp.join(pkg_path, '..', '..', 'sample_datasets', 'aptos_objectdetection_sample')

        with tempfile.TemporaryDirectory() as tmp:
            dsv = DatasetValidator(ds_path, tmp)
            msgs, _ = dsv.validate_dataset()
            log.info(msgs)
            # assert that there are not warning/error messages
            self.assertEqual(len(msgs), 0)

    def test_keypoint_detection(self):

        pkg_path = osp.dirname(aptosconnector.__file__)
        ds_path = osp.join(pkg_path, '..', '..', 'sample_datasets', 'aptos_keypoints_sample')

        with tempfile.TemporaryDirectory() as tmp:
            dsv = DatasetValidator(ds_path, tmp)
            msgs, _ = dsv.validate_dataset()
            log.info(msgs)
            # assert that there are not warning/error messages
            self.assertEqual(len(msgs), 0)

    # testing copying dataset to another directory, changing dataset infos entry and checking the autofix
    def test_autofix_simple(self):
        pkg_path = osp.dirname(aptosconnector.__file__)
        ds_path = osp.join(pkg_path, '..', '..', 'sample_datasets', 'aptos_classification_sample')

        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(ds_path, tmp, dirs_exist_ok=True)
            dsv = DatasetValidator(tmp, tmp, auto_fix=True)
            while True:
                msgs, restart = dsv.validate_dataset()
                if not restart:
                    break
            # assert that there are not warning/error messages
            self.assertEqual(len(msgs), 0)

            # change dataset infos entry
            with open(osp.join(tmp, 'dataset_infos.json')) as file:
                dataset_infos = json.load(file)
            dataset_name = list(dataset_infos.keys())[0]
            # scrambling dataset size
            dataset_infos[dataset_name]["dataset_size"] = 100
            # scrambling a split
            dataset_infos[dataset_name]["splits"]["train"]["num_bytes"] = 0
            # deleting an entry
            del dataset_infos[dataset_name]["builder_name"]
            with open(osp.join(tmp, 'dataset_infos.json'), 'w') as file:
                json.dump(dataset_infos, file)
            msgs, _ = dsv.validate_dataset()
            log.info(msgs)
            # assert that there are not warning/error messages
            self.assertEqual(len(msgs), 0)

    def test_autofix(self):
        pkg_path = osp.dirname(aptosconnector.__file__)
        ds_path = osp.join(pkg_path, '..', '..', 'sample_datasets', 'aptos_classification_sample')

        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(ds_path, tmp, dirs_exist_ok=True)
            dsv_no_autofix = DatasetValidator(tmp, tmp, auto_fix=False)
            dsv_autofix = DatasetValidator(tmp, tmp, auto_fix=True, auto_fix_prompt=False)
            while True:
                msgs, restart = dsv_no_autofix.validate_dataset()
                if not restart:
                    break
            # assert that there are not warning/error messages (except potential dataset size on Mac)
            self.assertLessEqual(len(msgs), 1)

            annotations_dir = osp.join(osp.join(tmp, "annotations"))
            images_dir = osp.join(osp.join(tmp, "images"))
            # change images and annotation files
            with open(osp.join(annotations_dir, "coco_train.json")) as file:
                coco_train = json.load(file)
            # image without annotations
            coco_train["annotations"] = [
                ann for ann in coco_train["annotations"] if ann["image_id"] != coco_train["images"][0]["id"]
            ]
            # duplicate images
            shutil.copy(
                osp.join(images_dir, coco_train["images"][1]["file_name"]),
                osp.join(images_dir, coco_train["images"][2]["file_name"])
            )
            # duplicate image filenames in the split
            coco_train["images"][3]["file_name"] = coco_train["images"][4]["file_name"]

            with open(osp.join(annotations_dir, "coco_train.json"), 'w') as file:
                json.dump(coco_train, file)

            msgs, _ = dsv_no_autofix.validate_dataset()
            log.info(msgs)
            # assert that there are not warning/error messages
            self.assertGreater(len(msgs), 0)

            while True:
                msgs, restart = dsv_autofix.validate_dataset()
                if not restart:
                    break

            # assert that there are not warning/error messages
            self.assertEqual(len(msgs), 0)


if __name__ == '__main__':
    log.getLogger().setLevel(log.INFO)
    unittest.main()
