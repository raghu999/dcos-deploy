import time
import requests
from dcosdeploy.auth import get_auth, get_base_url

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class CosmosAdapter(object):
    def __init__(self):
        self.service_url = get_base_url() + "/cosmos/service"
        self.package_url = get_base_url() + "/package"

    def describe_service(self, service_name):
        headers = {
            "Accept": "application/vnd.dcos.service.describe-response+json;charset=utf-8;version=v1",
            "Content-Type": "application/vnd.dcos.service.describe-request+json;charset=utf-8;version=v1",
        }
        response = requests.post(self.service_url+"/describe", json=dict(appId=service_name), headers=headers, auth=get_auth(), verify=False)
        if not response.ok:
            if response.json()["type"] == "MarathonAppNotFound":
                return None
            print(response.text, flush=True)
            raise Exception("Failed to get describe for %s" % service_name)
        return response.json()

    def install_package(self, service_name, package_name, version, options):
        headers = {
            "Accept": "application/vnd.dcos.package.install-response+json;charset=utf-8;version=v2",
            "Content-Type": "application/vnd.dcos.package.install-request+json;charset=utf-8;version=v1",
        }
        data = dict(appId=service_name, options=options, packageName=package_name, packageVersion=version, replace=True)
        response = requests.post(self.package_url+"/install", json=data, headers=headers, auth=get_auth(), verify=False)
        if not response.ok:
            print(response.text, flush=True)
            raise Exception("Failed to update service %s" % service_name)

    def update_service(self, service_name, version, options):
        headers = {
            "Accept": "application/vnd.dcos.service.update-response+json;charset=utf-8;version=v1",
            "Content-Type": "application/vnd.dcos.service.update-request+json;charset=utf-8;version=v1",
        }
        data = dict(appId=service_name, options=options, replace=True)
        if version:
            data["packageVersion"] = version
        response = requests.post(self.service_url+"/update", json=data, headers=headers, auth=get_auth(), verify=False)
        if not response.ok:
            print(response.text, flush=True)
            raise Exception("Failed to update service %s" % service_name)

    def wait_for_plan_complete(self, service_name, plan, timeout=10*60):
        wait_time = 0
        status = self._get_plan_status(service_name, plan)
        if not status:
            # Wait for scheduler to come back online
            time.sleep(40)
        while wait_time < timeout:
            status = self._get_plan_status(service_name, plan)
            if status != "COMPLETE":
                time.sleep(20)
                wait_time += 20
        return status

    def _get_plan_status(self, service_name, plan):
        response = requests.get(get_base_url()+"/service" + service_name + "v1/plans/%s" % plan, auth=get_auth(), verify=False)
        if response.ok:
            return response.json()["status"]
        else:
            return None
