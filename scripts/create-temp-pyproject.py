import sys
import toml

input_file = sys.argv[1]
service_name = sys.argv[2]

contents = toml.load(input_file)

contents["tool"]["uv"]["sources"] = {
    key: val
    for key, val in contents["tool"]["uv"]["sources"].items()
    if key == service_name or "shared" in key
}

contents["tool"]["uv"]["dev-dependencies"] = [
    dep
    for dep in contents["tool"]["uv"]["dev-dependencies"]
    if dep == service_name or "shared" in dep
]

with open("../pyproject.toml", "w") as f:
    toml.dump(contents, f)
