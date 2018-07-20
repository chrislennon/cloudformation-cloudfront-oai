import sys
sys.path.append('./vendor')
import boto3
import logging
import cfn_resource


logger = logging.getLogger()
logger.setLevel(logging.INFO)

cfclient = boto3.client('cloudfront')

# set `handler` as the entry point for Lambda
handler = cfn_resource.Resource()


def get_oai(oai_name):
    result = cfclient.list_cloud_front_origin_access_identities()
    items = result['CloudFrontOriginAccessIdentityList']['Items']
    logger.exception('Items: %s' % items)
    id = filter(lambda n: n.get('Comment') == oai_name, items)[0]['Id']

    result = cfclient.get_cloud_front_origin_access_identity_config(Id=id)
    etag = result['ETag']

    return {'id': id, 'ETag': etag}


def create_oai(oai_name):
    id = 'UNKNOWN'
    try:
        oai_config = get_oai(oai_name)
        id = oai_config['id']
        etag = oai_config['ETag']
    except IndexError:
        config = {
            'CallerReference': oai_name,
            'Comment': oai_name
        }
        result = cfclient.create_cloud_front_origin_access_identity(
            CloudFrontOriginAccessIdentityConfig=config)
        id = result['CloudFrontOriginAccessIdentity']['Id']
        pass

    return id


def delete_oai(oai_name):
    try:
        oai_config = get_oai(oai_name)
        id = oai_config['id']
        etag = oai_config['ETag']
        result = cfclient.delete_cloud_front_origin_access_identity(
            Id=id, IfMatch=etag)
    except IndexError:
        raise

    return id


@handler.create
def create(event, context):
    props = event['ResourceProperties']
    oai_name = props['OAIName']
    oai_id = create_oai(oai_name)

    return {
        "PhysicalResourceId": oai_id,
        "Data": {
            "OriginAccessIdentity": oai_id
        }
    }


@handler.delete
def delete(event, context):
    props = event['ResourceProperties']
    oai_name = props['OAIName']
    oai_id = delete_oai(oai_name)

    return {"PhysicalResourceId": oai_id}
