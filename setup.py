from setuptools import setup, find_packages

setup(
    name='makrell',
    version='0.9.1',
    author='Hans-Christian Holm',
    author_email='jobb@hcholm.net',
    description='Makrell: A programming language family',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/hcholm/makrell-py',
    packages=find_packages(exclude=["tests*"]),
    package_data={
        "makrell": ["*.mr", "*.mrpy"],
        "makrell.makrellpy": ["*.mr", "*.mrpy"],
    },
    entry_points={
        'console_scripts': [
            'makrell=makrell.cli:main',
            'makrell-langserver=makrell.langserver:main',
        ],
    },
    install_requires=[
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)
