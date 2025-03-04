from ndn.encoding import Component, MetaInfo, Name, NonStrictName, Signer, SignaturePtrs, TlvModel, UintField, make_data, parse_data
from typing import Union


class AnnObjModel(TlvModel):
    expiration = UintField(0x6d)


def create_announcement_object(name: NonStrictName, pa_signer: Signer,
                               expiration: int = 24 * 3600_000) -> Union[bytearray, memoryview]:
    name = Name.normalize(name)

    ann_obj_name = name + [Component.from_str('32=PA'), Component.from_version(1), Component.from_segment(0)]

    ann_obj_model = AnnObjModel()
    ann_obj_model.expiration = expiration

    ann_obj = make_data(ann_obj_name,
                        MetaInfo(content_type=5),
                        ann_obj_model.encode(),
                        pa_signer)

    return ann_obj


def change_announcement_signature(announcement: Union[bytearray, memoryview],
                                  pa_signer: Signer) -> Union[bytearray, memoryview]:
    name, meta_info, content, _ = parse_data(announcement)

    ann_obj = make_data(name,
                        meta_info,
                        content,
                        pa_signer)

    return ann_obj


def parse_announcement(announcement: Union[bytearray, memoryview]) -> (Name, int, SignaturePtrs):
    name, _, content, sigs = parse_data(announcement)

    ann_obj_model = AnnObjModel.parse(content)

    return name[:-3], ann_obj_model.expiration, sigs
