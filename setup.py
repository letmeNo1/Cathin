import setuptools


with open("README.md", "r", encoding='UTF-8') as fh:
    long_description = fh.read()


def parse_requirements(filename):
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


setuptools.setup(
    name="Cathin",
    version="2.0.2",
    author="Hank Huang",
    author_email="hanhuang@jabra.com",
    description="Support Desktop/Mobile Automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    package_data={
        'apollo_cathin': ['console_scripts/cat_ui_web/templates/*']
    },
    install_requires=[
        "flask==3.0.3",
        'lxml==5.1.0',
        'numpy==1.24.4',
        "opencv-python==4.6.0.66",
        "opencv-contrib-python==4.6.0.66",
        'loguru==0.7.2',
        'scikit-learn>=1.3.2'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'cat_ui = apollo_cathin.console_scripts.cat_ui_web.main:main',
        ]
    },

    python_requires='>=3.6',
    include_package_data = True)