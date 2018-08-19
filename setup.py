from distutils.core import setup

required = [
    'gensim >= 2.0.0', 'nltk >= 3.2.4', 'Keras>=2.0.5', 'h5py>=2.7.0', 'scikit-learn>0.18.2',
    'numpy>=1.13.0', 'tensorflow>=1.2.0'
]

setup(
    name='PheneBank',
    version='1.0',
    author='Mohammad Taher Pilehvar',
    author_email='mp792@cam.ac.uk',
    packages=['tagging', 'grounding'],
    scripts=['grounding/grounding.py','utils/web_browser.py'],
    url='http://pilehvar.github.io/phenebank/',
    license='LICENSE.txt',
    description='PheneBank Project: automatic extraction and harmonisation of medical entities.',
    long_description=open('requirements.txt').read(),
    install_requires=[
        "numpy == 1.13.3",
        "gensim >= 2.0.0",
        "nltk >= 3.2.4",
    ],
)
