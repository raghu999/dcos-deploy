from dcosdeploy.adapters.ca import CAAdapter
from dcosdeploy.adapters.secrets import SecretsAdapter


class Cert(object):
    def __init__(self, name, cert_secret, key_secret, dn, hostnames):
        self.name = name
        self.cert_secret = cert_secret
        self.key_secret = key_secret
        self.dn = dn
        self.hostnames = hostnames


def parse_config(name, config, variables):
    cert_secret = config.get("cert_secret")
    key_secret = config.get("key_secret")
    dn = config.get("dn")
    hostnames = config.get("hostnames", list())
    if not cert_secret:
        raise Exception("Cert %s has no cert_secret" % name)
    if not key_secret:
        raise Exception("Cert %s has no key_secret" % name)
    if not dn:
        raise Exception("Cert %s has no dn" % name)
    cert_secret = variables.render(cert_secret)
    key_secret = variables.render(key_secret)
    dn = variables.render(dn)
    hostnames = [variables.render(hn) for hn in hostnames]
    return Cert(name, cert_secret, key_secret, dn, hostnames)


class CertsManager(object):
    def __init__(self):
        self.ca = CAAdapter()
        self.secrets = SecretsAdapter()

    def deploy(self, config, dependencies_changed=False, silent=False):
        cert_secret = self.secrets.get_secret(config.cert_secret)
        key_secret = self.secrets.get_secret(config.key_secret)
        if key_secret and cert_secret:
            if not silent:
                print("\tSecrets already exist. Not doing anything.")
            return False
        if cert_secret and not key_secret:
            if not silent:
                print("\tDeleting existing secret %s" % config.cert_secret)
            self.secrets.delete_secret(config.cert_secret)
        if not cert_secret and key_secret:
            if not silent:
                print("\tDeleting existing secret %s" % config.key_secret)
            self.secrets.delete_secret(config.key_secret)

        if not silent:
            print("\tGenerating private key")
        csr, private_key = self.ca.generate_key(config.dn, config.hostnames)
        if not silent:
            print("\tSigning csr")
        cert = self.ca.sign_csr(csr, config.hostnames)
        if not silent:
            print("\tCreating secrets")
        self.secrets.write_secret(config.key_secret, file_content=private_key, update=False)
        self.secrets.write_secret(config.cert_secret, file_content=cert, update=False)
        if not silent:
            print("\tFinished")
        return True

    def dry_run(self, config, dependencies_changed=False, debug=False):
        cert_secret = self.secrets.get_secret(config.cert_secret)
        key_secret = self.secrets.get_secret(config.key_secret)
        if key_secret and cert_secret:
            return False
        elif cert_secret and not key_secret:
            print("Would delete existing secret %s for cert %s and recreate" % (config.cert_secret, config.name))
            return True
        elif not cert_secret and key_secret:
            print("Would delete existing secret %s for cert %s and recreate" % (config.key_secret, config.name))
            return True
        else:
            print("Would create cert %s" % config.name)
            return True


__config__ = Cert
__manager__ = CertsManager
__config_name__ = "cert"
