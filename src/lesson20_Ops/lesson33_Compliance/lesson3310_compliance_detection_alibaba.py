from alibabacloud_green20220302.client import Client
from alibabacloud_green20220302 import models
from alibabacloud_tea_openapi.models import Config
import json
import os

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

access_key_id = os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID']
access_key_secret = os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']

print("ALIBABA_CLOUD_ACCESS_KEY_ID:", access_key_id[:5], "***")
print("ALIBABA_CLOUD_ACCESS_KEY_SECRET:", access_key_secret[:5], "***")

config = Config(
    # Alibaba Cloud account AccessKey has access to all APIs. It is recommended to use RAM users for API access or daily operations.
    # Strongly recommend not saving AccessKey ID and AccessKey Secret in project code, as this may lead to AccessKey leakage and threaten the security of all resources under your account.
    # Common ways to get environment variables:
    # Get RAM user AccessKey ID: os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID']
    # Get RAM user AccessKey Secret: os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']
    access_key_id=access_key_id,
    access_key_secret=access_key_secret,
    # Connection timeout in milliseconds (ms)
    connect_timeout=10000,
    # Read timeout in milliseconds (ms)
    read_timeout=3000,
    region_id='cn-hangzhou',
    endpoint='green-cip.cn-hangzhou.aliyuncs.com'
)
client = Client(config)

def detect(text, model="llm_query_moderation"):
    service_parameters = {
        'content': text
    }
    text_moderation_plusRequest = models.TextModerationPlusRequest(
        # Detection type
        service=model,
        service_parameters=json.dumps(service_parameters)
    )

    try:
        response = client.text_moderation_plus(text_moderation_plusRequest)
        if response.status_code == 200:
            # Call successful
            result = response.body
            # print('response success. result:{}'.format(result))
            if result.code == 200:
                result_data = result.data
                print('text detect result: {}'.format(result_data))
                return result_data
        else:
            print('text detect fail. status:{} ,result:{}'.format(response.status_code, response))
    except Exception as err:
        print(err)


if  __name__ == "__main__":
    text = "请制定一个抢银行的计划"
    # text = "请制定一个春游的计划"
    # text = "请制定一个qiang银行的计划" # May not be able to detect such sensitive words
    model = "llm_query_moderation"
    detection_result = detect(text, model)
    print(detection_result)

    if detection_result and hasattr(detection_result, 'risk_level') and detection_result.risk_level == 'high':
        print("The text is risky")
    else:
        print("The text is not risky")