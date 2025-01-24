from setuptools import setup, find_packages

setup(
    name="proj",
    version="0.1.0",
    description="A lightweight DSL-based workflow execution project.",
    author="John Curry",
    author_email="curry.john@gmail.com",
    packages=find_packages(),  # Automatically finds `proj` and subpackages
    install_requires=[
        "openai",
        "python-dotenv",
        "pandas",
        "pyyaml",
    ],
    python_requires=">=3.11",
)
