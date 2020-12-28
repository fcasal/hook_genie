from setuptools import setup

setup(
    name="hook_genie",
    version="0.1",
    description="Simple hook generator",
    author="mandlebro",
    license="MIT",
    include_package_data=True,
    entry_points={"console_scripts": ["hook_genie=hook_genie:main"]},
    package_data={"hook_base": ["template/base_hook.c"]},
)
