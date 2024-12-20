import setuptools


with open("README.md", "r", encoding='UTF-8') as fh:
    long_description = fh.read()


def parse_requirements(filename):
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


setuptools.setup(
    name="Cathin",
    version="2.0.1",
    author="Hank Huang",
    author_email="hanhuang@jabra.com",
    description="Support Desktop/Mobile Automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),

    install_requires=[
        'paddleocr',
        'fastapi',
        'numpy',
        'psutil',
        'pydantic',
        'transformers ',
        'torch',
        'scikit-learn',
        'uvicorn',
        'sentencepiece',
        'protobuf==3.20.3',
        'timm',
        'einops',
        "fastapi",
        "opencv-python==4.6.0.66",
        "opencv-contrib-python==4.6.0.66",
        'loguru==0.7.2'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'ai_server = cathin.console_scripts.ai_model_server:main',
            'cat_ui = cathin.console_scripts.cat_ui:main',
        ]
    },

    python_requires='>=3.6',
    include_package_data = True)