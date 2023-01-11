#!/usr/bin/env python3
import boto3
import json
import sys
import os
from typing import Dict, List

if len(sys.argv) != 3:
    context = 'dev-cset'
    prefix = 'docker-dcu-local.artifactory.secureserver.net'
else:
    context = sys.argv[1]
    prefix = sys.argv[2]


def get_images(kube_context: str) -> List[str]:
    stream = os.popen(f'kubectl --context={kube_context} get pods --all-namespaces -o jsonpath=\'{{range .items[*]}}{{range .spec.containers[*]}}{{","}}{{.image}}{{end}}{{end}}\'')
    images = [x for x in stream.read().split(',') if x]
    return list(dict.fromkeys(images))


def filter_images(images: List[str], filters=[]) -> List[str]:
    return [x for x in images if list(filter(x.startswith, filters)) != []]


def build_tracked_bases(prefix) -> List[str]:
    prefixes = []
    for dockerfile in os.listdir('./containers/dockerfiles'):
        image_name = dockerfile.split('Dockerfile.')[1]
        prefixes.append(f'{prefix}/{image_name}')

    return prefixes


def find_base_digests(images: List[str]) -> Dict[str, str]:
    image_to_base = {}
    for image in images:
        try:
            os.popen(f'docker pull {image}').read()
            stream = os.popen(f'docker inspect {image}')
            output = stream.read()
            container_data = json.loads(output)[0]
            if len(container_data) > 0 and container_data.get('Config', {}).get('Labels', {}).get('BASE_DIGEST'):
                image_to_base[image] = container_data.get('Config', {}).get('Labels', {}).get('BASE_DIGEST')
        except Exception:
            pass

    return image_to_base


def find_outdated_images(images: List[str], prefix: str) -> List[str]:
    outdated_images = []
    ssm_client = boto3.client('ssm')
    for image in images:
        if image.startswith(prefix):
            image_name_with_version = image.split(f'{prefix}/')[1]
            image_name = image_name_with_version.split(':')[0]
            result = json.loads(ssm_client.get_parameter(Name=f'/gci/{image_name}')['Parameter']['Value'])
            ssm_image = f'{image_name}:{result["base-version"]}.{result["local-version"]}'
            if image_name_with_version != ssm_image:
                outdated_images.append(image)

    return outdated_images


tracked_base_images = build_tracked_bases(prefix)
images = get_images(context)
cset_images = filter_images(images, [prefix])
base_images = find_base_digests(cset_images)
outdated_images = find_outdated_images(list(base_images.values()), prefix)

images_with_no_approved_base = list(set(cset_images) - set(base_images.keys()))

if len(images_with_no_approved_base) > 0:
    print(f'We have {len(images_with_no_approved_base)} images without a base images')

for image in cset_images:
    if image in base_images:
        digest = base_images[image]
        if digest in outdated_images:
            print(f'{image.split("@")[0]} is outdated and needs updating')
