import re


def validate_rfc1123_name(name) -> bool:
    """
    Kubernetes enforces that node and container names are valid DNS subdomains.
    https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#dns-subdomain-names
    Specifically, the name must:
    - contain no more than 253 characters
    - contain only lowercase alphanumeric characters, '-' or '.'
    - start with an alphanumeric character
    - end with an alphanumeric character

    Takes a string to check against the above requirements.
    Returns true if the name complies with the above rules, and false otherwise.

    """

    rfc1123_dns_subdomain_regex_string = r"^[a-z0-9][a-z0-9-.]{0,253}[a-z0-9]$"
    name_match = re.match(rfc1123_dns_subdomain_regex_string, name)
    return bool(name_match)
